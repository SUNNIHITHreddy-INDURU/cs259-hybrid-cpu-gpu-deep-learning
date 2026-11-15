# Environment report - spartan_k40_gpu01

Generated: 2026-11-15T23:34:47Z by scripts/env_report.sh

## Operating system and CPU

$ uname -a
```
Linux gpu01.cluster 5.14.0-427.33.1.el9_4.x86_64 #1 SMP PREEMPT_DYNAMIC Wed Aug 28 17:34:59 UTC 2024 x86_64 x86_64 x86_64 GNU/Linux
```

$ lscpu
```
Architecture:                       x86_64
CPU op-mode(s):                     32-bit, 64-bit
Address sizes:                      46 bits physical, 48 bits virtual
Byte Order:                         Little Endian
CPU(s):                             28
On-line CPU(s) list:                0-27
Vendor ID:                          GenuineIntel
Model name:                         Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
CPU family:                         6
Model:                              79
Thread(s) per core:                 1
Core(s) per socket:                 14
Socket(s):                          2
Stepping:                           1
Frequency boost:                    enabled
CPU(s) scaling MHz:                 100%
CPU max MHz:                        2401.0000
CPU min MHz:                        1200.0000
BogoMIPS:                           4788.92
Flags:                              fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb cat_l3 cdp_l3 pti intel_ppin fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap intel_pt xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts
L1d cache:                          896 KiB (28 instances)
L1i cache:                          896 KiB (28 instances)
L2 cache:                           7 MiB (28 instances)
L3 cache:                           70 MiB (2 instances)
NUMA node(s):                       2
NUMA node0 CPU(s):                  0-13
NUMA node1 CPU(s):                  14-27
Vulnerability Gather data sampling: Not affected
Vulnerability Itlb multihit:        KVM: Mitigation: VMX unsupported
Vulnerability L1tf:                 Mitigation; PTE Inversion
Vulnerability Mds:                  Vulnerable: Clear CPU buffers attempted, no microcode; SMT disabled
Vulnerability Meltdown:             Mitigation; PTI
Vulnerability Mmio stale data:      Vulnerable: Clear CPU buffers attempted, no microcode; SMT disabled
Vulnerability Retbleed:             Not affected
Vulnerability Spec rstack overflow: Not affected
Vulnerability Spec store bypass:    Vulnerable
Vulnerability Spectre v1:           Mitigation; usercopy/swapgs barriers and __user pointer sanitization
Vulnerability Spectre v2:           Mitigation; Retpolines, STIBP disabled, RSB filling, PBRSB-eIBRS Not affected
Vulnerability Srbds:                Not affected
Vulnerability Tsx async abort:      Vulnerable: Clear CPU buffers attempted, no microcode; SMT disabled
```

$ grep -m1 model name /proc/cpuinfo
```
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
```

$ nproc
```
2
```

$ free -h
```
               total        used        free      shared  buff/cache   available
Mem:           125Gi       3.1Gi        99Gi       820Mi        24Gi       122Gi
Swap:          4.0Gi          0B       4.0Gi
```

## Compilers and build tools

$ c++ --version
```
c++ (GCC) 11.4.1 20231218 (Red Hat 11.4.1-3)
Copyright (C) 2021 Free Software Foundation, Inc.
```

$ g++ --version
```
g++ (GCC) 11.4.1 20231218 (Red Hat 11.4.1-3)
Copyright (C) 2021 Free Software Foundation, Inc.
```

$ make --version
```
GNU Make 4.3
Built for x86_64-redhat-linux-gnu
```

## OpenMP

$ bash -c echo | gcc -fopenmp -dM -E - | grep _OPENMP
```
#define _OPENMP 201511
```

## GPU and CUDA

$ nvidia-smi
```
Sun Nov 15 15:34:47 2026       
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 470.256.02   Driver Version: 470.256.02   CUDA Version: 11.4     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|                               |                      |               MIG M. |
|===============================+======================+======================|
|   0  Tesla K40m          Off  | 00000000:05:00.0 Off |                    0 |
| N/A   30C    P8    20W / 235W |      0MiB / 11441MiB |      0%      Default |
|                               |                      |                  N/A |
+-------------------------------+----------------------+----------------------+
                                                                               
+-----------------------------------------------------------------------------+
| Processes:                                                                  |
|  GPU   GI   CI        PID   Type   Process name                  GPU Memory |
|        ID   ID                                                   Usage      |
|=============================================================================|
|  No running processes found                                                 |
+-----------------------------------------------------------------------------+
```

$ nvidia-smi --query-gpu=name,compute_cap,memory.total,driver_version,clocks.max.sm,clocks.max.mem,pcie.link.gen.max,pcie.link.width.max --format=csv
```
Field "compute_cap" is not a valid field to query.

```

$ nvcc --version
```
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2022 NVIDIA Corporation
Built on Wed_Jun__8_16:49:14_PDT_2022
Cuda compilation tools, release 11.7, V11.7.99
Build cuda_11.7.r11.7/compiler.31442593_0
```

## Python

$ python3 -c import sys,numpy,pandas,matplotlib,scipy;print(sys.version.split()[0],'numpy',numpy.__version__,'pandas',pandas.__version__,'matplotlib',matplotlib.__version__,'scipy',scipy.__version__)
```
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'pandas'
```

## Tools and storage

$ git --version
```
git version 2.43.5
```

$ df -h /scratch/home/sinduru/cs259_native
```
Filesystem      Size  Used Avail Use% Mounted on
beegfs_nodev    524T  377T  148T  72% /scratch
```
