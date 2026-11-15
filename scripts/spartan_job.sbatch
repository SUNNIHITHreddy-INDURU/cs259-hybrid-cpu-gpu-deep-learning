#!/bin/bash -l
#SBATCH --partition=gpus
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=24
#SBATCH --time=03:00:00
# Full benchmark on a Spartan K40 node. Submit from the unpacked project directory, e.g.
#   sbatch --job-name=cs259_native \
#          --export=ALL,PLATFORM=spartan_k40_native,ARCH_FLAGS=-march=native,BUILD_DIR=build_native \
#          scripts/spartan_job.sbatch
module load gcc/11.4.1 cuda/11.7
cd "${SLURM_SUBMIT_DIR}"
export CUDA_ARCH=35                       # Tesla K40: compute capability 3.5
export THREADS="${THREADS:-1,2,4,8,12,16,24}" RUNS="${RUNS:-20}" WARMUP="${WARMUP:-3}"
echo "node: $(hostname)  job: ${SLURM_JOB_ID}  platform: ${PLATFORM}  arch flags: '${ARCH_FLAGS:-}'"
nvidia-smi -L
benchmarks/run_all.sh "${PLATFORM}" gpu
