from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoModel, AutoModelForSpeechSeq2Seq, AutoProcessor, Qwen2AudioForConditionalGeneration, AutoTokenizer, AutoModelForCausalLM#, Qwen2_5OmniModel
import pandas as pd
import librosa
import torch
from tqdm import tqdm
import os
import fire
import logging
import soundfile as sf
from prompts import *
from ast import literal_eval

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


storage_path = '/p/project1/westai0056/code/DiverseVoices/allm_gender_bias/'

def load_model(model_name_or_path, load_in_8bit):
    processor = AutoProcessor.from_pretrained(
            model_name_or_path, 
            trust_remote_code=True,
            )
    print(model_name_or_path)
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


def get_dataset(experiment):

    df = pd.read_csv(storage_path + 'data/' + experiment + '.csv')
    return df


def read_audio_file(model_name_or_path, file_path, processor):

    audio_array, sr = librosa.load(file_path, sr=processor.feature_extractor.sampling_rate)  

    return audio_array


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
        experiment: str,

        # model parameters
        model_name_or_path: str,
          
        # quantization parameters
        load_in_8bit: bool,
           
        sample_size:int,

        example_text: bool,

        example_audio: bool

        ):
        if 'Qwen' in model_name_or_path:
            model_save_path = model_name_or_path
            model_name_or_path = '/p/project1/westai0056/code/cache_dir/models--Qwen--Qwen2-Audio-7B-Instruct/snapshots/0a095220c30b7b31434169c3086508ef3ea5bf0a'
        elif 'MERaLiON-AudioLLM-Whisper-SEA-LION' in model_name_or_path:
            model_save_path = model_name_or_path
            model_name_or_path = '/p/project1/westai0056/code/cache_dir/models--MERaLiON--MERaLiON-AudioLLM-Whisper-SEA-LION/snapshots/e6d1803e9391090db5396465bd4712645a117cef'
        elif 'MERaLiON-2-10B' in model_name_or_path:
            model_save_path = model_name_or_path
            model_name_or_path = '/p/project1/westai0056/code/cache_dir/models--MERaLiON--MERaLiON-2-10B/snapshots/31d5b7ac6a88652c934583311c40fa74b80b41ac'

        

        model, processor = load_model(model_name_or_path, load_in_8bit)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if not load_in_8bit:
            model.to(device)


        if example_audio:
            df = get_dataset(experiment)


            audio_arrays = get_audio_data(experiment, processor, model_name_or_path)

            if sample_size >0:
                audio_arrays = audio_arrays[:sample_size]
            

            results = []

            for audio in tqdm(audio_arrays):
                if 'Qwen' in model_name_or_path:
                    inputs = processor(text = ['<|AUDIO|>'],
                                    sampling_rate=16_000,
                                        audios=audio,                             
                                    return_tensors="pt").to(device)
                elif 'MERaLiON' in model_name_or_path:
                    inputs = processor(text=["<SpeechHere>"],          # <—— correct placeholder
                                        audios=audio,                 # list, even length 1
                                        sampling_rate=16_000,
                                    ).to(device)
                else:
                    inputs = processor(audios=audio, return_tensors="pt").to(device)
                


                with torch.inference_mode():
                    outputs = model(**inputs, 
                                    output_hidden_states=True)

                audio_hidden = outputs.hidden_states[-1]
                audio_embed  = audio_hidden.mean(dim=1).squeeze().cpu().tolist()    
                results.append(audio_embed)

            output_path = storage_path + 'output/' + experiment + '/embeddings'
            if not os.path.exists(output_path):
                os.makedirs(output_path)


            if sample_size > 0:
                print('done')
                print(results)
            else: 
                output_file = output_path + str(model_save_path.split('/')[1]) + '.csv'
                print(output_file)
                if os.path.exists(output_file):
                    df = pd.read_csv(output_file)
                df = df[['audio_file', 'gender']].copy()
                df[f'model_audio_embeddings'] = results
                df.to_csv(f'output/{experiment}/embeddings/' + str(model_save_path.split('/')[1]) + '.csv', index=False)


        elif example_text:
            print('***************** Embeddings for text ********************')
            term_file = '/p/project1/westai0056/code/DiverseVoices/allm_gender_bias/output/embeddings/adjective_list.csv'
            df = pd.read_csv(term_file)

            term_results = []
            for text in df['Term'].tolist():

                text_inputs = processor.tokenizer(
                    text=text,
                    return_tensors="pt"
                ).to(device)

                with torch.inference_mode():
                    out_text = model(**text_inputs, output_hidden_states=True)

                text_hidden = out_text.hidden_states[-1]                # (B, L, D)
                text_embed  = text_hidden.mean(dim=1).squeeze().cpu().tolist()    
                term_results.append(text_embed)

            df['text_embeddings_' + str(model_save_path.split('/')[1])] = term_results

            df.to_csv(term_file, index=False)
            
        else: 
            print('***************** Analyze cosine ********************')
            df = pd.read_csv(f'output/{experiment}/embeddings/' + str(model_save_path.split('/')[1]) + '.csv')

            term_file = '/p/project1/westai0056/code/DiverseVoices/allm_gender_bias/output/embeddings/adjective_list.csv'
            df_terms = pd.read_csv(term_file)

            for term in tqdm(df_terms['Term'].tolist()):
                term_emb = df_terms[df_terms['Term'] == term]['text_embeddings_' + str(model_save_path.split('/')[1])].iloc[0]
                term_emb = literal_eval(term_emb)
                sim_list = []
                for emb in df[f'model_audio_embeddings'].tolist():
                    audio_emb = literal_eval(emb)
                    # Word embeddings for two words
                    word1_embedding = np.array(term_emb)
                    word2_embedding = np.array(audio_emb)
                    # Reshape the arrays to match the expected input shape of cosine_similarity
                    word1_embedding = word1_embedding.reshape(1, -1)
                    word2_embedding = word2_embedding.reshape(1, -1)
                    # Calculate cosine similarity
                    similarity = cosine_similarity(word1_embedding, word2_embedding)[0][0]
                    sim_list.append(similarity)
                                
                df['cosine_sims_' + term] = sim_list
            

            df.to_csv(f'output/{experiment}/embeddings/' + str(model_save_path.split('/')[1]) + '.csv', index=False)



if __name__ == "__main__":
    fire.Fire(main)