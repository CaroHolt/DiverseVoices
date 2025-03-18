#!/bin/bash
#SBATCH --partition=a100ai
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=5
#SBATCH --gres=gpu:3
#SBATCH --time=24:00:00
#SBATCH --mem=50gb
#SBATCH --output=/lustre/project/ki-topml/minbui/repos/FiscalKnowledgeBias/slurm_output/test_%j.log



# Activate conda env
source /lustre/project/ki-topml/minbui/.bashrc
conda_initialize
micromamba activate audio

# List of models
MODEL_NAMES=(
  "/lustre/project/ki-topml/minbui/projects/models/Llama-3.3-70B-Instruct"
  "/lustre/project/ki-topml/kabecher/models/Meta-Llama-3.1-70B-Instruct"
  "/lustre/project/ki-topml/minbui/projects/models/sync/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659"
  "/lustre/project/ki-topml/minbui/projects/models/qwen_2.5_72b_chat"
  "/lustre/project/ki-topml/minbui/projects/models/sync/models--Qwen--Qwen2.5-7B-Instruct/snapshots/bb46c15ee4bb56c5b63245ef50fd7637234d6f75"
  "/lustre/project/ki-topml/minbui/projects/models/sync/models--CohereForAI--aya-expanse-32b/snapshots/c1df2547e1f5fe22e1f4897f980f231dc74cfc27"
  "/lustre/project/ki-topml/minbui/projects/models/sync/models--CohereForAI--aya-expanse-8b/snapshots/e46040a1bebe4f32f4d2f04b0a5b3af2c523d11b"
)

# Define the model name and script location
SCRIPT_PATH="/lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/scripts/inference.py"
OUTPUT_FOLDER="/lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/output/implicit"
GT_FILE="/lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/data/prompts/tasks/implicit.csv"
# Loop through the models
for MODEL_NAME in "${MODEL_NAMES[@]}"; do
    # Loop through the dimensions for each model
    python $SCRIPT_PATH \
        --model_name $MODEL_NAME \
        --output_folder "$OUTPUT_FOLDER" \
        --gt_file "$GT_FILE"
done
