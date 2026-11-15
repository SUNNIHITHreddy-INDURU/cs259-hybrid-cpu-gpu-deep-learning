# Environment report - mac_m4

Generated: 2026-11-15T22:30:11Z by scripts/env_report.sh

## Operating system and CPU

$ uname -a
```
Darwin SUNNIHITHs-MacBook-Pro.local 25.6.0 Darwin Kernel Version 25.6.0: Fri Jul 31 19:11:03 PDT 2026; root:xnu-12377.161.14~5/RELEASE_ARM64_T8132 arm64
```

$ sw_vers
```
ProductName:		macOS
ProductVersion:		26.6.2
BuildVersion:		25G83
```

$ sysctl -n machdep.cpu.brand_string
```
Apple M4
```

$ sysctl hw.physicalcpu hw.logicalcpu hw.perflevel0.physicalcpu hw.perflevel1.physicalcpu hw.memsize hw.perflevel0.l2cachesize hw.perflevel1.l2cachesize
```
hw.physicalcpu: 10
hw.logicalcpu: 10
hw.perflevel0.physicalcpu: 4
hw.perflevel1.physicalcpu: 6
hw.memsize: 17179869184
hw.perflevel0.l2cachesize: 16777216
hw.perflevel1.l2cachesize: 4194304
```

## Compilers and build tools

$ c++ --version
```
Apple clang version 21.0.0 (clang-2100.3.34.2)
Target: arm64-apple-darwin25.6.0
```

$ g++ --version
```
Apple clang version 21.0.0 (clang-2100.3.34.2)
Target: arm64-apple-darwin25.6.0
```

$ clang++ --version
```
Apple clang version 21.0.0 (clang-2100.3.34.2)
Target: arm64-apple-darwin25.6.0
```

$ cmake --version
```
cmake version 4.4.4

```

$ make --version
```
GNU Make 3.81
Copyright (C) 2006  Free Software Foundation, Inc.
```

## OpenMP

$ brew list --versions libomp
```
==> Downloading Homebrew API data
✔︎ JSON API packages.arm64_tahoe.jws.json
libomp 23.1.2
```

## GPU and CUDA

nvidia-smi: not found (no NVIDIA GPU / driver on this machine)

nvcc: not found (CUDA cannot be compiled on this machine)

## Python

$ python3 -c import sys,numpy,pandas,matplotlib,scipy;print(sys.version.split()[0],'numpy',numpy.__version__,'pandas',pandas.__version__,'matplotlib',matplotlib.__version__,'scipy',scipy.__version__)
```
3.12.7 numpy 1.26.4 pandas 2.2.2 matplotlib 3.9.2 scipy 1.13.1
```

## Tools and storage

$ git --version
```
git version 2.54.0 (Apple Git-157)
```

$ df -h /Users/sunnihithreddy/Desktop/CS_259/cs259-hybrid-cpu-gpu-deep-learning
```
Filesystem      Size    Used   Avail Capacity iused ifree %iused  Mounted on
/dev/disk3s5   460Gi   307Gi   132Gi    70%    2.3M  1.4G    0%   /System/Volumes/Data
```
