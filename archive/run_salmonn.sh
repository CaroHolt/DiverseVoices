#!/bin/sh


# check python version
python3 --version

# to surpress annoyingly verbose warning
export TOKENIZERS_PARALLELISM=true
export CUDA_VISIBLE_DEVICES=3
export HF_HOME="/work/bbc6523/cache_dir"


for EXPERIMENT in  "synthetic_compare_dataset"; do #synthetic_compare_dataset synthetic_data british_dialects_compare

    for TASK in profession_compare; do 

        python3 /work/bbc6523/diverse_voices/SALMONN-7B/cli_inference.py \
            --ckpt_path /work/bbc6523/diverse_voices/SALMONN-7B/salmonn_7b_v0.pth \
            --whisper_path /work/bbc6523/diverse_voices/SALMONN-7B/whisper-large-v2 \
            --beats_path /work/bbc6523/diverse_voices/SALMONN-7B/beats_path/BEATs_iter3_plus_AS2M_finetuned_on_AS2M_cpt2.pt \
            --vicuna_path /work/bbc6523/diverse_voices/SALMONN-7B/vicuna-7b-v1.5 \
            --task $TASK \
            --experiment $EXPERIMENT

    done

done