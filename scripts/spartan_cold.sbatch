#!/bin/bash -l
#SBATCH --partition=gpus
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=24
#SBATCH --time=00:30:00
# Cold-start timing on a Spartan K40 node (10 fresh processes). Same flags as the reference runs.
#   sbatch --job-name=cs259_cold --export=ALL,PLATFORM=spartan_k40_native,ARCH_FLAGS=-march=native,BUILD_DIR=build_native scripts/spartan_cold.sbatch
module load gcc/11.4.1 cuda/11.7
cd "${SLURM_SUBMIT_DIR}"
export CUDA_ARCH=35 THREADS=24
echo "node: $(hostname) job: ${SLURM_JOB_ID} platform: ${PLATFORM}"
benchmarks/run_cold.sh "${PLATFORM}" 10
