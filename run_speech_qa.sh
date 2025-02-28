#!/bin/sh


# check python version
python3 --version

# to surpress annoyingly verbose warning
export TOKENIZERS_PARALLELISM=true
export CUDA_VISIBLE_DEVICES=0

# store repo path
REPO="diverse_voices"

#"adjective_princeton" "adjective_arousal" "adjective_valence" "adjective_dominance" "profession" "location_country" "degree" "adjective_arousal_uniform" "adjective_valence_uniform" "adjective_dominance_uniform" "profession_binary"

#profession_binary_nurse_doctor profession_binary_hairdresser_CEO

# set params
PROVIDER=Qwen #  # MERaLiON # Qwen # scb10x/llama3.1-typhoon2-audio-8b-instruct
MODEL_NAME=Qwen2-Audio-7B-Instruct #MERaLiON-AudioLLM-Whisper-SEA-LION  #  Qwen2-Audio-7B-Instruct

for EXPERIMENT in "synthetic_data"; do #"british_dialects" # "english_accents"

    for TASK in "test_prompt2"; do #"adjective_princeton" "adjective_arousal" "adjective_valence" "adjective_dominance" "profession" # location_country degree adjective_arousal_uniform adjective_valence_uniform adjective_dominance_uniform 

        python3 run_speech_qa.py \
            --model_name_or_path $PROVIDER/$MODEL_NAME \
            --task $TASK \
            --experiment $EXPERIMENT \
            --load_in_8bit False \
            --log_level "error" \
            --cache_dir "/work/bbc6523/cache_dir" \
            --seq_length 256 \
            --batch_size 2 \
            --sample_size 0

    done;


done;