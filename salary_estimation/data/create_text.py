import pandas as pd
import os
from transformers import AutoTokenizer, AutoModelForCausalLM



input_dir = "data/wikidir"
output_dir = "data/prompts/text_creation"



def load_model(model_name, gt_file):
    tokenizer = AutoTokenizer.from_pretrained(model_name, padding_side='left')
    if tokenizer.pad_token is None:
        # Option 1: Use eos_token as pad_token
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name, device_map="auto", torch_dtype=torch.bfloat16)
    model.config.pad_token_id = model.config.eos_token_id
    # model, tokenizer = None, None
    return model, tokenizer

def tokenize_data(text):

    prompts_template = []
    prompt_metadata = []
    for _, prompt in enumerate(all_prompts):
        messages = tokenizer.apply_chat_template(
            prompt[0], add_generation_prompt=True, tokenize=False)
        prompts_template.append(messages)
        prompt_metadata.append(prompt[1])
    return prompts_template, prompt_metadata


languages = ["als", "bar", "frr", "ksh", "nds", "pfl", "stq"]
prompt_raw = "Translate the following German dialect text into standard German: '<TEXT>'. Only answer with the standard German version:"

dfs = []
for language in languages:
    file = os.path.join(input_dir, "de." + language, "docs.jsonl")

    df = pd.read_json(file, lines=True)
    df["length"] = df["contents"].apply(lambda x: len(x))
    df = df[(df["length"] > 300) & (df["length"] < 500)]

    df["prompts"] = df.apply(lambda row: prompt_raw.replace("<TEXT>", row["contents"]), axis=1)

    df["language"] = language

    df = df.sample(n=50, random_state=40)  # Set random_state for reproducibility
    print(len(df))
    print(language)
    dfs.append(df)
print(dfs)
df = pd.concat(dfs, ignore_index=True)  # Merge DataFrames correctly
file = os.path.join(output_dir, "raw_text.csv")
df.to_csv(file)



