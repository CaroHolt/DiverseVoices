#!/bin/sh


# check python version
python3 --version

# to surpress annoyingly verbose warning
export TOKENIZERS_PARALLELISM=true
export CUDA_VISIBLE_DEVICES=3
export HF_HOME="/work/bbc6523/cache_dir"

# store repo path
REPO="diverse_voices"

#"adjective_princeton" "adjective_arousal" "adjective_valence" "adjective_dominance" "profession" "location_country" "degree" "adjective_arousal_uniform" "adjective_valence_uniform" "adjective_dominance_uniform" "profession_binary"

#profession_binary 



for MODEL in MERaLiON/MERaLiON-AudioLLM-Whisper-SEA-LION; do # moonshotai/Kimi-Audio-7B-Instruct  MERaLiON/MERaLiON-AudioLLM-Whisper-SEA-LION #microsoft/Phi-4-multimodal-instruct Qwen/Qwen2-Audio-7B-Instruct 

    for EXPERIMENT in  "british_dialects" "synthetic_data"; do #"british_dialects" # "english_accents" synthetic_compare_dataset_2

        for TASK in reference_letter story;do #reference_letter profession_binary adjective_binary profession_gender_compare profession_compare adjective_compare

            python3 run_speech_qa.py \
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