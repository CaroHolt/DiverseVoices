#!/bin/bash
#SBATCH --partition=a100ai
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=5
#SBATCH --gres=gpu:3
#SBATCH --time=24:00:00
#SBATCH --mem=50gb
#SBATCH --output=/lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/sh/output/test_%j.log


# Activate conda env
source /lustre/project/ki-topml/minbui/.bashrc
conda_initialize
micromamba activate audio

python /lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/scripts/extract_decision.py
