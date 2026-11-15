// validation.hpp - metrics used to prove that two implementations computed the same result.
#pragma once
#include <cstdint>

namespace nn {

struct Agreement {
  double max_abs_err = 0;    // max |a - b| over all logits
  double mean_abs_err = 0;   // mean |a - b| over all logits
  double pred_agreement = 0; // fraction of samples with identical predicted class
};

// Compare logits (n x 10) and predictions (n) of a test run against a reference run.
Agreement compare_runs(const float* ref_logits, const int32_t* ref_pred, const float* logits,
                       const int32_t* pred, int n);

// Fraction of predictions equal to the true labels.
double accuracy(const int32_t* pred, const uint8_t* labels, int n);

}  // namespace nn
