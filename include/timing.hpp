// timing.hpp - wall-clock timer and platform metadata recorded with every measurement.
#pragma once
#include <chrono>
#include <string>

namespace nn {

// Monotonic wall-clock time in milliseconds.
inline double now_ms() {
  using clock = std::chrono::steady_clock;
  return std::chrono::duration<double, std::milli>(clock::now().time_since_epoch()).count();
}

struct PlatformInfo {
  std::string cpu_model;     // e.g. "Apple M4"
  int logical_threads = 0;   // hardware threads visible to the program
  std::string compiler;      // host compiler version string
};

PlatformInfo query_platform();  // src/common/timing.cpp

}  // namespace nn
