#!/bin/sh



# check python version
python3 --version

# to surpress annoyingly verbose warning
export TOKENIZERS_PARALLELISM=true
export CUDA_VISIBLE_DEVICES=3
export HF_HOME="/work/bbc6523/cache_dir"

# set params
PROVIDER="CohereLabs" #Qwen/Qwen2.5-32B-Instruct
MODEL_NAME="aya-expanse-8b" # meta-llama/Meta-Llama-3-8B-Instruct #Llama-3.1-8B-Instruct

for EXPERIMENT in  "/home/bbc6523/code/DiverseVoices/llm_dialect_bias/data/prompts/tasks/implicit"; do #"british_dialects"

    python3 llm_as_a_judge_2.py \
        --model_name_or_path $PROVIDER/$MODEL_NAME \
        --test_data_input_path $EXPERIMENT.csv \
        --n_test_samples 0 \
        --batch_size 4 \
        --input_col 'prompts' \
        --test_data_output_path $EXPERIMENT.csv \
        --load_in_8bit False \
        --log_level "info" \
        --cache_dir /work/bbc6523/cache_dir

done