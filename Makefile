# Makefile - builds the CPU-only binaries (serial + OpenMP) and, where nvcc exists, the GPU ones.
#   make cpu        -> build/cpu/nn_bench, build/cpu/nn_validate
#   make gpu        -> build/gpu/nn_bench, build/gpu/nn_validate (needs nvcc)
#   make test       -> build cpu and run the correctness gate
#   make clean
# Variables: CUDA_ARCH=75 (override the auto-detected compute capability), NVCC=/path/to/nvcc

UNAME := $(shell uname -s)
STD   := -std=c++14

ifeq ($(UNAME),Darwin)
  CXX      := clang++
  OMP_PFX  := $(shell brew --prefix libomp 2>/dev/null)
  OMPFLAGS := -Xpreprocessor -fopenmp -I$(OMP_PFX)/include
  OMPLIBS  := -L$(OMP_PFX)/lib -lomp -Wl,-rpath,$(OMP_PFX)/lib
else
  CXX      ?= g++
  OMPFLAGS := -fopenmp
  OMPLIBS  := -fopenmp
endif

CXXFLAGS := -O3 $(STD) -Wall -Wextra -Iinclude $(OMPFLAGS)

COMMON_SRC := src/common/data_loader.cpp src/common/model.cpp src/common/timing.cpp \
              src/common/validation.cpp src/serial/serial_nn.cpp src/openmp/openmp_nn.cpp

NVCC ?= nvcc
# compute capability of the first GPU, e.g. 7.5 -> 75 (falls back to 75 if it cannot be queried)
CUDA_ARCH ?= $(shell nvidia-smi --query-gpu=compute_cap --format=csv,noheader 2>/dev/null | head -1 | tr -d '. \r' | grep -E '^[0-9]+$$' || echo 75)
NVCCFLAGS := -O3 $(STD) -Iinclude -arch=sm_$(CUDA_ARCH) -DUSE_CUDA -Wno-deprecated-gpu-targets \
             -Xcompiler -fopenmp,-O3,-Wall

.PHONY: all cpu gpu test clean
all: cpu

cpu: build/cpu/nn_bench build/cpu/nn_validate

build/cpu/nn_bench: src/app/main.cpp $(COMMON_SRC) | build/cpu
	$(CXX) $(CXXFLAGS) $^ -o $@ $(OMPLIBS)
build/cpu/nn_validate: src/app/validate_main.cpp $(COMMON_SRC) | build/cpu
	$(CXX) $(CXXFLAGS) $^ -o $@ $(OMPLIBS)

GPU_SRC := $(COMMON_SRC) src/cuda/cuda_nn.cu src/hybrid/hybrid_pipeline.cu
gpu: build/gpu/nn_bench build/gpu/nn_validate

build/gpu/nn_bench: src/app/main.cpp $(GPU_SRC) | build/gpu
	$(NVCC) $(NVCCFLAGS) -Isrc/cuda $^ -o $@ -lgomp
build/gpu/nn_validate: src/app/validate_main.cpp $(GPU_SRC) | build/gpu
	$(NVCC) $(NVCCFLAGS) -Isrc/cuda $^ -o $@ -lgomp

build/cpu build/gpu:
	mkdir -p $@

test: cpu
	build/cpu/nn_validate

clean:
	rm -rf build
