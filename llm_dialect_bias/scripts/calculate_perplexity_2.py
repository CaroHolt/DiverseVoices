from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed, Gemma3ForConditionalGeneration
import evaluate
from evaluate import logging
import pandas as pd
from argparse import ArgumentParser
import torch
from torch.nn import CrossEntropyLoss
import datasets
import numpy as np
from tqdm import tqdm


parser = ArgumentParser(description='Arguments for training')
parser.add_argument('--input_path', type=str, help='dataset name')
parser.add_argument('--input_col', type=str, help='col name')
parser.add_argument('--model_name', type=str, help='Model name', default="models/flan_base_0/")
parser.add_argument('--cache_dir', type=str, help='Cache directory', default="/work/bbc6523/")
parser.add_argument('--seed', type=int, help='Random seed to set', default=10)
parser.add_argument('--batch_size', type=int, help='Batch size to choose', default=16)
args = parser.parse_args()

device = 'cuda'

torch.cuda.empty_cache()

set_seed(args.seed)


if "gemma" in args.model_name:
    print('HELLO')
    model = Gemma3ForConditionalGeneration.from_pretrained(args.model_name, 
                                                            device_map="auto", 
                                                            torch_dtype=torch.float16).eval()
    
else: 
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        cache_dir=args.cache_dir,
        torch_dtype=torch.float16,
        device_map='auto'
    )


print("Model loaded")

tokenizer = AutoTokenizer.from_pretrained(args.model_name,
    cache_dir=args.cache_dir)

df = pd.read_csv(args.input_path)



new_col_name = 'ppl_' + args.input_col + '_' + args.model_name 

print(new_col_name)


input_texts = df[args.input_col].tolist()


# Assign the EOS token as the padding token
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

def calculate_batch_perplexity(input_texts):
    """
    Calculate perplexity for a batch of input texts using a pretrained language model.

    Args:
    - input_texts (List[str]): A list of input texts to evaluate.

    Returns:
    - List[float]: A list of perplexity scores, one for each input text.
    """
    full_perplexities = []
    for i in tqdm(range(0, len(input_texts), args.batch_size)):
        input_batch =  input_texts[i:i + args.batch_size]
        # Tokenize the batch of texts with padding for uniform length
        inputs = tokenizer(
            input_batch, return_tensors="pt", padding=True, truncation=True
        ).to(device)

        input_ids = inputs["input_ids"]
        attention_mask = inputs["attention_mask"]

        # Pass the input batch through the model to get logits
        with torch.no_grad():
            outputs = model(input_ids, attention_mask=attention_mask)
            logits = outputs.logits

        # Shift the logits and input_ids to align targets correctly
        # Logits dimensions are: (batch_size, seq_length, vocab_size) 
        shift_logits = logits[:, :-1, :]  # Ignore the last token's logits
        shift_labels = input_ids[:, 1:]   # Skip the first token in the labels

        # Compute log probabilities
        log_probs = torch.nn.functional.log_softmax(shift_logits, dim=-1)

        # Gather the log probabilities for the correct tokens
        target_log_probs = log_probs.gather(dim=-1, index=shift_labels.unsqueeze(-1)).squeeze(-1)

        # Mask out positions corresponding to padding tokens
        target_log_probs = target_log_probs * attention_mask[:, 1:].to(log_probs.dtype)

        # Compute the mean negative log-likelihood for each sequence
        negative_log_likelihood = -target_log_probs.sum(dim=-1) / attention_mask[:, 1:].sum(dim=-1)

        # Compute perplexity for each sequence
        perplexities = torch.exp(negative_log_likelihood)
        perplexities = perplexities.tolist()
        full_perplexities.extend(perplexities)

    return full_perplexities


df[new_col_name] = calculate_batch_perplexity(input_texts)


df.to_csv(args.input_path, index=False)


