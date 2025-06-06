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
from run_speech_qa import get_dataset, load_model, storage_path


def get_text_query_list(task, model_name_or_path, processor, batch_size, text_arrays):
    query_list = create_prompts(task, 'english', 'text', len(text_arrays), [])
    chat_prompts = []
    if 'MERaLiON' in model_name_or_path:
        asdsad

    elif 'Phi' in model_name_or_path:
        asdsad

    else:
        for index, query in enumerate(query_list):
            conversation = [
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Given the following text context: "},
                        {"type": "text", "text": text_arrays[index]},
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



def get_text_data(experiment, model_name_or_path):
    text_arrays = []

    df = get_dataset(experiment)

    for index, row in tqdm(df.iterrows()):
        if row["gender"] == "female":
            gender = "Female Person: "
        else:
            gender = "Male Person: " 
        text_arrays.append(gender +  str(row['text']) + "\n\n")

    return text_arrays


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

        model, processor = load_model(model_name_or_path, load_in_8bit)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if not load_in_8bit:
            model.to(device)
        #model, processor = None, None


        text_arrays = get_text_data(experiment, model_name_or_path)

        if sample_size >0:
            text_arrays = text_arrays[:sample_size]

        chat_prompts = get_text_query_list(task, model_name_or_path, processor, batch_size, text_arrays)

        print(len(chat_prompts))
        print("Example chat: '{}'".format(chat_prompts[0]))


        results = []

        for i in tqdm(range(0, len(chat_prompts), batch_size)):
            text_batch = chat_prompts[i:i + batch_size]


            if 'Qwen' in model_name_or_path:
                inputs = processor(text=text_batch, padding=True, return_tensors="pt").to(device)
            elif 'MERaLiON' in model_name_or_path:
                inputs = processor(text=text_batch).to(device)
            else:
                inputs = processor(text=text_batch, return_tensors="pt").to(device)
            

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

        output_path = storage_path + 'output/' + experiment + '_textonly' + '/'
        if not os.path.exists(output_path):
            os.makedirs(output_path)


        if sample_size > 0:
            print(results)
        else: 
            output_file = output_path + str(model_save_path.split('/')[1]) + '.csv'
            print(output_file)
            if os.path.exists(output_file):
                df = pd.read_csv(output_file)
            else:
                df = get_dataset(experiment)

            df[f'model_response_{task}'] = results
            df[f'model_prompt_{task}'] = chat_prompts
            df.to_csv(output_file, index=False)

def wrapper(task='profession_binary', **kwargs):
    if task == "profession_choice_multi":
        task_list = [f'profession_choice_{i}' for i in range(5)]
        for t in task_list:
            print(f"\n=== Running task: {t} ===")
            main(task=t, **kwargs)
    else:
        main(task=task, **kwargs)

if __name__ == "__main__":
    fire.Fire(wrapper)
