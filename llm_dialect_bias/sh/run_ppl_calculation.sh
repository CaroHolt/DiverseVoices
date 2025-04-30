#!/bin/sh

# check python version
python3 --version

# to surpress annoyingly verbose warning
export TOKENIZERS_PARALLELISM=true
export CUDA_VISIBLE_DEVICES=0,3
export HF_HOME="/work/bbc6523/cache_dir"

# mistralai/Mistral-7B-Instruct-v0.1 mistralai/Mistral-7B-Instruct-v0.2 meta-llama/Llama-2-13b-chat-hf HuggingFaceH4/zephyr-7b-beta meta-llama/Llama-2-7b-chat-hf 

#Qwen/Qwen2.5-72B-Instruct meta-llama/Meta-Llama-3.1-8B-Instruct CohereLabs/aya-expanse-32b google/gemma-3-27b-it google/gemma-3-12b-it meta-llama/Llama-3.1-8B-Instruct Qwen/Qwen2.5-7B-Instruct CohereLabs/aya-expanse-8b; do  

SEED=10

for MODEL in Qwen/Qwen2.5-72B-Instruct meta-llama/Meta-Llama-3.1-8B-Instruct CohereLabs/aya-expanse-32b meta-llama/Llama-3.1-8B-Instruct Qwen/Qwen2.5-7B-Instruct CohereLabs/aya-expanse-8b; do 

    for COL in dialect dialect_original; do  

        python3 ../scripts/calculate_perplexity_2.py \
            --model_name ${MODEL} \
            --input_path '../data/prompts/tasks/implicit_robustness_0.33.csv' \
            --input_col ${COL} \
            --cache_dir '/work/bbc6523/cache_dir' \
            --seed ${SEED} \
            --batch_size 16


    done;

done;
