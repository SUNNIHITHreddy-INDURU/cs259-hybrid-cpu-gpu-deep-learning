// serial_nn.cpp - Implementation 1: single-threaded C++ inference with ordinary loops.
//
// Per batch: preprocess every image, hidden layer (batch x 16 blocks), output layer
// (batch x 10), argmax. No threads, no libraries; the compiler flags are identical to the
// OpenMP build (-O3) so any speed difference comes from parallelism, not from optimisation level.
#include <algorithm>
#include <vector>

#include "impl.hpp"
#include "model.hpp"
#include "timing.hpp"

namespace nn {

void run_serial(const Weights& w, const uint8_t* raw, int n, int batch, float* logits,
                int32_t* pred, StageTimes& t) {
  std::vector<float> x(static_cast<size_t>(batch) * kIn);
  std::vector<float> h(static_cast<size_t>(batch) * kHidden);
  t = StageTimes();
  const double t0 = now_ms();
  for (int s = 0; s < n; s += batch) {
    const int B = std::min(batch, n - s);
    const double a = now_ms();
    for (int b = 0; b < B; ++b)
      preprocess_image(raw + static_cast<size_t>(s + b) * kIn, &x[static_cast<size_t>(b) * kIn]);
    const double b1 = now_ms();
    for (int b = 0; b < B; ++b)
      for (int jb = 0; jb < kJBlocks; ++jb)
        layer1_block(w.w1.data(), w.b1.data(), &x[static_cast<size_t>(b) * kIn], jb,
                     &h[static_cast<size_t>(b) * kHidden]);
    const double c = now_ms();
    for (int b = 0; b < B; ++b) {
      float* z = logits + static_cast<size_t>(s + b) * kOut;
      for (int k = 0; k < kOut; ++k)
        z[k] = layer2_item(w.w2.data(), w.b2.data(), &h[static_cast<size_t>(b) * kHidden], k);
      pred[s + b] = argmax10(z);
    }
    const double d = now_ms();
    t.pre_ms += b1 - a;
    t.layer1_ms += c - b1;
    t.layer2_ms += d - c;
  }
  t.e2e_ms = now_ms() - t0;
}

}  // namespace nn
