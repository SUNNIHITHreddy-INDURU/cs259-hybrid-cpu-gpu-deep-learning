// main.cpp - nn_bench: runs the benchmark grid and writes one CSV row per measured pass.
//
// A "pass" processes the whole 10,000-image MNIST test set in batches of the given size.
// For every configuration: `warmup` unrecorded passes, then `runs` recorded passes.
// Result files are never overwritten (the program refuses to open an existing --out file).
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <fstream>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

#include "common.hpp"
#include "impl.hpp"
#include "timing.hpp"
#include "validation.hpp"

using namespace nn;

namespace {

std::vector<std::string> split(const std::string& s) {
  std::vector<std::string> out;
  std::stringstream ss(s);
  std::string item;
  while (std::getline(ss, item, ',')) if (!item.empty()) out.push_back(item);
  return out;
}
std::vector<int> split_ints(const std::string& s) {
  std::vector<int> v;
  for (const auto& x : split(s)) v.push_back(std::atoi(x.c_str()));
  return v;
}

struct Args {
  std::string platform = "local";
  std::string data = "data/raw";
  std::string weights = "data/weights/mlp_784_256_10.bin";
  std::string out;
  std::vector<std::string> impls = {"serial", "openmp"};
  std::vector<int> batches = {1, 8, 32, 64, 128, 256, 1024, 4096};
  std::vector<int> threads;  // default filled from hardware
  std::vector<int> blocks = {16};
  int default_block = 16;
  int streams = 3;
  int runs = 20;
  int warmup = 3;
  int n = 10000;
  bool micro = false;
};

std::string iso_utc() {
  std::time_t t = std::time(nullptr);
  char buf[32];
  std::strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", std::gmtime(&t));
  return buf;
}

[[noreturn]] void die(const std::string& msg) {
  std::cerr << "error: " << msg << "\n";
  std::exit(1);
}

Args parse(int argc, char** argv, int hw_threads) {
  Args a;
  for (int i = 1; i < argc; ++i) {
    const std::string k = argv[i];
    auto next = [&]() -> std::string {
      if (i + 1 >= argc) die("missing value for " + k);
      return argv[++i];
    };
    if (k == "--platform") a.platform = next();
    else if (k == "--data") a.data = next();
    else if (k == "--weights") a.weights = next();
    else if (k == "--out") a.out = next();
    else if (k == "--impls") a.impls = split(next());
    else if (k == "--batches") a.batches = split_ints(next());
    else if (k == "--threads") a.threads = split_ints(next());
    else if (k == "--blocks") a.blocks = split_ints(next());
    else if (k == "--default-block") a.default_block = std::atoi(next().c_str());
    else if (k == "--streams") a.streams = std::atoi(next().c_str());
    else if (k == "--runs") a.runs = std::atoi(next().c_str());
    else if (k == "--warmup") a.warmup = std::atoi(next().c_str());
    else if (k == "--n") a.n = std::atoi(next().c_str());
    else if (k == "--micro") a.micro = true;
    else die("unknown argument " + k);
  }
  if (a.threads.empty()) {
    for (int t = 1; t < hw_threads; t *= 2) a.threads.push_back(t);
    a.threads.push_back(hw_threads);
  }
  if (a.out.empty()) die("--out <file.csv> is required");
  return a;
}

}  // namespace

