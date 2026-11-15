#!/usr/bin/env python3
"""Train the 784-256-10 MLP once with NumPy and export float32 weights for C++/CUDA inference.

Only NumPy is used (no PyTorch / TensorFlow). Hyper-parameters are fixed in advance and were
NOT tuned on the test set: He initialisation, Adam (lr 1e-3, beta 0.9/0.999), batch 128,
10 epochs, seed 0, cross-entropy loss.

Input preprocessing is identical to the C++ `preprocess_image` (per-image standardisation):
    x = (p - mean(p)) / sqrt(var(p) + 1e-5)      p = raw 0..255 pixel values, per image

Outputs (data/weights/):
    mlp_784_256_10.bin     header: 'MLP1' + int32 in, hidden, out; then float32 W1[784][256],
                           b1[256], W2[256][10], b2[10] (row-major, little-endian)
    ref_logits_100.bin     float32 [100][10] logits of the first 100 test images, computed
                           independently in float64 (anchor for the C++ correctness test)
    training_log.txt       loss per epoch and final test accuracy
    SHA256SUMS             checksums of the files above
"""
import hashlib
import struct
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "weights"
IN, HID, OUT_DIM = 784, 256, 10
EPS = 1e-5


def read_idx(path):
    with open(path, "rb") as f:
        magic = struct.unpack(">I", f.read(4))[0]
        ndim = magic & 0xFF
        dims = struct.unpack(">" + "I" * ndim, f.read(4 * ndim))
        return np.frombuffer(f.read(), dtype=np.uint8).reshape(dims)


def preprocess(u8, dtype=np.float32):
    x = u8.reshape(len(u8), IN).astype(dtype)
    mean = x.mean(axis=1, keepdims=True)
    var = ((x - mean) ** 2).mean(axis=1, keepdims=True)
    return (x - mean) / np.sqrt(var + dtype(EPS))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    xtr_u8 = read_idx(RAW / "train-images-idx3-ubyte")
    ytr = read_idx(RAW / "train-labels-idx1-ubyte").astype(np.int64)
    xte_u8 = read_idx(RAW / "t10k-images-idx3-ubyte")
    yte = read_idx(RAW / "t10k-labels-idx1-ubyte").astype(np.int64)
    assert xtr_u8.shape == (60000, 28, 28) and xte_u8.shape == (10000, 28, 28)

    xtr, xte = preprocess(xtr_u8), preprocess(xte_u8)
    rng = np.random.default_rng(0)
    params = {
        "w1": (rng.standard_normal((IN, HID)) * np.sqrt(2.0 / IN)).astype(np.float32),
        "b1": np.zeros(HID, np.float32),
        "w2": (rng.standard_normal((HID, OUT_DIM)) * np.sqrt(2.0 / HID)).astype(np.float32),
        "b2": np.zeros(OUT_DIM, np.float32),
    }
    m = {k: np.zeros_like(v) for k, v in params.items()}
    v = {k: np.zeros_like(p) for k, p in params.items()}
    lr, b1c, b2c, adam_eps, batch, epochs = 1e-3, 0.9, 0.999, 1e-8, 128, 10
    step = 0
    log = []

    def forward(x):
        h = np.maximum(x @ params["w1"] + params["b1"], 0.0)
        return h, h @ params["w2"] + params["b2"]

    for epoch in range(1, epochs + 1):
        order = rng.permutation(len(xtr))
        total = 0.0
        for i in range(0, len(order), batch):
            idx = order[i:i + batch]
            x, y = xtr[idx], ytr[idx]
            h, z = forward(x)
            z -= z.max(axis=1, keepdims=True)
            p = np.exp(z)
            p /= p.sum(axis=1, keepdims=True)
            total += -np.log(p[np.arange(len(y)), y] + 1e-12).sum()
            dz = p
            dz[np.arange(len(y)), y] -= 1.0
            dz /= len(y)
            grads = {"w2": h.T @ dz, "b2": dz.sum(axis=0)}
            dh = dz @ params["w2"].T
            dh[h <= 0] = 0.0
            grads["w1"] = x.T @ dh
            grads["b1"] = dh.sum(axis=0)
            step += 1
            for k in params:
                m[k] = b1c * m[k] + (1 - b1c) * grads[k]
                v[k] = b2c * v[k] + (1 - b2c) * grads[k] ** 2
                mh = m[k] / (1 - b1c ** step)
                vh = v[k] / (1 - b2c ** step)
                params[k] = (params[k] - lr * mh / (np.sqrt(vh) + adam_eps)).astype(np.float32)
        line = f"epoch {epoch:2d}  train_loss {total / len(xtr):.5f}"
        print(line)
        log.append(line)

    _, logits = forward(xte)
    acc = float((logits.argmax(axis=1) == yte).mean())
    line = f"final test accuracy (10000 images, float32 NumPy): {acc * 100:.2f}%"
    print(line)
    log.append(line)

    with open(OUT / "mlp_784_256_10.bin", "wb") as f:
        f.write(b"MLP1" + struct.pack("<3i", IN, HID, OUT_DIM))
        for k in ("w1", "b1", "w2", "b2"):
            f.write(np.ascontiguousarray(params[k], dtype="<f4").tobytes())

    # independent float64 reference for the first 100 test images
    x64 = preprocess(xte_u8[:100], np.float64)
    h64 = np.maximum(x64 @ params["w1"].astype(np.float64) + params["b1"].astype(np.float64), 0.0)
    ref = h64 @ params["w2"].astype(np.float64) + params["b2"].astype(np.float64)
    (OUT / "ref_logits_100.bin").write_bytes(np.ascontiguousarray(ref, dtype="<f4").tobytes())

    (OUT / "training_log.txt").write_text("\n".join(log) + "\n")
    sums = []
    for name in ("mlp_784_256_10.bin", "ref_logits_100.bin"):
        sums.append(f"{hashlib.sha256((OUT / name).read_bytes()).hexdigest()}  {name}")
    (OUT / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
