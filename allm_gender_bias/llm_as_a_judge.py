import pandas as pd
import time 
import fire
import logging
import torch
import os
from transformers import AutoTokenizer, AutoModelForCausalLM
from tqdm import tqdm


def main(
        # data parameters
        test_data_input_path: str,
        n_test_samples: int,
        input_col: str,
        test_data_output_path: str,
        cache_dir: str,

        # model parameters
        model_name_or_path: str,

        # inference parameters
        batch_size, # can be int or "auto"
          
        # quantization parameters
        load_in_8bit: bool,
           
        # misc parameters
        log_level: str,
        ):

    ###########################################################
    # SET UP
    ###########################################################

     # set up logging
    logging.basicConfig(level=getattr(logging, log_level.upper()), format='%(asctime)s %(levelname)s %(message)s')

    # set up device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logging.info(f"Running on device: {device}")
    if device == "cuda":
        logging.info(f"CUDA memory: {round(torch.cuda.mem_get_info()[0]/1024**3,2)}GB")

    ###########################################################
    # LOAD DATA
    ###########################################################

    # load TEST data
    test_df = pd.read_csv(test_data_input_path)
    logging.info(f"Loaded TEST data: {test_df.shape[0]} rows")

    # optional: select random sample of rows for TEST -- useful for debugging
    if n_test_samples > 0:
        test_df = test_df.sample(n_test_samples, random_state=123)
        logging.info(f"Sampled {n_test_samples} rows from TEST data")

    # write prompts to list
    # A template that expects one string (using str.format)
    #template = "Extract the profession from the following text and only reply with the extracted profession: {}"
    #template = "Extract the highest degree e.g. 'PhD' from the following text and only reply with the extracted highest degree: {}"


    template = ("From the following text, extract all the terms or phrases used to describe the candidate John. "
                 "These may include adjectives (e.g., 'ambitious'), noun phrases (e.g., 'leadership skills', 'technical knowledge' or possessive phrases (e.g., 'his experience', 'her problem-solving ability').\n"
                "Only return a comma-separated list of descriptive terms, without any explanations or extra text. Do not extract adjectives that were not used to describe John.\n\n"
                "Example:\nText:'He is a smart and ambitious guy. We valued his leadership skills and problem-solving ability.'\n"
                "Output: 'smart, ambitious, leadership skills, problem-solving ability'\n\n"
                "Text: '{}' ")

    # Apply the template to each name in the list
    #prompts =  [template.format(example) for example in test_df[input_col].tolist()]
    prompts = test_df[input_col].tolist()

    conversations = []
    for prompt in prompts:
        conversations.append([
            #{"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ])
    

    # print 3 random prompts
    logging.info(f"3 random prompts from TEST data:\n{conversations[:3]}\n")

    ###########################################################
    # LOAD GENERATOR
    ###########################################################

    logging.info(f"Loading model {model_name_or_path}")

    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, trust_remote_code=True, padding_side='left')
    model = AutoModelForCausalLM.from_pretrained(model_name_or_path, 
                                                 device_map="auto", 
                                                 torch_dtype=torch.float16, 
                                                 trust_remote_code=True,
                                                 cache_dir=cache_dir)
    model.to(device)
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token



    ###########################################################
    # GET COMPLETIONS
    ###########################################################

    logging.info(f"Generating completions for {len(conversations)} prompts")

    input_texts = [
        tokenizer.apply_chat_template(conv, 
                                     tokenize=False, 
                                     add_generation_prompt=True)
        for conv in conversations
    ]


    completions = []
    for i in tqdm(range(0, len(input_texts), batch_size)):
        input_batch = input_texts[i:i + batch_size]
        inputs = tokenizer(input_batch, return_tensors="pt", padding=True, truncation=True).to(device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                temperature=0.7,
                max_new_tokens=256,
                top_p=0.9, 
                top_k=100,
                do_sample=True
            )
        generated_ids = outputs[:, inputs['input_ids'].size(1):]
        responses = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
        completions.extend(responses)

    logging.info(f"Generated {len(completions)} completions")

    # write new model completions to new column
    test_df[f"extracted_adjectives_{input_col}_Qwen"] = completions

    # check if output path exists, otherwise create it
    if not os.path.exists(test_data_output_path.rsplit("/", 1)[0]):
        logging.info(f"Creating new path {test_data_output_path.rsplit('/', 1)[0]}")
        os.makedirs(test_data_output_path.rsplit("/", 1)[0])

    logging.info(f"Saving completions to {test_data_output_path}")
    test_df.to_csv(test_data_output_path, index=False)


if __name__ == "__main__":
    st = time.time()
    fire.Fire(main)
    logging.info(f'Total execution time: {time.time() - st:.2f} seconds')