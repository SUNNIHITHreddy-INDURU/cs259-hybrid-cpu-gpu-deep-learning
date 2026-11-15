// model.hpp - the exact arithmetic of the workload, shared by the serial, OpenMP and
// CUDA-with-CPU-preprocessing implementations. Keeping these functions identical guarantees
// that every implementation performs the same mathematical work.
#pragma once
#include <cmath>

#include "common.hpp"

namespace nn {

// Stage 0 - preprocessing: per-image standardisation of the raw 0..255 pixels
//   dst[i] = (src[i] - mean) / sqrt(var + eps)
// One image is always processed by one thread, in the same order, so results are bit-identical
// whether the caller is serial or OpenMP.
inline void preprocess_image(const uint8_t* src, float* dst) {
  float sum = 0.f;
  for (int i = 0; i < kIn; ++i) sum += static_cast<float>(src[i]);
  const float mean = sum / static_cast<float>(kIn);
  float ss = 0.f;
  for (int i = 0; i < kIn; ++i) {
    const float d = static_cast<float>(src[i]) - mean;
    ss += d * d;
  }
  const float inv = 1.0f / std::sqrt(ss / static_cast<float>(kIn) + kVarEps);
  for (int i = 0; i < kIn; ++i) dst[i] = (static_cast<float>(src[i]) - mean) * inv;
}

// Stage 1 - hidden layer for one sample and one block of kJBlock hidden units:
//   h[j] = ReLU(b1[j] + sum_k x[k] * W1[k][j])      (k = 0..kIn-1 in increasing order)
inline void layer1_block(const float* w1, const float* b1, const float* x, int jb, float* h) {
  const int j0 = jb * kJBlock;
  float acc[kJBlock];
  for (int t = 0; t < kJBlock; ++t) acc[t] = b1[j0 + t];
  for (int k = 0; k < kIn; ++k) {
    const float xv = x[k];
    const float* wr = w1 + static_cast<size_t>(k) * kHidden + j0;
    for (int t = 0; t < kJBlock; ++t) acc[t] += xv * wr[t];
  }
  for (int t = 0; t < kJBlock; ++t) h[j0 + t] = acc[t] > 0.f ? acc[t] : 0.f;
}

// Stage 2 - one output logit of one sample: z[c] = b2[c] + sum_j h[j] * W2[j][c]
inline float layer2_item(const float* w2, const float* b2, const float* h, int c) {
  float acc = b2[c];
  for (int j = 0; j < kHidden; ++j) acc += h[j] * w2[static_cast<size_t>(j) * kOut + c];
  return acc;
}

// Stage 3 - prediction: index of the first maximum logit.
inline int32_t argmax10(const float* z) {
  int best = 0;
  for (int c = 1; c < kOut; ++c)
    if (z[c] > z[best]) best = c;
  return best;
}

}  // namespace nn
