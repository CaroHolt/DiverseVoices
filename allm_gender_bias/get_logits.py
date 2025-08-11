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
import torch.nn.functional as F
import numpy as np


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

    audio_array, sr = librosa.load(file_path, sr=processor.feature_extractor.sampling_rate)  

    return audio_array

def get_dataset(experiment):

    df = pd.read_csv(storage_path + 'data/' + experiment + '.csv')
    return df



def get_audio_data(experiment, processor, model_name_or_path):
    audio_arrays = []

    if experiment == 'prior':

        for audio in ['silence', 'random_noise']:
            file_path = 'data/audio_files/'+ audio + '.wav'
            audio_array = read_audio_file(model_name_or_path, file_path, processor)
            audio_arrays.append(audio_array)

    else:

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
        print(model_name_or_path)
        if 'Qwen' in model_name_or_path:
            model_save_path = model_name_or_path
            model_name_or_path = '/p/project1/westai0056/code/cache_dir/models--Qwen--Qwen2-Audio-7B-Instruct/snapshots/0a095220c30b7b31434169c3086508ef3ea5bf0a'
        elif 'MERaLiON-AudioLLM-Whisper-SEA-LION' in model_name_or_path:
            model_save_path = model_name_or_path
            model_name_or_path = '/p/project1/westai0056/code/cache_dir/models--MERaLiON--MERaLiON-AudioLLM-Whisper-SEA-LION/snapshots/e6d1803e9391090db5396465bd4712645a117cef'
        elif 'MERaLiON-2-10B' in model_name_or_path:
            model_save_path = model_name_or_path
            model_name_or_path = '/p/project1/westai0056/code/cache_dir/models--MERaLiON--MERaLiON-2-10B/snapshots/31d5b7ac6a88652c934583311c40fa74b80b41ac'

        if experiment == 'prior':
            df = pd.DataFrame(np.nan, index=range(2), columns=["gender"])
        else:
            df = get_dataset(experiment)
            

        model, processor = load_model(model_name_or_path, load_in_8bit)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if not load_in_8bit:
            model.to(device)

        chat_prompts = get_query_list(task, model_name_or_path, processor, df)


        audio_arrays = get_audio_data(experiment, processor, model_name_or_path)
        if 'gender' in task:
            tokens_of_interest = ['male', 'female']# ['1', '2', '3', '4', '5', '6', '7', '8', '9']     
        else:
            tokens_of_interest = [inner_list for sublist in ADJECTIVES_IAT_SINGLETOKEN[task.replace('adjectives_list_iat_logits_', '')[:-8]] for inner_list in sublist]
        tok_ids = [processor.tokenizer.encode(tok, add_special_tokens=False)[0]
                for tok in tokens_of_interest]
        
        batch_size = 1
        if sample_size >0:
            audio_arrays = audio_arrays[:sample_size]
        results = []
        for i in tqdm(range(0, len(audio_arrays), batch_size)):
            
            audio_batch = audio_arrays[i:i + batch_size]
            text_batch = chat_prompts[i:i + batch_size]
            #print('text')
            #print(text_batch)
            #print('audio')
            #print(audio_batch)


            if 'Qwen' in model_name_or_path:
                inputs = processor(text=text_batch, audios=audio_batch, padding=True, return_tensors="pt").to(device)
            elif 'MERaLiON' in model_name_or_path:
                inputs = processor(text=text_batch, audios=audio_batch).to(device)
            else:
                inputs = processor(text=text_batch, audios=audio_batch, return_tensors="pt").to(device)
            

            inputs['input_ids'] = inputs['input_ids'].to(device)


            # Get the raw logits
            with torch.no_grad():
                outputs = model.generate(**inputs, 
                                    max_new_tokens=10, 
                                    return_dict_in_generate=True,  
                                    output_scores=True,            
                                    do_sample=False                
                                    )


            full_response = processor.batch_decode(outputs.sequences, skip_special_tokens=True)
            print('full response')
            print(full_response)

            result_dict = {}
            logits = outputs.scores[0]
            logits_cpu = logits[0].float().cpu()
            probs  = torch.softmax(logits_cpu, dim=-1)
            result_dict = {tok: probs[tid].item()          # <— .item() here
                for tok, tid in zip(tokens_of_interest, tok_ids)}
            results.append(result_dict)
 


            # 5) free GPU memory for this step
            del logits
            torch.cuda.empty_cache()


        output_path = storage_path + 'output/' + experiment + '/'
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        print(results)
        if sample_size > 0:
            print(results)
        else: 
            output_file = output_path + str(model_save_path.split('/')[1]) + '.csv'
            df[f'model_response_logits_{task}'] = results
            if os.path.exists(output_file):
                df_old = pd.read_csv(output_file)
                df = pd.concat([df,df_old])

            
            df.to_csv(output_file, index=False)


def wrapper(task='trait_assignment', prompt_variations=True, **kwargs):
    task_list = [task]
    if task == 'trait_assignment':
        task_list = [f'trait_assignment_{i}' for i in ['confidence']] # TRAIT_LIST.keys()
    elif task == 'adjectives_list_iat_logits':
        task_list = [f'adjectives_list_iat_logits_{i}' for i in ADJECTIVES_IAT_SINGLETOKEN.keys()]


    # Add Prompt Variations
    if prompt_variations:
        task_list = [task + f"_prompt{i}" for task in task_list for i in range(3)]

    for t in task_list:
        print(f"\n=== Running task: {t} ===")
        main(task=t, **kwargs)

if __name__ == "__main__":
    fire.Fire(wrapper)



exit()
for step, logits_gpu in enumerate(outputs.scores):
    
    logits = logits_gpu[0].float().cpu()


    probs  = torch.softmax(logits, dim=-1)


    
    chosen_id   = generated_ids[prompt_len + step].item()
    chosen_tok  = processor.decode([chosen_id])
    print(chosen_tok)
    if 'MERaLiON' in model_name_or_path:
        result_dict = {tok: round(probs[tid].item(), 4)        
            for tok, tid in zip(tokens_of_interest, tok_ids)}
        results.append(result_dict)
        break


    if chosen_tok.lower().strip() in tokens_of_interest:
        result_dict = {tok: round(probs[tid].item(), 4)        
            for tok, tid in zip(tokens_of_interest, tok_ids)}
        results.append(result_dict)
        break