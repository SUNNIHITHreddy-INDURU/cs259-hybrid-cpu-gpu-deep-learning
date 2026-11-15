#!/usr/bin/env python3
"""Download the MNIST IDX files, verify checksums, and decompress them to data/raw/.

Usage:
    python3 data/download_mnist.py            # download (if missing) + verify + decompress
    python3 data/download_mnist.py --verify   # only verify files already present
    python3 data/download_mnist.py --write-sha256   # (re)generate data/SHA256SUMS from the files

Integrity checks performed on every .gz file:
  1. MD5 against the values published with the dataset mirrors (MD5_PUBLISHED below).
  2. SHA-256 against data/SHA256SUMS (recorded in this repository).
"""
import gzip
import hashlib
import shutil
import sys
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
RAW_DIR = DATA_DIR / "raw"
SHA_FILE = DATA_DIR / "SHA256SUMS"

MIRRORS = [
    "https://ossci-datasets.s3.amazonaws.com/mnist/",
    "https://storage.googleapis.com/cvdf-datasets/mnist/",
]

MD5_PUBLISHED = {
    "train-images-idx3-ubyte.gz": "f68b3c2dcbeaaa9fbdd348bbdeb94873",
    "train-labels-idx1-ubyte.gz": "d53e105ee54ea40749a09fcbcd1e9432",
    "t10k-images-idx3-ubyte.gz": "9fb629c4189551a2d022fa330f9573f3",
    "t10k-labels-idx1-ubyte.gz": "ec29112dd5afa0611ce80d1b7f02629c",
}


def digest(path, algo):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_sha_file():
    sums = {}
    if SHA_FILE.exists():
        for line in SHA_FILE.read_text().splitlines():
            if line.strip():
                value, name = line.split()
                sums[name] = value
    return sums


def fetch(name):
    dest = RAW_DIR / name
    last_err = None
    for base in MIRRORS:
        try:
            print(f"  downloading {base}{name}")
            urllib.request.urlretrieve(base + name, dest)
            return
        except Exception as exc:  # network errors differ by platform
            last_err = exc
            print(f"  failed: {exc}")
    raise SystemExit(f"could not download {name}: {last_err}")


def verify(name):
    path = RAW_DIR / name
    ok = digest(path, "md5") == MD5_PUBLISHED[name]
    sha_known = read_sha_file().get(name)
    if sha_known is not None:
        ok = ok and digest(path, "sha256") == sha_known
    return ok


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    verify_only = "--verify" in sys.argv
    for name in MD5_PUBLISHED:
        path = RAW_DIR / name
        if not path.exists():
            if verify_only:
                raise SystemExit(f"missing {path}")
            fetch(name)
        if not verify(name):
            raise SystemExit(f"checksum mismatch for {name}; delete it and retry")
        print(f"OK  {name}")
        raw = RAW_DIR / name[:-3]
        if not raw.exists():
            with gzip.open(path, "rb") as src, open(raw, "wb") as dst:
                shutil.copyfileobj(src, dst)
    if "--write-sha256" in sys.argv:
        lines = [f"{digest(RAW_DIR / n, 'sha256')}  {n}" for n in MD5_PUBLISHED]
        SHA_FILE.write_text("\n".join(lines) + "\n")
        print(f"wrote {SHA_FILE}")


if __name__ == "__main__":
    main()
