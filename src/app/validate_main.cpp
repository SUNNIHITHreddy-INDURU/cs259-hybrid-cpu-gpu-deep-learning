// validate_main.cpp - nn_validate: correctness gate that runs BEFORE any benchmarking.
//
// Reference = serial implementation (batch 256) on the full 10,000-image test set.
// Every other implementation / batch size / thread count is compared against it:
//   max |logit difference|, mean |logit difference|, prediction agreement, accuracy.
// An independent anchor checks the serial float32 logits against a float64 NumPy computation
// of the first 100 test images (data/weights/ref_logits_100.bin).
// Acceptance criterion (fixed before running): max |logit difference| <= 1e-4 and prediction
// agreement >= 99.9 %. The measured values are printed and written to the CSV in all cases.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <fstream>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

#include "common.hpp"
#include "impl.hpp"
#include "model.hpp"
#include "timing.hpp"
#include "validation.hpp"

using namespace nn;

namespace {

constexpr double kMaxAbsTol = 1e-4;
constexpr double kAgreeMin = 0.999;

[[noreturn]] void die(const std::string& m) {
  std::cerr << "error: " << m << "\n";
  std::exit(1);
}

}  // namespace

int main(int argc, char** argv) {
  std::string data = "data/raw", weights = "data/weights/mlp_784_256_10.bin";
  std::string ref_path = "data/weights/ref_logits_100.bin", out, platform = "local";
  for (int i = 1; i + 1 < argc; i += 2) {
    const std::string k = argv[i], v = argv[i + 1];
    if (k == "--data") data = v;
    else if (k == "--weights") weights = v;
    else if (k == "--ref") ref_path = v;
    else if (k == "--out") out = v;
    else if (k == "--platform") platform = v;
    else die("unknown argument " + k);
  }
  Weights w;
  Dataset ds;
  std::string err;
  if (!load_weights(weights, w, err)) die(err);
  if (!load_mnist(data + "/t10k-images-idx3-ubyte", data + "/t10k-labels-idx1-ubyte", ds, err)) die(err);
  const int n = ds.n;
  const PlatformInfo pi = query_platform();
  const int hw = pi.logical_threads;

  std::ofstream csv;
  if (!out.empty()) {
    std::ifstream probe(out);
    if (probe.good()) die("refusing to overwrite existing result file " + out);
    csv.open(out);
    csv << "platform,comparison,impl,batch,threads,block,max_abs_err,mean_abs_err,pred_agreement,accuracy,pass\n";
  }
  int failures = 0;
  auto report = [&](const std::string& cmp, const std::string& impl, int batch, int threads, int block,
                    const Agreement& a, double acc) {
    const bool ok = a.max_abs_err <= kMaxAbsTol && a.pred_agreement >= kAgreeMin;
    failures += !ok;
    std::printf("%-34s batch=%-5d thr=%-3d blk=%-2d  max|err| %.3e  mean|err| %.3e  agree %.4f%%  acc %.2f%%  %s\n",
                cmp.c_str(), batch, threads, block, a.max_abs_err, a.mean_abs_err, a.pred_agreement * 100,
                acc * 100, ok ? "PASS" : "FAIL");
    if (csv.is_open())
      csv << platform << "," << cmp << "," << impl << "," << batch << "," << threads << "," << block << ","
          << a.max_abs_err << "," << a.mean_abs_err << "," << a.pred_agreement << "," << acc << ","
          << (ok ? "PASS" : "FAIL") << "\n";
  };

  // reference run
  std::vector<float> ref_logits(static_cast<size_t>(n) * kOut), logits(ref_logits.size());
  std::vector<int32_t> ref_pred(n), pred(n);
  StageTimes t;
  run_serial(w, ds.images.data(), n, 256, ref_logits.data(), ref_pred.data(), t);
  const double ref_acc = accuracy(ref_pred.data(), ds.labels.data(), n);
  std::printf("reference: serial, batch 256, accuracy %.2f%% on %d test images\n", ref_acc * 100, n);

  // independent anchor: float64 NumPy logits for the first 100 images
  {
    std::ifstream f(ref_path, std::ios::binary);
    if (!f) die("cannot open " + ref_path);
    std::vector<float> np_logits(100 * kOut);
    f.read(reinterpret_cast<char*>(np_logits.data()), np_logits.size() * sizeof(float));
    if (!f) die("short read of " + ref_path);
    std::vector<int32_t> np_pred(100);
    for (int i = 0; i < 100; ++i) np_pred[i] = argmax10(&np_logits[i * kOut]);
    report("Serial float32 vs NumPy float64", "serial", 256, 1, 0,
           compare_runs(np_logits.data(), np_pred.data(), ref_logits.data(), ref_pred.data(), 100),
           accuracy(ref_pred.data(), ds.labels.data(), 100));
  }

  const std::vector<int> batches = {1, 37, 256, 4096};  // 37 does not divide 10000: partial last batch
  std::vector<int> threads = {1, 2, 4};
  threads.push_back(hw);
  std::sort(threads.begin(), threads.end());
  threads.erase(std::unique(threads.begin(), threads.end()), threads.end());

  for (int b : {1, 37, 4096}) {
    run_serial(w, ds.images.data(), n, b, logits.data(), pred.data(), t);
    report("Serial batch-invariance", "serial", b, 1, 0,
           compare_runs(ref_logits.data(), ref_pred.data(), logits.data(), pred.data(), n),
           accuracy(pred.data(), ds.labels.data(), n));
  }
  for (int b : batches)
    for (int T : threads) {
      run_openmp(w, ds.images.data(), n, b, T, logits.data(), pred.data(), t);
      report("Serial vs OpenMP", "openmp", b, T, 0,
             compare_runs(ref_logits.data(), ref_pred.data(), logits.data(), pred.data(), n),
             accuracy(pred.data(), ds.labels.data(), n));
    }

#ifdef USE_CUDA
  for (int block : {8, 16, 32}) {
    CudaRunner r(w, 4096, block);
    for (int b : batches) {
      r.run_sync(ds.images.data(), n, b, 1, logits.data(), pred.data(), t);
      report("Serial vs CUDA", "cuda", b, 1, block,
             compare_runs(ref_logits.data(), ref_pred.data(), logits.data(), pred.data(), n),
             accuracy(pred.data(), ds.labels.data(), n));
    }
    if (block == 16) {
      for (int b : batches)
        for (int T : threads) {
          r.run_sync(ds.images.data(), n, b, T, logits.data(), pred.data(), t);
          report("Serial vs Hybrid-sequential", "hybrid_seq", b, T, block,
                 compare_runs(ref_logits.data(), ref_pred.data(), logits.data(), pred.data(), n),
                 accuracy(pred.data(), ds.labels.data(), n));
          for (int s : {1, 3}) {
            r.run_pipelined(ds.images.data(), n, b, T, s, logits.data(), pred.data(), t);
            report("Serial vs Hybrid-pipelined (s=" + std::to_string(s) + ")", "hybrid", b, T, block,
                   compare_runs(ref_logits.data(), ref_pred.data(), logits.data(), pred.data(), n),
                   accuracy(pred.data(), ds.labels.data(), n));
          }
        }
    }
  }
#else
  std::printf("(CUDA comparisons skipped: binary built without CUDA)\n");
#endif

  std::printf("\n%s: %d comparison(s) outside tolerance (max|err| <= %.0e, agreement >= %.1f%%)\n",
              failures ? "FAILED" : "ALL PASSED", failures, kMaxAbsTol, kAgreeMin * 100);
  return failures ? 1 : 0;
}
