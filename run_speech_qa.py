from datasets import load_dataset
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, Qwen2AudioForConditionalGeneration, AutoModel
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
    elif 'typhoon' in model_name_or_path:
        model = AutoModel.from_pretrained(
            model_name_or_path,
            use_safetensors=True,
            trust_remote_code=True,
            cache_dir = cache_dir
        )  
    elif 'MERaLiON' in model_name_or_path:
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_name_or_path,
            use_safetensors=True,
            trust_remote_code=True,
            cache_dir = cache_dir,
            load_in_8bit=load_in_8bit
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

def get_audio_data(experiment, processor, cache_dir):
    audio_arrays = []

    if 'african_dialects' in experiment:
        df = pd.read_csv('/work/bbc6523/diverse_voices/full_text_african_dialects.csv')
        component = experiment.replace('african_dialects_', '')
        df = df[(df['content_token_length'] > 10) & (df['CORAAL Component'] == component)]

        for index, row in tqdm(df.iterrows()):

            file_path =  '/work/bbc6523/diverse_voices/audio_african_dialects/' + row['Spkr'] + '_segment_' + str(row['segment'])  + '.wav'

            audio_array, sr = librosa.load(file_path, sr=processor.feature_extractor.sampling_rate)  # e.g., load and resample to 16kHz
            audio_arrays.append(audio_array)

    elif experiment == 'english_accents':
        df = pd.read_csv('english_accents.csv')

        for index, row in tqdm(df.iterrows()):

            file_path =  '/work/bbc6523/diverse_voices/recordings/' + row['filename'] + '.mp3'

            audio_array, sr = librosa.load(file_path, sr=processor.feature_extractor.sampling_rate)  # e.g., load and resample to 16kHz
            audio_arrays.append(audio_array)

    elif 'british_dialects' in experiment:
        df = pd.read_pickle(f"/work/bbc6523/diverse_voices/audio_british_dialects/{experiment}.pkl")
        audio_arrays = df['audio_array'].tolist()

    elif experiment == 'synthetic_data':
        print('synthetic')
        df = pd.read_csv('synthetic_data.csv')

        for index, row in tqdm(df.iterrows()):

            file_path =  'synthetic_audio/' + row['audio_file']

            audio_array, sr = librosa.load(file_path, sr=processor.feature_extractor.sampling_rate)  # e.g., load and resample to 16kHz
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

        model, processor = load_model(model_name_or_path, cache_dir, load_in_8bit)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if not load_in_8bit:
            model.to(device)


        audio_arrays = get_audio_data(experiment, processor, cache_dir)

        if sample_size >0:
            audio_arrays = audio_arrays[:sample_size]

        chat_prompts = get_query_list(task, model_name_or_path, processor, batch_size, len(audio_arrays))

        


        results = []

        for i in tqdm(range(0, len(audio_arrays), batch_size)):
            audio_batch = audio_arrays[i:i + batch_size]
            text_batch = chat_prompts[i:i + batch_size]

            if 'MERaLiON' in model_name_or_path:
                inputs = processor(text=text_batch, audios=audio_batch).to(device)
            else:
                inputs = processor(text=text_batch, audios=audio_batch, padding=True, return_tensors="pt")#.to(device)


            inputs['input_ids'] = inputs['input_ids'].to("cuda")
            with torch.no_grad():
                outputs = model.generate(**inputs, max_new_tokens=seq_length, do_sample=True, temperature=0.7, top_p=0.9, top_k=100)
            generated_ids = outputs[:, inputs['input_ids'].size(1):]
            responses = processor.batch_decode(generated_ids, skip_special_tokens=True)#[0]
            results.extend(responses)


        if sample_size > 0:
            print(results)
        else: 
            if os.path.exists(f"{experiment}.csv"):
                df = pd.read_csv(f'{experiment}.csv')
            else:
                if 'british_dialects' in experiment:
                    start_df = pd.read_pickle(f"{experiment}.pkl")
                    df = pd.DataFrame({
                        'speaker_id': start_df['speaker_id'].tolist()
                    })
                elif 'african_dialects' in experiment:
                    start_df = pd.read_csv('/work/bbc6523/diverse_voices/full_text_african_dialects.csv')
                    component = experiment.replace('african_dialects_', '')
                    start_df = start_df[(start_df['content_token_length'] > 10) & (start_df['CORAAL Component'] == component)]
                    df = pd.DataFrame({
                        'Spkr': start_df['Spkr'].tolist(),
                        'segment': start_df['segment'].tolist()
                    })
            model_name = model_name_or_path.split('/')[1]
            df[f'model_response_{task}_{model_name}'] = results
            df[f'model_prompt_{task}_{model_name}'] = chat_prompts
            df.to_csv(f'{experiment}.csv', index=False)





if __name__ == "__main__":
    st = time.time()
    fire.Fire(main)
    logging.info(f'Total execution time: {time.time() - st:.2f} seconds')
