#!/bin/bash

# Define the base path for the files
BASE_PATH="/lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/output/bayrisch/"

# List of files to evaluate
files=("kabecher.csv" 
       "models--CohereForAI--aya-expanse-8b.csv"
       "models--meta-llama--Llama-3.1-8B-Instruct.csv"
       "models--CohereForAI--aya-expanse-32b.csv"
       "models--Qwen--Qwen2.5-7B-Instruct.csv"
       "projects.csv")
# Activate conda env
source /lustre/project/ki-topml/minbui/.bashrc
conda_initialize
micromamba activate audio

# Loop over each file and run the evaluation
for file in "${files[@]}"; do
  echo ""
  echo ""
  echo ""
  echo "-----Running evaluation for $file-----"
  python /lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/eval.py --input_file "${BASE_PATH}${file}"
done
