#!/bin/sh


# check python version
python3 --version

# to surpress annoyingly verbose warning
export TOKENIZERS_PARALLELISM=true
export CUDA_VISIBLE_DEVICES=0

# store repo path
REPO="diverse_voices"


# set params
PROVIDER=Qwen #  # MERaLiON # Qwen2-Audio-7B-Instruct # scb10x/llama3.1-typhoon2-audio-8b-instruct
MODEL_NAME=Qwen2-Audio-7B-Instruct #MERaLiON-AudioLLM-Whisper-SEA-LION  #  Qwen2-Audio-7B

for EXPERIMENT in "english_accents"; do #"british_dialects" # "english_accents"

    for TASK in  "adjective_princeton" "adjective_arousal" "adjective_valence" "adjective_dominance" "profession"; do 

        python3 run_speech_qa.py \
            --model_name_or_path $PROVIDER/$MODEL_NAME \
            --task $TASK \
            --experiment $EXPERIMENT \
            --load_in_8bit False \
            --log_level "error" \
            --cache_dir "cache_dir" \
            --seq_length 256 \
            --batch_size 1 \
            --sample_size 0

    done;


done;