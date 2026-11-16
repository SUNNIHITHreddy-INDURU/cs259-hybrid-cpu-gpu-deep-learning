// cuda_nn.cu - Implementation 3: CUDA inference (and the shared device code + set-up).
//
// Thread organisation
//   Hidden layer (layer1_kernel): 2-D grid of 2-D blocks of block_dim x block_dim threads.
//     thread (tx, ty) of block (bx, by) computes ONE output element:
//         hidden unit j = bx*block_dim + tx   (fastest-varying index -> consecutive threads read
//                                              consecutive W1 addresses: coalesced loads)
//         sample      b = by*block_dim + ty
//     grid = ceil(256/block_dim) x ceil(B/block_dim). Threads with b >= B exit immediately.
//   Output layer (layer2_kernel): 1-D, 128 threads/block, thread i computes logit (i/10, i%10).
//   Argmax (argmax_kernel): 1-D, 128 threads/block, one thread per sample.
// Every thread writes a distinct output element, so no atomics or synchronisation are needed.
//
// Timing: each batch is bracketed with CUDA events (H2D copy, the three kernels, D2H copies);
// preprocessing is timed on the CPU; the end-to-end time is the wall clock of the whole pass.
#include <algorithm>
#include <cstring>
#include <vector>

#include "cuda_internal.cuh"
#include "timing.hpp"

namespace nn {

__global__ void layer1_kernel(const float* __restrict__ x, const float* __restrict__ w1,
                              const float* __restrict__ b1, float* __restrict__ h, int B) {
  const int j = blockIdx.x * blockDim.x + threadIdx.x;  // hidden unit
  const int b = blockIdx.y * blockDim.y + threadIdx.y;  // sample
  if (b >= B || j >= kHidden) return;
  const float* xr = x + static_cast<size_t>(b) * kIn;
  float acc = b1[j];
  for (int k = 0; k < kIn; ++k) acc += xr[k] * w1[static_cast<size_t>(k) * kHidden + j];
  h[static_cast<size_t>(b) * kHidden + j] = acc > 0.f ? acc : 0.f;  // ReLU
}

__global__ void layer2_kernel(const float* __restrict__ h, const float* __restrict__ w2,
                              const float* __restrict__ b2, float* __restrict__ logits, int B) {
  const int i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i >= B * kOut) return;
  const int b = i / kOut, c = i % kOut;
  const float* hr = h + static_cast<size_t>(b) * kHidden;
  float acc = b2[c];
  for (int j = 0; j < kHidden; ++j) acc += hr[j] * w2[static_cast<size_t>(j) * kOut + c];
  logits[i] = acc;
}

__global__ void argmax_kernel(const float* __restrict__ logits, int32_t* __restrict__ pred, int B) {
  const int b = blockIdx.x * blockDim.x + threadIdx.x;
  if (b >= B) return;
  const float* z = logits + static_cast<size_t>(b) * kOut;
  int best = 0;
  for (int c = 1; c < kOut; ++c)
    if (z[c] > z[best]) best = c;
  pred[b] = best;
}

void launch_forward(CudaRunner::Impl& p, int slot, cudaStream_t stream, int B) {
  const int d = p.block_dim;
  const dim3 block1(d, d);
  const dim3 grid1((kHidden + d - 1) / d, (B + d - 1) / d);
  layer1_kernel<<<grid1, block1, 0, stream>>>(p.d_x[slot], p.d_w1, p.d_b1, p.d_h[slot], B);
  CUDA_CHECK(cudaGetLastError());
  const int items = B * kOut;
  layer2_kernel<<<(items + 127) / 128, 128, 0, stream>>>(p.d_h[slot], p.d_w2, p.d_b2,
                                                          p.d_logits[slot], B);
  CUDA_CHECK(cudaGetLastError());
  argmax_kernel<<<(B + 127) / 128, 128, 0, stream>>>(p.d_logits[slot], p.d_pred[slot], B);
  CUDA_CHECK(cudaGetLastError());
}

// ---- construction / destruction --------------------------------------------------------------

