#!/bin/bash
#SBATCH --partition=a100ai
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=5
#SBATCH --gres=gpu:2
#SBATCH --time=24:00:00
#SBATCH --mem=50gb
#SBATCH --output=/lustre/project/ki-topml/minbui/repos/FiscalKnowledgeBias/slurm_output/test_%j.log


# Model names
BASE_DIR="/lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation"
OUTPUT_FOLDER="/lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/output/text_creation"
GT_FILE="/lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/data/prompts/text_creation/raw_text.csv"


# Model names
MODELS=(
  "/lustre/project/ki-topml/minbui/projects/models/Llama-3.3-70B-Instruct"
)

source /lustre/project/ki-topml/minbui/.bashrc
conda_initialize
micromamba activate audio

nvidia-smi

cd "$BASE_DIR"

# Iterate over languages and models
echo "Output folder: $OUTPUT_FOLDER"
# Run with each model_name
for MODEL in "${MODELS[@]}"; do
  echo "Model: $MODEL"
  if [ -n "$MODEL" ]; then
    python "$BASE_DIR/scripts/inference.py" --model_name "$MODEL" --output_folder "$OUTPUT_FOLDER" --gt_file "$GT_FILE"
  fi
done
