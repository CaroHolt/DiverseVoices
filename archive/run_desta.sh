#!/bin/sh


# check python version
python3 --version

# to surpress annoyingly verbose warning
export TOKENIZERS_PARALLELISM=true
export CUDA_VISIBLE_DEVICES=0

# store repo path
REPO="diverse_voices"

#"adjective_princeton" "adjective_arousal" "adjective_valence" "adjective_dominance" "profession" "location_country" "degree" "adjective_arousal_uniform" "adjective_valence_uniform" "adjective_dominance_uniform" "profession_binary"

#profession_binary 



for MODEL in DeSTA-ntu/DeSTA2-8B-beta; do # moonshotai/Kimi-Audio-7B-Instruct  MERaLiON/MERaLiON-AudioLLM-Whisper-SEA-LION #microsoft/Phi-4-multimodal-instruct Qwen/Qwen2-Audio-7B-Instruct 

    for EXPERIMENT in  "synthetic_compare_dataset"; do #"british_dialects" # "english_accents" synthetic_compare_dataset

        for TASK in profession_gender_compare; do #reference_letter profession_binary adjective_binary profession_gender_compare profession_compare adjective_compare

            python3 run_desta_qa.py \
                --model_name_or_path $MODEL \
                --task $TASK \
                --experiment $EXPERIMENT \
                --load_in_8bit False \
                --log_level "error" \
                --cache_dir "/work/bbc6523/cache_dir" \
                --seq_length 2048 \
                --batch_size 4 \
                --sample_size 0

        done

    done

done
