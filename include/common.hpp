// common.hpp - constants, data containers and loaders shared by every implementation.
#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace nn {

// Network: 784 -> 256 -> ReLU -> 10 (float32 everywhere).
constexpr int kIn = 784;      // 28 x 28 input pixels
constexpr int kHidden = 256;  // hidden units
constexpr int kOut = 10;      // digit classes
// One CPU work item computes kJBlock consecutive hidden units of one sample (one 64-byte
// cache line of a W1 row). Serial and OpenMP use the same blocks, so each output element is
// accumulated in exactly the same order in both.
constexpr int kJBlock = 16;
constexpr int kJBlocks = kHidden / kJBlock;
constexpr float kVarEps = 1e-5f;  // epsilon in per-image standardisation
static_assert(kHidden % kJBlock == 0, "kHidden must be a multiple of kJBlock");

struct Weights {
  std::vector<float> w1;  // [kIn][kHidden]   row-major (input-major)
  std::vector<float> b1;  // [kHidden]
  std::vector<float> w2;  // [kHidden][kOut]  row-major
  std::vector<float> b2;  // [kOut]
};

struct Dataset {
  int n = 0;
  std::vector<uint8_t> images;  // n * kIn raw pixels (0..255)
  std::vector<uint8_t> labels;  // n labels
};

// Per-pass stage times in milliseconds. A "pass" processes n images in batches.
//  CPU implementations fill pre/layer1/layer2; GPU implementations fill pre/h2d/kernel/d2h.
//  e2e_ms is the wall-clock time of the whole pass (what an application would observe).
struct StageTimes {
  double pre_ms = 0, layer1_ms = 0, layer2_ms = 0;
  double h2d_ms = 0, kernel_ms = 0, d2h_ms = 0;
  double e2e_ms = 0;
};

// Loaders (src/common). Return false and fill `err` on failure.
bool load_mnist(const std::string& images_path, const std::string& labels_path, Dataset& out,
                std::string& err);
bool load_weights(const std::string& path, Weights& w, std::string& err);

}  // namespace nn
