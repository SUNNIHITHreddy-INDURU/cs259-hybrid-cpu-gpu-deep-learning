// openmp_nn.cpp - Implementation 2: the serial algorithm parallelised with OpenMP.
//
// One parallel region covers the whole pass; inside it the batch loop is executed by every
// thread and each pipeline stage is a work-shared `omp for`. The implicit barrier at the end of
// each `omp for` is required: a stage reads data written by other threads in the previous stage.
//
// Loop ownership (why every loop is race-free):
//   stage            iteration space            writes (exclusive to the iteration)
//   preprocess       image b                    x[b][0..783]
//   hidden layer     (image b, block jb)        h[b][16*jb .. 16*jb+15]
//   output layer     (image b, class k)         logits[s+b][k]
//   argmax           image b                    pred[s+b]
//   Reads (x, h, W1, b1, W2, b2) are never written while the stage runs.
//   Variables declared inside the region (s, B, timestamps) are private to each thread; only
//   thread 0 updates the shared stage-time accumulators.
//
// Why these loops and not others: the batch loop itself is NOT work-shared because consecutive
// batches reuse the buffers x and h. The hidden layer is split over (b, jb) - not only over b -
// so that even a batch of 1 image offers kJBlocks = 16 independent work items.
#include <omp.h>

#include <algorithm>
#include <vector>

#include "impl.hpp"
#include "model.hpp"
#include "timing.hpp"

namespace nn {

void run_openmp(const Weights& w, const uint8_t* raw, int n, int batch, int threads,
                float* logits, int32_t* pred, StageTimes& t) {
  std::vector<float> x(static_cast<size_t>(batch) * kIn);
  std::vector<float> h(static_cast<size_t>(batch) * kHidden);
  const float* w1 = w.w1.data();
  const float* b1 = w.b1.data();
  const float* w2 = w.w2.data();
  const float* b2 = w.b2.data();
  float* xp = x.data();
  float* hp = h.data();
  double pre = 0, l1 = 0, l2 = 0;
  omp_set_dynamic(0);

  const double t0 = now_ms();
#pragma omp parallel num_threads(threads) shared(raw, logits, pred, pre, l1, l2, xp, hp, w1, b1, w2, b2, n, batch)
  {
    const bool lead = (omp_get_thread_num() == 0);
    for (int s = 0; s < n; s += batch) {
      const int B = std::min(batch, n - s);
      const double ta = lead ? now_ms() : 0.0;
#pragma omp for schedule(static)
      for (int b = 0; b < B; ++b)
        preprocess_image(raw + static_cast<size_t>(s + b) * kIn, xp + static_cast<size_t>(b) * kIn);
      const double tb = lead ? now_ms() : 0.0;
#pragma omp for collapse(2) schedule(static)
      for (int b = 0; b < B; ++b)
        for (int jb = 0; jb < kJBlocks; ++jb)
          layer1_block(w1, b1, xp + static_cast<size_t>(b) * kIn, jb,
                       hp + static_cast<size_t>(b) * kHidden);
      const double tc = lead ? now_ms() : 0.0;
#pragma omp for collapse(2) schedule(static)
      for (int b = 0; b < B; ++b)
        for (int k = 0; k < kOut; ++k)
          logits[static_cast<size_t>(s + b) * kOut + k] =
              layer2_item(w2, b2, hp + static_cast<size_t>(b) * kHidden, k);
#pragma omp for schedule(static)
      for (int b = 0; b < B; ++b) pred[s + b] = argmax10(logits + static_cast<size_t>(s + b) * kOut);
      if (lead) {
        const double td = now_ms();
        pre += tb - ta;
        l1 += tc - tb;
        l2 += td - tc;
      }
    }
  }
  t = StageTimes();
  t.pre_ms = pre;
  t.layer1_ms = l1;
  t.layer2_ms = l2;
  t.e2e_ms = now_ms() - t0;
}

// ---- micro-benchmarks: measured CPU limits used in the analysis -------------------------------

CpuMicro cpu_microbench(int threads) {
  CpuMicro m;
  m.threads = threads;
  omp_set_dynamic(0);

  // 1) fork/join cost of an empty parallel region
  volatile int sink = 0;
  for (int i = 0; i < 200; ++i) {
#pragma omp parallel num_threads(threads)
    {
      if (omp_get_thread_num() > 1000000) sink = sink + 1;
    }
  }
  const int reps = 3000;
  const double f0 = now_ms();
  for (int i = 0; i < reps; ++i) {
#pragma omp parallel num_threads(threads)
    {
      if (omp_get_thread_num() > 1000000) sink = sink + 1;
    }
  }
  m.fork_join_us = (now_ms() - f0) * 1000.0 / reps;

  // 2) STREAM-triad style bandwidth: a[i] = b[i] + s*c[i], 3 arrays of 32M floats (128 MiB each)
  const size_t N = static_cast<size_t>(1) << 25;
  std::vector<float> a(N), b(N), c(N);
#pragma omp parallel for num_threads(threads) schedule(static)
  for (long i = 0; i < static_cast<long>(N); ++i) { a[i] = 0.f; b[i] = 1.f; c[i] = 2.f; }
  std::vector<double> bw;
  for (int r = 0; r < 11; ++r) {
    const double t0 = now_ms();
#pragma omp parallel for num_threads(threads) schedule(static)
    for (long i = 0; i < static_cast<long>(N); ++i) a[i] = b[i] + 3.0f * c[i];
    const double dt = (now_ms() - t0) / 1000.0;
    if (r > 0) bw.push_back(3.0 * N * sizeof(float) / dt / 1e9);  // r == 0 is a warm-up
  }
  std::sort(bw.begin(), bw.end());
  m.triad_gbs = bw[bw.size() / 2];  // median
  if (a[N / 2] < 0.f) m.triad_gbs = 0;  // keeps the loop observable
  return m;
}

}  // namespace nn
