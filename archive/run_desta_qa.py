from datasets import load_dataset
from transformers import AutoModel, AutoModelForSpeechSeq2Seq, AutoProcessor, Qwen2AudioForConditionalGeneration, AutoTokenizer, AutoModelForCausalLM#, Qwen2_5OmniModel
import pandas as pd
import librosa
import torch
from tqdm import tqdm
import os
import time 
import fire
import logging
import soundfile as sf
from prompts import *


storage_path = '/work/bbc6523/diverse_voices/'
    

def get_query_list(task, df):
    query_list = create_prompts(task, 'english', 'audio', len(df))
    audio_files = df['audio_file'].tolist()
    chat_prompts = []

    for i in range(len(query_list)):
        conversation = [
            {"role": "system", "content": "You are a helpful voice assistant."},
            {"role": "audio", "content": storage_path + 'synthetic_audio/' + audio_files[i]},
            {"role": "user", "content": query_list[i]}
            ]

        chat_prompts.append(conversation)
    return chat_prompts



def get_dataset(experiment):
    if 'african_dialects' in experiment:
        df = pd.read_csv(storage_path + 'full_text_african_dialects.csv')
        component = experiment.replace('african_dialects_', '')
        df = df[(df['content_token_length'] > 10) & (df['CORAAL Component'] == component)]

    elif experiment == 'english_accents':
        df = pd.read_csv(storage_path + 'data/' + 'english_accents.csv')

    elif 'british_dialects' in experiment:
        df = pd.read_csv(storage_path + 'data/' + experiment + '.csv')

    elif 'synthetic' in experiment:
        df = pd.read_csv(storage_path + 'data/' + experiment + '.csv')

    return df




def main(
        # data parameters
        task: str,
        experiment: str,

        # model parameters
        model_name_or_path: str,

        cache_dir:str,
          
        # quantization parameters
        load_in_8bit: bool,
           
        # misc parameters
        log_level: str,

        sample_size:int,

        batch_size:int,
        seq_length:int

        ):

        df = get_dataset(experiment)

        model = AutoModel.from_pretrained("DeSTA-ntu/DeSTA2-8B-beta", 
                                trust_remote_code=True,
                                cache_dir='/work/bbc6523/cache_dir',
                                token=token)
        model.speech_perception.whisper.generation_config.forced_decoder_ids = None
        model.to("cuda")

        chat_prompts = get_query_list(task, df)


        results = []

        print(len(chat_prompts))
        print(len(df))

        for prompt in tqdm(chat_prompts):
            generated_ids = model.chat(
                prompt, 
                max_new_tokens=seq_length, 
                do_sample=True, 
                temperature=0.1, 
                top_p=0.9, 
            )
            response = model.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
            if len(response) > 1: 
                print('RESPONSE TOO LONG')
                print(response)
                print(type(response))
            results.extend(response)

        print(len(results))

        output_path = storage_path + 'output/' + experiment + '/'
        if not os.path.exists(output_path):
            os.makedirs(output_path)


        if sample_size > 0:
            print(results)
        else: 
            output_file = output_path + str(model_name_or_path.split('/')[1]) + '.csv'
            if os.path.exists(output_file):
                df = pd.read_csv(output_file)
            df[f'model_response_{task}'] = results
            df[f'model_prompt_{task}'] = chat_prompts
            df.to_csv(output_file, index=False)


def wrapper(task='profession_binary', **kwargs):
    print(task)
    if task == 'profession_binary':
        task_list = [f'profession_binary_{i}' for i in range(22)]
        for t in task_list:
            print(f"\n=== Running task: {t} ===")
            st = time.time()
            main(task=t, **kwargs)
            logging.info(f'Task "{t}" finished in {time.time() - st:.2f} seconds')
    elif task == 'adjective_binary':
        task_list = [f'adjective_binary_{i}' for i in range(22)]
        for t in task_list:
            print(f"\n=== Running task: {t} ===")
            st = time.time()
            main(task=t, **kwargs)
            logging.info(f'Task "{t}" finished in {time.time() - st:.2f} seconds')
    elif task == 'profession_compare':
        task_list = [f'profession_compare_{i}' for i in range(9,len(PROFESSIONS['english']))]
        for t in task_list:
            print(f"\n=== Running task: {t} ===")
            st = time.time()
            main(task=t, **kwargs)
            logging.info(f'Task "{t}" finished in {time.time() - st:.2f} seconds')
    elif task == 'profession_gender_compare':
        task_list = [f'profession_gender_compare_{i}' for i in range(9,len(PROFESSIONS_GENDER['english']))]
        for t in task_list:
            print(f"\n=== Running task: {t} ===")
            st = time.time()
            main(task=t, **kwargs)
            logging.info(f'Task "{t}" finished in {time.time() - st:.2f} seconds')
    elif task == 'adjective_compare':
        for adj in ADJECTIVES.keys():
            task_list = [f'adjective_compare_{adj}_{i}' for i in range(len(ADJECTIVES[adj]))]
            for t in task_list:
                print(f"\n=== Running task: {t} for adjective {adj} ===")
                st = time.time()
                main(task=t, **kwargs)
                logging.info(f'Task "{t}" finished in {time.time() - st:.2f} seconds')

    else:
        main(task=task, **kwargs)


if __name__ == "__main__":
    st = time.time()

    fire.Fire(wrapper)
    logging.info(f'Total execution time: {time.time() - st:.2f} seconds')
