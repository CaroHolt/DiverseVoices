from transformers import AutoTokenizer, AutoModelForCausalLM
import pandas as pd
import librosa
import torch
from tqdm import tqdm
import os
import time 
import fire
import logging
# from prompts_german import *
from allm_gender_bias.prompts import *


def load_model(model_name_or_path, cache_dir, load_in_8bit):
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, padding_side='left')
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token  # Option 1: Use eos_token as pad_token
    model = AutoModelForCausalLM.from_pretrained(model_name_or_path, device_map="auto", torch_dtype=torch.bfloat16, load_in_8bit=load_in_8bit)
    #processor = None
    return model, tokenizer



def get_query_list(task, model_name_or_path, processor, batch_size, text_arrays):

    if "profession_implicit" == task or "profession_implicit_reverse" == task or "profession_explicit" == task:
        ds_size = int(len(text_arrays) / 2)
        base_query = "Given the following text context: \nWriter A: '{}'\nWriter B: '{}'.\n\n{}"
    elif "profession_implicit_explicit" == task:
        ds_size = int(len(text_arrays) / 2)
        base_query = "Given the following two writers: \nWriter A: Speaks in standard German.\nWriter B: Speaks in German dialect.\n\n{}"
    else:
        ds_size = len(text_arrays)
        base_query = "Given the following text context: '{}'.\n\n{}"

    query_list = create_prompts(task, 'german', 'text', ds_size)
    chat_prompts = []
    for index, query in enumerate(query_list):
        text = text_arrays["text"].iloc[index]
        prompts = []

        for single in query:

            if "profession_implicit" == task or "profession_explicit" == task:
                text2 = text_arrays["text"].iloc[index + ds_size]
                content = base_query.format(text, text2, single)
            elif "profession_implicit_reverse" == task:
                text2 = text_arrays["text"].iloc[index + ds_size]
                content = base_query.format(text2, text, single)
            elif "profession_implicit_explicit" == task:
                text2 = text_arrays["text"].iloc[index + ds_size]
                content = base_query.format(single)
            else:
                content = base_query.format(text, single)

            conversation = [
                #{"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": content,
                }
            ]

            chat_prompt = processor.apply_chat_template(
                conversation=conversation,
                tokenize=False,
                add_generation_prompt=True
            )
            prompts.append(chat_prompt)
        
        chat_prompts.append(prompts)

    return chat_prompts, text_arrays[:ds_size]

def get_text_data(experiment, processor, cache_dir):
    text_arrays = []

    # Load data
    df = pd.read_pickle("data/Llama-3.3-70B-Instruct.pkl")
    df["id"] = df.index
    df["answer"] = df.apply(lambda row: row["answer"][0].replace("\n", " "), axis=1)
    df["contents"] = df.apply(lambda row: row["contents"].replace("\n", " "), axis=1)

    df = df.rename(columns={'answer': 'standard_text', "contents": "dialect_text"})
    # Transform the DataFrame
    df = df.melt(id_vars=["id", "language"], 
                            value_vars=["standard_text", "dialect_text"], 
                            var_name="text_type", 
                            value_name="text")

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

        model, processor = load_model(model_name_or_path, cache_dir, load_in_8bit)

        #device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        #if not load_in_8bit:
        #    model.to(device)

        text_arrays = get_text_data(experiment, processor, cache_dir)

        if sample_size >0:
            text_arrays = text_arrays[:sample_size]

        chat_prompts, text_arrays = get_query_list(task, model_name_or_path, processor, batch_size, text_arrays)
        text_arrays["prompts"] = chat_prompts
        text_arrays = text_arrays.explode('prompts')
        chat_prompts = list(text_arrays["prompts"])

        results = []

        for i in tqdm(range(0, len(chat_prompts), batch_size)):
            text_batch = chat_prompts[i:i + batch_size]

            if 'MERaLiON' in model_name_or_path:
                inputs = processor(text=text_batch, audios=audio_batch).to(device)
            else:
                inputs = processor(text=text_batch, padding=True, return_tensors="pt")#.to(device)

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
                df = text_arrays
            model_name = model_name_or_path.split('/')[-1]
            df[f'model_response_{task}_{model_name}'] = results
            #df[f'model_prompt_{task}_{model_name}'] = chat_prompts
            df.to_csv(f'{experiment}.csv', index=False)


if __name__ == "__main__":
    st = time.time()
    fire.Fire(main)
    logging.info(f'Total execution time: {time.time() - st:.2f} seconds')
