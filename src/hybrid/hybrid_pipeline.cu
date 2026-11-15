// hybrid_pipeline.cu - Implementation 4: hybrid OpenMP + CUDA with a software pipeline.
//
// Who does what
//   CPU, OpenMP threads : preprocessing of batch i (per-image standardisation into a pinned
//                         host buffer) - the only stage that runs on the CPU.
//   DMA engines (async) : host->device copy of the preprocessed batch and device->host copy of
//                         the logits / predictions, issued with cudaMemcpyAsync on pinned memory.
//   GPU, CUDA threads   : hidden layer, output layer, argmax (same kernels as the CUDA-only path).
//
// Pipeline: batches are assigned round-robin to `streams` slots (own stream, own device buffers,
// own pinned buffers). While the GPU works on batches i-1, i-2, ... the CPU already preprocesses
// batch i. A slot is only reused after its previous batch has completed (event synchronised), so
// no buffer is read and written at the same time. With streams == 1 nothing overlaps.
//
// Reported times: pre_ms is the CPU time spent preprocessing; h2d/kernel/d2h are GPU-timeline
// durations from CUDA events (they may overlap each other and the CPU work, so their sum can
// exceed e2e_ms); e2e_ms is the wall clock of the pass - the number that matters.
#include <algorithm>
#include <cstring>

#include "cuda_internal.cuh"
#include "timing.hpp"

namespace nn {

void CudaRunner::run_pipelined(const uint8_t* raw, int n, int batch, int pre_threads, int streams,
                               float* logits, int32_t* pred, StageTimes& t) {
  Impl& p = *p_;
  if (batch > p.max_batch) {
    std::fprintf(stderr, "batch %d exceeds the runner's max_batch %d\n", batch, p.max_batch);
    std::exit(2);
  }
  const int S = std::max(1, std::min(streams, kMaxSlots));
  struct Slot {
    bool busy = false;
    int s0 = 0, B = 0;
  } slot[kMaxSlots];
  t = StageTimes();

  // Wait for a slot's batch, accumulate its GPU-side durations, copy its results out.
  auto drain = [&](int sl) {
    Slot& sd = slot[sl];
    CUDA_CHECK(cudaEventSynchronize(p.ev[sl][3]));
    float a = 0, b = 0, c = 0;
    CUDA_CHECK(cudaEventElapsedTime(&a, p.ev[sl][0], p.ev[sl][1]));
    CUDA_CHECK(cudaEventElapsedTime(&b, p.ev[sl][1], p.ev[sl][2]));
    CUDA_CHECK(cudaEventElapsedTime(&c, p.ev[sl][2], p.ev[sl][3]));
    t.h2d_ms += a;
    t.kernel_ms += b;
    t.d2h_ms += c;
    std::memcpy(logits + static_cast<size_t>(sd.s0) * kOut, p.ph_logits[sl],
                static_cast<size_t>(sd.B) * kOut * sizeof(float));
    std::memcpy(pred + sd.s0, p.ph_pred[sl], static_cast<size_t>(sd.B) * sizeof(int32_t));
    sd.busy = false;
  };

  const double t0 = now_ms();
  int i = 0;
  for (int s0 = 0; s0 < n; s0 += batch, ++i) {
    const int B = std::min(batch, n - s0);
    const int sl = i % S;
    if (slot[sl].busy) drain(sl);  // slot must be free before its buffers are overwritten

    const double a = now_ms();
    preprocess_batch(raw + static_cast<size_t>(s0) * kIn, p.ph_x[sl], B, pre_threads);  // OpenMP
    t.pre_ms += now_ms() - a;

    cudaStream_t st = p.stream[sl];
    CUDA_CHECK(cudaEventRecord(p.ev[sl][0], st));
    CUDA_CHECK(cudaMemcpyAsync(p.d_x[sl], p.ph_x[sl], static_cast<size_t>(B) * kIn * sizeof(float),
                               cudaMemcpyHostToDevice, st));
    CUDA_CHECK(cudaEventRecord(p.ev[sl][1], st));
    launch_forward(p, sl, st, B);
    CUDA_CHECK(cudaEventRecord(p.ev[sl][2], st));
    CUDA_CHECK(cudaMemcpyAsync(p.ph_logits[sl], p.d_logits[sl],
                               static_cast<size_t>(B) * kOut * sizeof(float), cudaMemcpyDeviceToHost, st));
    CUDA_CHECK(cudaMemcpyAsync(p.ph_pred[sl], p.d_pred[sl], static_cast<size_t>(B) * sizeof(int32_t),
                               cudaMemcpyDeviceToHost, st));
    CUDA_CHECK(cudaEventRecord(p.ev[sl][3], st));
    slot[sl].busy = true;
    slot[sl].s0 = s0;
    slot[sl].B = B;
  }
  for (int k = 0; k < S; ++k) {  // oldest in-flight batch first
    const int sl = (i + k) % S;
    if (slot[sl].busy) drain(sl);
  }
  t.e2e_ms = now_ms() - t0;
}

}  // namespace nn
