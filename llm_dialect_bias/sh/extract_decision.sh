#!/bin/bash
# to surpress annoyingly verbose warning
export TOKENIZERS_PARALLELISM=true
export CUDA_VISIBLE_DEVICES=0,1
export HF_HOME="/work/bbc6523/cache_dir"



#python scripts/extract_decision.py --model google/gemma-3-12b-it
#python scripts/extract_stories.py 
python scripts/eval_decision.py 