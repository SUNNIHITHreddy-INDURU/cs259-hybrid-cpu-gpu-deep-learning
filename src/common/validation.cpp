// validation.cpp - agreement metrics between two runs of the same workload.
#include "validation.hpp"

#include <cmath>

namespace nn {

Agreement compare_runs(const float* ref_logits, const int32_t* ref_pred, const float* logits,
                       const int32_t* pred, int n) {
  Agreement a;
  double sum = 0;
  long same = 0;
  const long total = static_cast<long>(n) * 10;
  for (long i = 0; i < total; ++i) {
    const double d = std::fabs(static_cast<double>(ref_logits[i]) - static_cast<double>(logits[i]));
    if (d > a.max_abs_err) a.max_abs_err = d;
    sum += d;
  }
  for (int i = 0; i < n; ++i) same += (ref_pred[i] == pred[i]);
  a.mean_abs_err = total ? sum / static_cast<double>(total) : 0.0;
  a.pred_agreement = n ? static_cast<double>(same) / n : 1.0;
  return a;
}

double accuracy(const int32_t* pred, const uint8_t* labels, int n) {
  long ok = 0;
  for (int i = 0; i < n; ++i) ok += (pred[i] == static_cast<int32_t>(labels[i]));
  return n ? static_cast<double>(ok) / n : 0.0;
}

}  // namespace nn