CudaRunner::CudaRunner(const Weights& w, int max_batch, int block_dim) : p_(new Impl) {
  Impl& p = *p_;
  p.max_batch = max_batch;
  p.block_dim = block_dim;
  const double t_init = now_ms();
  CUDA_CHECK(cudaSetDevice(0));
  CUDA_CHECK(cudaFree(nullptr));  // create the context now so it is not charged to a timed pass
  p.init_ms = now_ms() - t_init;

  cudaDeviceProp prop;
  CUDA_CHECK(cudaGetDeviceProperties(&prop, 0));
  int driver = 0, mem_clock_khz = 0, bus_bits = 0, sms = 0;
  CUDA_CHECK(cudaDriverGetVersion(&driver));
  CUDA_CHECK(cudaRuntimeGetVersion(&p.runtime));
  CUDA_CHECK(cudaDeviceGetAttribute(&bus_bits, cudaDevAttrGlobalMemoryBusWidth, 0));
  CUDA_CHECK(cudaDeviceGetAttribute(&sms, cudaDevAttrMultiProcessorCount, 0));
#if CUDART_VERSION < 13000
  CUDA_CHECK(cudaDeviceGetAttribute(&mem_clock_khz, cudaDevAttrMemoryClockRate, 0));
#endif
  p.name = prop.name;
  char buf[512];
  std::snprintf(buf, sizeof(buf),
                "%s, compute capability %d.%d, %d SMs, %.0f MiB memory, %d-bit bus, memory clock "
                "%.0f MHz, driver %d, runtime %d",
                prop.name, prop.major, prop.minor, sms, prop.totalGlobalMem / 1048576.0, bus_bits,
                mem_clock_khz / 1000.0, driver, p.runtime);
  p.info = buf;

  const size_t w1b = w.w1.size() * 4, b1b = w.b1.size() * 4, w2b = w.w2.size() * 4, b2b = w.b2.size() * 4;
  const double t0 = now_ms();
  CUDA_CHECK(cudaMalloc(&p.d_w1, w1b));
  CUDA_CHECK(cudaMalloc(&p.d_b1, b1b));
  CUDA_CHECK(cudaMalloc(&p.d_w2, w2b));
  CUDA_CHECK(cudaMalloc(&p.d_b2, b2b));
  CUDA_CHECK(cudaMemcpy(p.d_w1, w.w1.data(), w1b, cudaMemcpyHostToDevice));
  CUDA_CHECK(cudaMemcpy(p.d_b1, w.b1.data(), b1b, cudaMemcpyHostToDevice));
  CUDA_CHECK(cudaMemcpy(p.d_w2, w.w2.data(), w2b, cudaMemcpyHostToDevice));
  CUDA_CHECK(cudaMemcpy(p.d_b2, w.b2.data(), b2b, cudaMemcpyHostToDevice));
  CUDA_CHECK(cudaDeviceSynchronize());
  p.setup_ms = now_ms() - t0;

  const size_t mb = static_cast<size_t>(max_batch);
  const double t_alloc = now_ms();
  for (int s = 0; s < kMaxSlots; ++s) {
    CUDA_CHECK(cudaMalloc(&p.d_x[s], mb * kIn * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&p.d_h[s], mb * kHidden * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&p.d_logits[s], mb * kOut * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&p.d_pred[s], mb * sizeof(int32_t)));
    CUDA_CHECK(cudaMallocHost(&p.ph_x[s], mb * kIn * sizeof(float)));
    CUDA_CHECK(cudaMallocHost(&p.ph_logits[s], mb * kOut * sizeof(float)));
    CUDA_CHECK(cudaMallocHost(&p.ph_pred[s], mb * sizeof(int32_t)));
    CUDA_CHECK(cudaStreamCreateWithFlags(&p.stream[s], cudaStreamNonBlocking));
    for (int e = 0; e < 4; ++e) CUDA_CHECK(cudaEventCreate(&p.ev[s][e]));
  }
  p.alloc_ms = now_ms() - t_alloc;
}

CudaRunner::~CudaRunner() {
  if (!p_) return;
  Impl& p = *p_;
  for (int s = 0; s < kMaxSlots; ++s) {
    for (int e = 0; e < 4; ++e) cudaEventDestroy(p.ev[s][e]);
    cudaStreamDestroy(p.stream[s]);
    cudaFreeHost(p.ph_x[s]);
    cudaFreeHost(p.ph_logits[s]);
    cudaFreeHost(p.ph_pred[s]);
    cudaFree(p.d_x[s]);
    cudaFree(p.d_h[s]);
    cudaFree(p.d_logits[s]);
    cudaFree(p.d_pred[s]);
  }
  cudaFree(p.d_w1);
  cudaFree(p.d_b1);
  cudaFree(p.d_w2);
  cudaFree(p.d_b2);
}

std::string CudaRunner::device_name() const { return p_->name; }
std::string CudaRunner::device_info() const { return p_->info; }
int CudaRunner::runtime_version() const { return p_->runtime; }
double CudaRunner::setup_upload_ms() const { return p_->setup_ms; }
double CudaRunner::init_ms() const { return p_->init_ms; }
double CudaRunner::buffer_alloc_ms() const { return p_->alloc_ms; }

// ---- CUDA path with synchronous copies (single- or multi-threaded preprocessing) -------------------------------------------------------------

