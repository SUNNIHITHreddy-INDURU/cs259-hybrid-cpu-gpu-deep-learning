// cuda_internal.cuh - state and helpers shared by cuda_nn.cu (synchronous CUDA path) and
// hybrid_pipeline.cu (pipelined hybrid). Not included by any host-only file.
#pragma once
#include <cuda_runtime.h>

#include <cstdio>
#include <cstdlib>
#include <string>

#include "common.hpp"
#include "impl.hpp"
#include "model.hpp"

// Every CUDA runtime call is wrapped: on failure print the call, location and error string, exit.
#define CUDA_CHECK(call)                                                                   \
  do {                                                                                     \
    const cudaError_t err_ = (call);                                                       \
    if (err_ != cudaSuccess) {                                                             \
      std::fprintf(stderr, "CUDA error in `%s` at %s:%d: %s\n", #call, __FILE__, __LINE__, \
                   cudaGetErrorString(err_));                                              \
      std::exit(2);                                                                        \
    }                                                                                      \
  } while (0)

namespace nn {

constexpr int kMaxSlots = 4;  // buffer sets / streams available to the pipelined hybrid

struct CudaRunner::Impl {
  int max_batch = 0;
  int block_dim = 16;  // layer-1 thread block is block_dim x block_dim
  // model weights resident on the device (uploaded once)
  float *d_w1 = nullptr, *d_b1 = nullptr, *d_w2 = nullptr, *d_b2 = nullptr;
  // one buffer set per slot; the synchronous path uses slot 0 only
  float* d_x[kMaxSlots] = {};
  float* d_h[kMaxSlots] = {};
  float* d_logits[kMaxSlots] = {};
  int32_t* d_pred[kMaxSlots] = {};
  // pinned (page-locked) host buffers used by the pipelined hybrid
  float* ph_x[kMaxSlots] = {};
  float* ph_logits[kMaxSlots] = {};
  int32_t* ph_pred[kMaxSlots] = {};
  cudaStream_t stream[kMaxSlots] = {};
  // events per slot: [0] before H2D, [1] after H2D, [2] after kernels, [3] after D2H
  cudaEvent_t ev[kMaxSlots][4] = {};
  std::string name, info;
  int runtime = 0;
  double setup_ms = 0;     // weight allocation + upload
  double init_ms = 0;      // context creation
  double alloc_ms = 0;     // buffers, pinned memory, streams, events
};

// Launch the three kernels (hidden layer, output layer, argmax) for one batch of B samples
// that already sits in d_x[slot]; results land in d_logits[slot] / d_pred[slot].
void launch_forward(CudaRunner::Impl& p, int slot, cudaStream_t stream, int B);

// Preprocess B consecutive raw images into x: serially for threads <= 1, otherwise with OpenMP
// (one image per iteration, so results are bit-identical to the serial path).
inline void preprocess_batch(const uint8_t* raw, float* x, int B, int threads) {
  if (threads <= 1) {
    for (int b = 0; b < B; ++b)
      preprocess_image(raw + static_cast<size_t>(b) * kIn, x + static_cast<size_t>(b) * kIn);
  } else {
#pragma omp parallel for num_threads(threads) schedule(static)
    for (int b = 0; b < B; ++b)
      preprocess_image(raw + static_cast<size_t>(b) * kIn, x + static_cast<size_t>(b) * kIn);
  }
}

}  // namespace nn
