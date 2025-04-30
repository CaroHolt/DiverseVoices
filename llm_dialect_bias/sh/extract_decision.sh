#!/bin/bash
# to surpress annoyingly verbose warning
export TOKENIZERS_PARALLELISM=true
export CUDA_VISIBLE_DEVICES=0,1,3
export HF_HOME="/work/bbc6523/cache_dir"



#python scripts/extract_decision.py --model google/gemma-3-12b-it
python scripts/parse_decision_story.py --model google/gemma-3-12b-it