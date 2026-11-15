// data_loader.cpp - reads MNIST IDX files (big-endian) and validates their headers.
#include <cstdio>

#include "common.hpp"

namespace nn {
namespace {

bool read_u32_be(FILE* f, uint32_t& v) {
  unsigned char b[4];
  if (std::fread(b, 1, 4, f) != 4) return false;
  v = (uint32_t(b[0]) << 24) | (uint32_t(b[1]) << 16) | (uint32_t(b[2]) << 8) | uint32_t(b[3]);
  return true;
}

}  // namespace

bool load_mnist(const std::string& images_path, const std::string& labels_path, Dataset& out,
                std::string& err) {
  FILE* fi = std::fopen(images_path.c_str(), "rb");
  if (!fi) { err = "cannot open " + images_path + " (run data/download_mnist.py)"; return false; }
  uint32_t magic, n, rows, cols;
  if (!read_u32_be(fi, magic) || !read_u32_be(fi, n) || !read_u32_be(fi, rows) ||
      !read_u32_be(fi, cols)) {
    std::fclose(fi); err = "truncated image header"; return false;
  }
  if (magic != 2051 || rows != 28 || cols != 28) {
    std::fclose(fi); err = "bad image header (expected magic 2051, 28x28)"; return false;
  }
  out.images.resize(static_cast<size_t>(n) * kIn);
  if (std::fread(out.images.data(), 1, out.images.size(), fi) != out.images.size()) {
    std::fclose(fi); err = "truncated image data"; return false;
  }
  std::fclose(fi);

  FILE* fl = std::fopen(labels_path.c_str(), "rb");
  if (!fl) { err = "cannot open " + labels_path; return false; }
  uint32_t lmagic, ln;
  if (!read_u32_be(fl, lmagic) || !read_u32_be(fl, ln) || lmagic != 2049 || ln != n) {
    std::fclose(fl); err = "bad label header or count mismatch"; return false;
  }
  out.labels.resize(n);
  if (std::fread(out.labels.data(), 1, n, fl) != n) {
    std::fclose(fl); err = "truncated label data"; return false;
  }
  std::fclose(fl);
  for (uint8_t l : out.labels)
    if (l > 9) { err = "label out of range"; return false; }
  out.n = static_cast<int>(n);
  return true;
}

}  // namespace nn
