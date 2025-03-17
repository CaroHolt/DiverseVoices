#!/bin/bash
#SBATCH --partition=a100ai
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=5
#SBATCH --gres=gpu:2
#SBATCH --time=10:00:00
#SBATCH --mem=50gb
#SBATCH --output=/lustre/project/ki-topml/minbui/repos/FiscalKnowledgeBias/slurm_output/test_%j.log


# Environment
source /lustre/project/ki-topml/minbui/.bashrc
conda_initialize
micromamba activate audio

# yingly verbose warning
export TOKENIZERS_PARALLELISM=true

# store repo path
# REPO="diverse_voices"

# set params
#MODEL_PATH="/lustre/project/ki-topml/minbui/projects/models/Llama-3.3-70B-Instruct"
#MODEL_PATH="/lustre/project/ki-topml/minbui/projects/models/sync/models--Qwen--Qwen2.5-7B-Instruct/snapshots/bb46c15ee4bb56c5b63245ef50fd7637234d6f75"
MODEL_PATH="/lustre/project/ki-topml/minbui/projects/models/Llama-3.3-70B-Instruct"
#MODEL_PATH="/lustre/project/ki-topml/minbui/projects/models/sync/models--Qwen--Qwen2.5-7B-Instruct/snapshots/bb46c15ee4bb56c5b63245ef50fd7637234d6f75"

for EXPERIMENT in "text"; do #"british_dialects" # "english_accents"

    for TASK in "profession_explicit"; do 
    # for TASK in  "adjective_arousal" "profession"; do 

        python run_text_qa.py \
            --model_name_or_path $MODEL_PATH \
            --task $TASK \
            --experiment $EXPERIMENT \
            --load_in_8bit False \
            --log_level "error" \
            --cache_dir "cache_dir" \
            --seq_length 16 \
            --batch_size 32 \
            --sample_size 0

    done;


done;