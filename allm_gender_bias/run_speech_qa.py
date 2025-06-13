from datasets import load_dataset
from transformers import AutoModel, AutoModelForSpeechSeq2Seq, AutoProcessor, Qwen2AudioForConditionalGeneration, AutoTokenizer, AutoModelForCausalLM#, Qwen2_5OmniModel
import pandas as pd
import librosa
import torch
from tqdm import tqdm
import os
import fire
import logging
import soundfile as sf
from prompts import *


storage_path = '/p/project1/westai0056/code/DiverseVoices/allm_gender_bias/'

def load_model(model_name_or_path, load_in_8bit):
    processor = AutoProcessor.from_pretrained(
            model_name_or_path, 
            trust_remote_code=True,
            )
    if 'Qwen' in model_name_or_path:
        model = Qwen2AudioForConditionalGeneration.from_pretrained(
            model_name_or_path,
            use_safetensors=True,
            trust_remote_code=True,
            load_in_8bit=load_in_8bit
        )        
    elif 'Phi' in model_name_or_path:
        model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            trust_remote_code=True,
            torch_dtype='auto',
            _attn_implementation='flash_attention_2',
        )
    elif 'MERaLiON' in model_name_or_path:
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_name_or_path,
            use_safetensors=True,
            trust_remote_code=True,
            load_in_8bit=load_in_8bit
        )
    else: 
        raise ValueError("No suitable model found")
    
    return model, processor
    

def get_query_list(task, model_name_or_path, processor, df):
    query_list = create_prompts(task, 'english', 'audio', len(df), df['gender'].tolist())
    chat_prompts = []
    print(model_name_or_path)
    print('CREATE PROMPTS')
    if 'MERaLiON-AudioLLM' in model_name_or_path:
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
    elif 'MERaLiON-2-10B' in model_name_or_path:
        prompt = "Instruction: {query} \nFollow the text instruction based on the following audio: <SpeechHere>"

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

    df = pd.read_csv(storage_path + 'data/' + experiment + '.csv')
    return df



def get_audio_data(experiment, processor, model_name_or_path):
    audio_arrays = []

    df = get_dataset(experiment)

    for index, row in tqdm(df.iterrows()):
        
        file_path = row['audio_file']

        audio_array = read_audio_file(model_name_or_path, file_path, processor)
            
        audio_arrays.append(audio_array)

    return audio_arrays


def main(
        # data parameters
        task: str,
        experiment: str,

        # model parameters
        model_name_or_path: str,
          
        # quantization parameters
        load_in_8bit: bool,
           
        # misc parameters
        log_level: str,

        sample_size:int,

        batch_size:int,
        seq_length:int
        ):
        if 'Qwen' in model_name_or_path:
            model_save_path = model_name_or_path
            model_name_or_path = '/p/project1/westai0056/code/cache_dir/models--Qwen--Qwen2-Audio-7B-Instruct/snapshots/0a095220c30b7b31434169c3086508ef3ea5bf0a'
        if 'MERaLiON-AudioLLM-Whisper-SEA-LION' in model_name_or_path:
            model_save_path = model_name_or_path
            model_name_or_path = '/p/project1/westai0056/code/cache_dir/models--MERaLiON--MERaLiON-AudioLLM-Whisper-SEA-LION/snapshots/e6d1803e9391090db5396465bd4712645a117cef'
        if 'MERaLiON-2-10B' in model_name_or_path:
            model_save_path = model_name_or_path
            model_name_or_path = '/p/project1/westai0056/code/cache_dir/models--MERaLiON--MERaLiON-2-10B/snapshots/31d5b7ac6a88652c934583311c40fa74b80b41ac'

        df = get_dataset(experiment)

        model, processor = load_model(model_name_or_path, load_in_8bit)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if not load_in_8bit:
            model.to(device)


        audio_arrays = get_audio_data(experiment, processor, model_name_or_path)

        if sample_size >0:
            audio_arrays = audio_arrays[:sample_size]

        chat_prompts = get_query_list(task, model_name_or_path, processor, df)

        print(chat_prompts[0])
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
                                            do_sample=False, 
                                            #do_sample=True, 
                                            #temperature=0.1, 
                                            #top_p=0.9, 
                                            #top_k=100,
                                            num_logits_to_keep=1)
            else:
                with torch.no_grad():
                    outputs = model.generate(**inputs, 
                                            max_new_tokens=seq_length, 
                                            do_sample=False,
                                            #do_sample=True, 
                                            #temperature=0.1, 
                                            #top_p=0.9, 
                                            #top_k=100,
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
            output_file = output_path + str(model_save_path.split('/')[1]) + '.csv'
            print(output_file)
            if os.path.exists(output_file):
                df = pd.read_csv(output_file)

            df[f'model_response_{task}'] = results
            df[f'model_prompt_{task}'] = chat_prompts
            df.to_csv(output_file, index=False)


def wrapper(task='profession_binary', **kwargs):
    if task == 'profession_binary':
        task_list = [f'profession_binary_{i}' for i in range(22)]
        for t in task_list:
            print(f"\n=== Running task: {t} ===")
            main(task=t, **kwargs)
    elif task == 'adjectives_iat':
        task_list = [f'adjectives_iat_{i}' for i in ADJECTIVES_IAT.keys()]
        for t in task_list:
            print(f"\n=== Running task: {t} ===")
            main(task=t, **kwargs)
    elif task == 'profession_compare':
        task_list = [f'profession_compare_{i}' for i in range(len(PROFESSIONS['english']))]
        for t in task_list:
            print(f"\n=== Running task: {t} ===")
            main(task=t, **kwargs)
    elif task == 'profession_gender_compare':
        task_list = [f'profession_gender_compare_{i}' for i in range(len(PROFESSIONS_GENDER['english']))]
        for t in task_list:
            print(f"\n=== Running task: {t} ===")
            main(task=t, **kwargs)
    elif task == 'adjective_compare':
        for adj in ADJECTIVES.keys():
            task_list = [f'adjective_compare_{adj}_{i}' for i in range(len(ADJECTIVES[adj]))]
            for t in task_list:
                print(f"\n=== Running task: {t} for adjective {adj} ===")
                main(task=t, **kwargs)

    # ---
    elif task == 'profession_salary':
        task_list = [f'profession_salary_{i}' for i in PROFESSIONS_SUBSET['english']]
        for t in task_list:
            print(f"\n=== Running task: {t} ===")
            main(task=t, **kwargs)
    elif task == 'profession_salary_bio':
        task_list = [f'profession_salary_bio_{i}' for i in PROFESSIONS_SUBSET['english']]
        for t in task_list:
            print(f"\n=== Running task: {t} ===")
            main(task=t, **kwargs)
    elif task == 'profession_salary_bio_wo_profession':
        task_list = [f'profession_salary_bio_wo_profession']
        for t in task_list:
            print(f"\n=== Running task: {t} ===")
            main(task=t, **kwargs)
    elif task == "profession_choice_multi":
        task_list = [f'profession_choice_{i}' for i in range(5)]
        for t in task_list:
            print(f"\n=== Running task: {t} ===")
            main(task=t, **kwargs)
    elif task == "profession_binary_category":
        task_list = [f'profession_binary_category_{category}' for category in PROFESSION_BINARY_CATEGORY.keys()]
        for t in task_list:
            print(f"\n=== Running task: {t} ===")
            main(task=t, **kwargs)

    else:
        main(task=task, **kwargs)


if __name__ == "__main__":
    fire.Fire(wrapper)
