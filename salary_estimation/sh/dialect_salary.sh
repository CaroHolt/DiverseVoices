#!/bin/bash


# Activate conda env
source /lustre/project/ki-topml/minbui/.bashrc
conda_initialize
micromamba activate audio

# Define the output folder variable
OUTPUT_FOLDER="/lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/output/bayrisch"

# Run the inference scripts
python /lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/inference.py \
    --model_name /lustre/project/ki-topml/kabecher/models/Meta-Llama-3.1-70B-Instruct \
    --output_folder $OUTPUT_FOLDER

python /lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/inference.py \
    --model_name /lustre/project/ki-topml/minbui/projects/models/sync/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659 \
    --output_folder $OUTPUT_FOLDER

python /lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/inference.py \
    --model_name /lustre/project/ki-topml/minbui/projects/models/sync/models--Qwen--Qwen2.5-7B-Instruct/snapshots/bb46c15ee4bb56c5b63245ef50fd7637234d6f75 \
    --output_folder $OUTPUT_FOLDER

python /lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/inference.py \
    --model_name /lustre/project/ki-topml/minbui/projects/models/sync/models--CohereForAI--aya-expanse-8b/snapshots/e46040a1bebe4f32f4d2f04b0a5b3af2c523d11b \
    --output_folder $OUTPUT_FOLDER

python /lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/inference.py \
    --model_name /lustre/project/ki-topml/minbui/projects/models/sync/models--CohereForAI--aya-expanse-32b/snapshots/c1df2547e1f5fe22e1f4897f980f231dc74cfc27 \
    --output_folder $OUTPUT_FOLDER

python /lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/inference.py \
    --model_name /lustre/project/ki-topml/minbui/projects/models/qwen_2.5_72b_chat \
    --output_folder $OUTPUT_FOLDER