void CudaRunner::run_sync(const uint8_t* raw, int n, int batch, int pre_threads, float* logits,
                          int32_t* pred, StageTimes& t) {
  Impl& p = *p_;
  if (batch > p.max_batch) {
    std::fprintf(stderr, "batch %d exceeds the runner's max_batch %d\n", batch, p.max_batch);
    std::exit(2);
  }
  std::vector<float> x(static_cast<size_t>(batch) * kIn);  // pageable host buffer
  t = StageTimes();
  cudaEvent_t e0 = p.ev[0][0], e1 = p.ev[0][1], e2 = p.ev[0][2], e3 = p.ev[0][3];

  const double t0 = now_ms();
  for (int s = 0; s < n; s += batch) {
    const int B = std::min(batch, n - s);
    const double a = now_ms();
    preprocess_batch(raw + static_cast<size_t>(s) * kIn, x.data(), B, pre_threads);
    t.pre_ms += now_ms() - a;

    CUDA_CHECK(cudaEventRecord(e0, 0));
    CUDA_CHECK(cudaMemcpy(p.d_x[0], x.data(), static_cast<size_t>(B) * kIn * sizeof(float),
                          cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaEventRecord(e1, 0));
    launch_forward(p, 0, 0, B);
    CUDA_CHECK(cudaEventRecord(e2, 0));
    CUDA_CHECK(cudaMemcpy(logits + static_cast<size_t>(s) * kOut, p.d_logits[0],
                          static_cast<size_t>(B) * kOut * sizeof(float), cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaMemcpy(pred + s, p.d_pred[0], static_cast<size_t>(B) * sizeof(int32_t),
                          cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaEventRecord(e3, 0));
    CUDA_CHECK(cudaEventSynchronize(e3));
    float m1 = 0, m2 = 0, m3 = 0;
    CUDA_CHECK(cudaEventElapsedTime(&m1, e0, e1));
    CUDA_CHECK(cudaEventElapsedTime(&m2, e1, e2));
    CUDA_CHECK(cudaEventElapsedTime(&m3, e2, e3));
    t.h2d_ms += m1;
    t.kernel_ms += m2;
    t.d2h_ms += m3;
  }
  t.e2e_ms = now_ms() - t0;
}

// ---- measured GPU limits ----------------------------------------------------------------------

__global__ void empty_kernel() {}

namespace {

double median(std::vector<double> v) {
  std::sort(v.begin(), v.end());
  return v[v.size() / 2];
}

// Median bandwidth (GB/s) of repeated copies of `bytes`, timed with CUDA events.
double copy_bandwidth(void* dst, const void* src, size_t bytes, cudaMemcpyKind kind, double traffic_factor) {
  cudaEvent_t a, b;
  CUDA_CHECK(cudaEventCreate(&a));
  CUDA_CHECK(cudaEventCreate(&b));
  std::vector<double> gbs;
  for (int r = 0; r < 23; ++r) {
    CUDA_CHECK(cudaEventRecord(a, 0));
    CUDA_CHECK(cudaMemcpy(dst, src, bytes, kind));
    CUDA_CHECK(cudaEventRecord(b, 0));
    CUDA_CHECK(cudaEventSynchronize(b));
    float ms = 0;
    CUDA_CHECK(cudaEventElapsedTime(&ms, a, b));
    if (r >= 3) gbs.push_back(traffic_factor * bytes / (ms / 1000.0) / 1e9);  // 3 warm-ups
  }
  CUDA_CHECK(cudaEventDestroy(a));
  CUDA_CHECK(cudaEventDestroy(b));
  return median(gbs);
}

}  // namespace

GpuMicro gpu_microbench() {
  GpuMicro g;
  const size_t bytes = static_cast<size_t>(64) << 20;
  float *d1 = nullptr, *d2 = nullptr, *pinned = nullptr;
  CUDA_CHECK(cudaMalloc(&d1, bytes));
  CUDA_CHECK(cudaMalloc(&d2, bytes));
  CUDA_CHECK(cudaMallocHost(&pinned, bytes));
  std::vector<char> pageable(bytes, 1);
  std::memset(pinned, 1, bytes);
  CUDA_CHECK(cudaMemset(d1, 0, bytes));

  g.h2d_pageable_gbs = copy_bandwidth(d1, pageable.data(), bytes, cudaMemcpyHostToDevice, 1.0);
  g.h2d_pinned_gbs = copy_bandwidth(d1, pinned, bytes, cudaMemcpyHostToDevice, 1.0);
  g.d2h_pageable_gbs = copy_bandwidth(pageable.data(), d1, bytes, cudaMemcpyDeviceToHost, 1.0);
  g.d2h_pinned_gbs = copy_bandwidth(pinned, d1, bytes, cudaMemcpyDeviceToHost, 1.0);
  g.d2d_gbs = copy_bandwidth(d2, d1, bytes, cudaMemcpyDeviceToDevice, 2.0);  // read + write

  for (int i = 0; i < 200; ++i) empty_kernel<<<1, 1>>>();
  CUDA_CHECK(cudaDeviceSynchronize());
  const int launches = 5000;
  double t0 = now_ms();
  for (int i = 0; i < launches; ++i) empty_kernel<<<1, 1>>>();
  g.launch_empty_us = (now_ms() - t0) * 1000.0 / launches;
  CUDA_CHECK(cudaDeviceSynchronize());
  const int syncs = 2000;
  t0 = now_ms();
  for (int i = 0; i < syncs; ++i) {
    empty_kernel<<<1, 1>>>();
    CUDA_CHECK(cudaDeviceSynchronize());
  }
  g.launch_sync_us = (now_ms() - t0) * 1000.0 / syncs;
  CUDA_CHECK(cudaGetLastError());

  CUDA_CHECK(cudaFree(d1));
  CUDA_CHECK(cudaFree(d2));
  CUDA_CHECK(cudaFreeHost(pinned));
  return g;
}

}  // namespace nn