int main(int argc, char** argv) {
  const PlatformInfo pi = query_platform();
  const Args args = parse(argc, argv, pi.logical_threads);

  Weights w;
  Dataset ds;
  std::string err;
  if (!load_weights(args.weights, w, err)) die(err);
  if (!load_mnist(args.data + "/t10k-images-idx3-ubyte", args.data + "/t10k-labels-idx1-ubyte", ds, err))
    die(err);
  const int n = std::min(args.n, ds.n);
  const int max_batch = std::min(*std::max_element(args.batches.begin(), args.batches.end()), n);

  (void)max_batch;  // only needed by the CUDA build
  bool need_gpu = false;
  for (const auto& im : args.impls)
    if (im == "cuda" || im == "hybrid_seq" || im == "hybrid") need_gpu = true;

  std::string gpu_model = "none", cuda_rt = "none";
#ifdef USE_CUDA
  std::map<int, std::unique_ptr<CudaRunner>> runners;
  auto get_runner = [&](int block) -> CudaRunner& {
    auto it = runners.find(block);
    if (it == runners.end())
      it = runners.emplace(block, std::unique_ptr<CudaRunner>(new CudaRunner(w, max_batch, block))).first;
    return *it->second;
  };
  if (need_gpu) {
    CudaRunner& r = get_runner(args.default_block);
    gpu_model = r.device_name();
    for (char& c : gpu_model) if (c == ',') c = ' ';
    cuda_rt = std::to_string(r.runtime_version());
    std::cerr << "GPU: " << r.device_info() << "\n";
    std::cerr << "one-time weight upload: " << r.setup_upload_ms() << " ms (excluded from passes)\n";
  }
#else
  if (need_gpu) die("this binary was built without CUDA (use `make gpu`)");
#endif

  {
    std::ifstream probe(args.out);
    if (probe.good()) die("refusing to overwrite existing result file " + args.out);
  }
  std::ofstream csv(args.out);
  if (!csv) die("cannot create " + args.out);
  csv << "timestamp_utc,platform,impl,batch,threads,block,streams,run,n_samples,pre_ms,layer1_ms,"
         "layer2_ms,h2d_ms,kernel_ms,d2h_ms,e2e_ms,accuracy,cpu_model,cpu_logical_threads,"
         "gpu_model,compiler,cuda_runtime\n";

  std::vector<float> logits(static_cast<size_t>(n) * kOut);
  std::vector<int32_t> pred(n);

  auto measure = [&](const std::string& impl, int batch, int threads, int block, int streams,
                     const std::function<void(StageTimes&)>& fn) {
    StageTimes t;
    for (int i = 0; i < args.warmup; ++i) fn(t);
    double sum = 0, min_acc = 1.0;
    for (int r = 0; r < args.runs; ++r) {
      fn(t);
      const double acc = accuracy(pred.data(), ds.labels.data(), n);
      min_acc = std::min(min_acc, acc);
      sum += t.e2e_ms;
      char row[1024];
      std::snprintf(row, sizeof(row),
                    "%s,%s,%s,%d,%d,%d,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%s,%d,%s,%s,%s\n",
                    iso_utc().c_str(), args.platform.c_str(), impl.c_str(), batch, threads, block,
                    streams, r, n, t.pre_ms, t.layer1_ms, t.layer2_ms, t.h2d_ms, t.kernel_ms,
                    t.d2h_ms, t.e2e_ms, acc, pi.cpu_model.c_str(), pi.logical_threads,
                    gpu_model.c_str(), pi.compiler.c_str(), cuda_rt.c_str());
      csv << row;
    }
    csv.flush();
    std::printf("%-10s batch=%-5d threads=%-3d block=%-2d streams=%d  mean e2e %9.3f ms  min acc %.4f\n",
                impl.c_str(), batch, threads, block, streams, sum / args.runs, min_acc);
    std::fflush(stdout);
  };

  for (int batch0 : args.batches) {
    const int batch = std::min(batch0, n);
    for (const auto& impl : args.impls) {
      if (impl == "serial") {
        measure(impl, batch, 1, 0, 0, [&](StageTimes& t) {
          run_serial(w, ds.images.data(), n, batch, logits.data(), pred.data(), t);
        });
      } else if (impl == "openmp") {
        for (int T : args.threads)
          measure(impl, batch, T, 0, 0, [&](StageTimes& t) {
            run_openmp(w, ds.images.data(), n, batch, T, logits.data(), pred.data(), t);
          });
      }
#ifdef USE_CUDA
      else if (impl == "cuda") {
        for (int block : args.blocks) {
          CudaRunner& r = get_runner(block);
          measure(impl, batch, 1, block, 0, [&](StageTimes& t) {
            r.run_sync(ds.images.data(), n, batch, 1, logits.data(), pred.data(), t);
          });
        }
      } else if (impl == "hybrid_seq") {
        CudaRunner& r = get_runner(args.default_block);
        for (int T : args.threads)
          measure(impl, batch, T, args.default_block, 0, [&](StageTimes& t) {
            r.run_sync(ds.images.data(), n, batch, T, logits.data(), pred.data(), t);
          });
      } else if (impl == "hybrid") {
        CudaRunner& r = get_runner(args.default_block);
        for (int T : args.threads)
          measure(impl, batch, T, args.default_block, args.streams, [&](StageTimes& t) {
            r.run_pipelined(ds.images.data(), n, batch, T, args.streams, logits.data(), pred.data(), t);
          });
      }
#endif
      else die("unknown implementation " + impl);
    }
  }

  if (args.micro) {
    std::string mpath = args.out;
    const auto dot = mpath.rfind(".csv");
    mpath = (dot == std::string::npos ? mpath : mpath.substr(0, dot)) + "_micro.csv";
    {
      std::ifstream exists(mpath);
      if (exists.good()) die("refusing to overwrite existing result file " + mpath);
    }
    std::ofstream m(mpath);
    m << "timestamp_utc,platform,metric,threads,value,unit\n";
    for (int T : args.threads) {
      const CpuMicro c = cpu_microbench(T);
      m << iso_utc() << "," << args.platform << ",openmp_fork_join," << T << "," << c.fork_join_us << ",us\n";
      m << iso_utc() << "," << args.platform << ",cpu_triad_bandwidth," << T << "," << c.triad_gbs << ",GB/s\n";
      std::printf("micro: threads=%d fork-join %.2f us, triad %.1f GB/s\n", T, c.fork_join_us, c.triad_gbs);
    }
#ifdef USE_CUDA
    if (need_gpu) {
      const GpuMicro g = gpu_microbench();
      const char* names[] = {"h2d_pageable", "h2d_pinned", "d2h_pageable", "d2h_pinned", "d2d_copy"};
      const double vals[] = {g.h2d_pageable_gbs, g.h2d_pinned_gbs, g.d2h_pageable_gbs, g.d2h_pinned_gbs, g.d2d_gbs};
      for (int i = 0; i < 5; ++i)
        m << iso_utc() << "," << args.platform << "," << names[i] << "_bandwidth,0," << vals[i] << ",GB/s\n";
      m << iso_utc() << "," << args.platform << ",kernel_launch_async,0," << g.launch_empty_us << ",us\n";
      m << iso_utc() << "," << args.platform << ",kernel_launch_sync,0," << g.launch_sync_us << ",us\n";
      std::printf("micro: H2D pageable %.2f pinned %.2f GB/s, D2H pageable %.2f pinned %.2f GB/s, D2D %.1f GB/s, launch %.2f us (sync %.2f us)\n",
                  g.h2d_pageable_gbs, g.h2d_pinned_gbs, g.d2h_pageable_gbs, g.d2h_pinned_gbs, g.d2d_gbs,
                  g.launch_empty_us, g.launch_sync_us);
    }
#endif
    std::printf("wrote %s\n", mpath.c_str());
  }
  std::printf("wrote %s\n", args.out.c_str());
  return 0;
}
