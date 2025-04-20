#!/bin/sh

# check python version
python3 --version

# to surpress annoyingly verbose warning
export TOKENIZERS_PARALLELISM=true
export CUDA_VISIBLE_DEVICES=0,1,2
export HF_HOME="/work/bbc6523/cache_dir"


MODEL_PATH='meta-llama/Meta-Llama-3.1-70B-Instruct'

python scripts/inference.py \
    --model_name $MODEL_PATH \
    --output_folder output/implicit \
    --gt_file data/prompts/tasks/implicit.csv