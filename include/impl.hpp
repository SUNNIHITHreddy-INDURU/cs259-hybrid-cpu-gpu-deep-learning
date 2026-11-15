// impl.hpp - the four implementations behind one interface.
//
// Every run_* function processes `n` raw (uint8) images in consecutive batches of `batch`
// images and writes logits (n x 10) and predicted classes (n). All buffers it needs are
// allocated BEFORE its timer starts; one-time set-up (weights upload, device buffers) is
// excluded for every implementation and reported separately.
#pragma once
#include <cstdint>
#include <memory>
#include <string>

#include "common.hpp"

namespace nn {

// Implementation 1 - serial C++ (src/serial/serial_nn.cpp).
void run_serial(const Weights& w, const uint8_t* raw, int n, int batch, float* logits,
                int32_t* pred, StageTimes& t);

// Implementation 2 - OpenMP on the CPU (src/openmp/openmp_nn.cpp).
void run_openmp(const Weights& w, const uint8_t* raw, int n, int batch, int threads,
                float* logits, int32_t* pred, StageTimes& t);

// Micro-benchmarks that measure the platform's own limits (no assumed hardware numbers).
struct CpuMicro {
  int threads = 0;
  double fork_join_us = 0;  // cost of one empty OpenMP parallel region
  double triad_gbs = 0;     // STREAM-triad style memory bandwidth, GB/s
};
CpuMicro cpu_microbench(int threads);  // src/openmp/openmp_nn.cpp

#ifdef USE_CUDA
// Implementations 3 and 4 - CUDA and hybrid OpenMP-CUDA (src/cuda, src/hybrid).
class CudaRunner {
 public:
  struct Impl;  // defined in src/cuda/cuda_internal.cuh (kept out of this header on purpose)

  // max_batch: largest batch that will be used; block_dim: layer-1 thread block is block_dim x block_dim.
  CudaRunner(const Weights& w, int max_batch, int block_dim);
  ~CudaRunner();
  CudaRunner(const CudaRunner&) = delete;
  CudaRunner& operator=(const CudaRunner&) = delete;

  // CUDA-only: synchronous pageable transfers, one batch at a time. pre_threads == 1 runs the
  // preprocessing serially ("cuda"); pre_threads > 1 runs it with OpenMP but without any
  // overlap ("hybrid_seq").
  void run_sync(const uint8_t* raw, int n, int batch, int pre_threads, float* logits,
                int32_t* pred, StageTimes& t);

  // Hybrid: OpenMP preprocessing of batch i overlaps with CUDA transfer+compute of earlier
  // batches using `streams` CUDA streams and pinned host buffers (src/hybrid).
  void run_pipelined(const uint8_t* raw, int n, int batch, int pre_threads, int streams,
                     float* logits, int32_t* pred, StageTimes& t);

  std::string device_name() const;
  std::string device_info() const;   // compute capability, SMs, memory, driver/runtime
  int runtime_version() const;       // CUDA runtime version, e.g. 12020
  double setup_upload_ms() const;    // one-time weight upload

 private:
  std::unique_ptr<Impl> p_;
};

struct GpuMicro {
  double h2d_pageable_gbs = 0, h2d_pinned_gbs = 0, d2h_pageable_gbs = 0, d2h_pinned_gbs = 0;
  double d2d_gbs = 0;            // device-to-device copy bandwidth (read+write counted)
  double launch_empty_us = 0;    // mean time of an asynchronous empty kernel launch
  double launch_sync_us = 0;     // mean launch + synchronise latency of an empty kernel
};
GpuMicro gpu_microbench();  // src/cuda/cuda_nn.cu
#endif

}  // namespace nn
