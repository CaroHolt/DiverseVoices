from datasets import load_dataset
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, Qwen2AudioForConditionalGeneration, AutoTokenizer, AutoModelForCausalLM#, Qwen2_5OmniModel
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

def load_model(model_name_or_path, cache_dir, load_in_8bit):
    processor = AutoProcessor.from_pretrained(
            model_name_or_path, 
            trust_remote_code=True,
            cache_dir = cache_dir
            )
    if 'Qwen' in model_name_or_path:
        model = Qwen2AudioForConditionalGeneration.from_pretrained(
            model_name_or_path,
            use_safetensors=True,
            trust_remote_code=True,
            cache_dir = cache_dir,
            load_in_8bit=load_in_8bit
        )        
    elif 'Phi' in model_name_or_path:
        model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            trust_remote_code=True,
            torch_dtype='auto',
            _attn_implementation='flash_attention_2',
            cache_dir = cache_dir,
        )
    elif 'MERaLiON' in model_name_or_path:
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_name_or_path,
            use_safetensors=True,
            trust_remote_code=True,
            cache_dir = cache_dir,
            load_in_8bit=load_in_8bit
        )
    elif 'typhoon' in model_name_or_path:    
        model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            cache_dir = cache_dir
        )
    elif 'Step' in model_name_or_path:
        model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
            cache_dir = cache_dir
        )
        tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path, trust_remote_code=True
        )
    else: 
        raise ValueError("No suitable model found")
    
    return model, processor
    

def get_query_list(task, model_name_or_path, processor, batch_size, ds_size):
    query_list = create_prompts(task, 'english', 'audio', ds_size)
    chat_prompts = []
    if 'MERaLiON' in model_name_or_path:
        prompt = "Given the following audio context: <SpeechHere>\n\nText instruction: {query}"

        for query in query_list:
            conversation = [
                {"role": "user", "content": prompt.format(query=query)}
            ]
            # Apply the chat template to create a prompt for the model
            chat_prompt = processor.tokenizer.apply_chat_template(
                conversation=conversation,
                tokenize=False,
                add_generation_prompt=True
            )
            chat_prompts.append(chat_prompt)

    elif 'Phi' in model_name_or_path:
        prompt = "<|audio_1|>{query}"

        for query in query_list:
            conversation = [
                {"role": "user", "content": prompt.format(query=query)}
            ]
            # Apply the chat template to create a prompt for the model
            chat_prompt = processor.tokenizer.apply_chat_template(
                conversation=conversation,
                tokenize=False,
                add_generation_prompt=True
            )
            chat_prompts.append(chat_prompt)

    else:
        for query in query_list:
            conversation = [
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Given the following audio context:"},
                        {"type": "audio", "audio_url": "audio"},
                        {"type": "text", "text": query}
                    ]
                }
            ]

            chat_prompt = processor.apply_chat_template(
                conversation=conversation,
                tokenize=False,
                add_generation_prompt=True
            )
            chat_prompts.append(chat_prompt)
    return chat_prompts

def read_audio_file(model_name_or_path, file_path, processor):

    if 'Phi' in model_name_or_path:

        audio_array = sf.read(file_path)
    
    else:
        audio_array, sr = librosa.load(file_path, sr=processor.feature_extractor.sampling_rate)  

    return audio_array

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



def get_audio_data(experiment, processor, model_name_or_path):
    audio_arrays = []

    df = get_dataset(experiment)

    for index, row in tqdm(df.iterrows()):
        
        if 'african_dialects' in experiment:
            file_path =  storage_path + 'audio_african_dialects/' + row['Spkr'] + '_segment_' + str(row['segment'])  + '.wav'
        elif experiment == 'english_accents':
            file_path =  storage_path + 'recordings/' + row['filename'] + '.mp3'
        elif 'british_dialects' in experiment:
            #file_path =  storage_path + 'british_dialects_audio/' + experiment +'/'+ row['audio_file'] + '.wav'
            file_path = row['audio_file']

        elif 'synthetic' in experiment:
            file_path =  storage_path + 'synthetic_audio/' + row['audio_file']

        audio_array = read_audio_file(model_name_or_path, file_path, processor)
            
        audio_arrays.append(audio_array)

    return audio_arrays


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

        model, processor = load_model(model_name_or_path, cache_dir, load_in_8bit)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if not load_in_8bit:
            model.to(device)


        audio_arrays = get_audio_data(experiment, processor, model_name_or_path)

        if sample_size >0:
            audio_arrays = audio_arrays[:sample_size]

        chat_prompts = get_query_list(task, model_name_or_path, processor, batch_size, len(audio_arrays))

        print(len(chat_prompts))
        print(len(audio_arrays))


        results = []

        for i in tqdm(range(0, len(audio_arrays), batch_size)):
            audio_batch = audio_arrays[i:i + batch_size]
            text_batch = chat_prompts[i:i + batch_size]


            if 'Qwen' in model_name_or_path:
                inputs = processor(text=text_batch, audios=audio_batch, padding=True, return_tensors="pt").to(device)
            elif 'MERaLiON' in model_name_or_path:
                inputs = processor(text=text_batch, audios=audio_batch).to(device)
            else:
                inputs = processor(text=text_batch, audios=audio_batch, return_tensors="pt").to(device)
            

            inputs['input_ids'] = inputs['input_ids'].to(device)
            if 'Phi' in model_name_or_path:
                with torch.no_grad():
                    outputs = model.generate(**inputs, 
                                            max_new_tokens=seq_length, 
                                            do_sample=True, 
                                            temperature=0.1, 
                                            top_p=0.9, 
                                            top_k=100,
                                            num_logits_to_keep=1)
            else:
                with torch.no_grad():
                    outputs = model.generate(**inputs, 
                                            max_new_tokens=seq_length, 
                                            do_sample=True, 
                                            temperature=0.1, 
                                            top_p=0.9, 
                                            top_k=100,
                                            )
            generated_ids = outputs[:, inputs['input_ids'].size(1):]
            responses = processor.batch_decode(generated_ids, skip_special_tokens=True)#[0]
            results.extend(responses)

        output_path = storage_path + 'output/' + experiment + '/'
        if not os.path.exists(output_path):
            os.makedirs(output_path)


        if sample_size > 0:
            print(results)
        else: 
            output_file = output_path + str(model_name_or_path.split('/')[1]) + '.csv'
            if os.path.exists(output_file):
                df = pd.read_csv(output_file)

            if 'african_dialects' in experiment:
                start_df = pd.read_csv('/work/bbc6523/diverse_voices/full_text_african_dialects.csv')
                component = experiment.replace('african_dialects_', '')
                start_df = start_df[(start_df['content_token_length'] > 10) & (start_df['CORAAL Component'] == component)]
                df = pd.DataFrame({
                    'Spkr': start_df['Spkr'].tolist(),
                    'segment': start_df['segment'].tolist()
                })
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
        task_list = [f'profession_compare_{i}' for i in range(42, len(PROFESSIONS['english']))]
        for t in task_list:
            print(f"\n=== Running task: {t} ===")
            st = time.time()
            main(task=t, **kwargs)
            logging.info(f'Task "{t}" finished in {time.time() - st:.2f} seconds')
    elif task == 'profession_gender_compare':
        task_list = [f'profession_gender_compare_{i}' for i in range(len(PROFESSIONS_GENDER['english']))]
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
