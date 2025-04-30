#!/bin/sh

# check python version
python3 --version

# to surpress annoyingly verbose warning
export TOKENIZERS_PARALLELISM=true
export CUDA_VISIBLE_DEVICES=0,1
export HF_HOME="/work/bbc6523/cache_dir"


#MODEL_PATH='Qwen/Qwen2.5-72B-Instruct' #Qwen/Qwen2.5-72B-Instruct  meta-llama/Meta-Llama-3.1-8B-Instruct 
#CohereLabs/aya-expanse-32b google/gemma-3-27b-it google/gemma-3-12b-it meta-llama/Llama-3.1-8B-Instruct Qwen/Qwen2.5-7B-Instruct CohereLabs/aya-expanse-8b
MODE='decision' #'decision' 'implicit' decision_robustness_0.95

for MODE in 'implicit_explicit'; do 

    for MODEL_PATH in CohereLabs/aya-expanse-32b; do 

        python scripts/inference.py \
            --model_name $MODEL_PATH \
            --output_folder output/$MODE \
            --gt_file data/prompts/tasks/$MODE.csv

    done

done