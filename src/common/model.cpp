// model.cpp - weight file loader. Format: 'MLP1', int32 {in, hidden, out}, then float32
// W1[in][hidden], b1[hidden], W2[hidden][out], b2[out] (little-endian).
#include <cstdio>
#include <cstring>

#include "common.hpp"

namespace nn {

bool load_weights(const std::string& path, Weights& w, std::string& err) {
  FILE* f = std::fopen(path.c_str(), "rb");
  if (!f) { err = "cannot open " + path; return false; }
  char magic[4];
  int32_t dims[3];
  if (std::fread(magic, 1, 4, f) != 4 || std::memcmp(magic, "MLP1", 4) != 0 ||
      std::fread(dims, sizeof(int32_t), 3, f) != 3) {
    std::fclose(f); err = "bad weight header"; return false;
  }
  if (dims[0] != kIn || dims[1] != kHidden || dims[2] != kOut) {
    std::fclose(f); err = "weight dimensions do not match 784-256-10"; return false;
  }
  w.w1.resize(static_cast<size_t>(kIn) * kHidden);
  w.b1.resize(kHidden);
  w.w2.resize(static_cast<size_t>(kHidden) * kOut);
  w.b2.resize(kOut);
  bool ok = std::fread(w.w1.data(), 4, w.w1.size(), f) == w.w1.size() &&
            std::fread(w.b1.data(), 4, w.b1.size(), f) == w.b1.size() &&
            std::fread(w.w2.data(), 4, w.w2.size(), f) == w.w2.size() &&
            std::fread(w.b2.data(), 4, w.b2.size(), f) == w.b2.size();
  // the file must end exactly here
  ok = ok && std::fgetc(f) == EOF;
  std::fclose(f);
  if (!ok) err = "weight file has the wrong size";
  return ok;
}

}  // namespace nn
