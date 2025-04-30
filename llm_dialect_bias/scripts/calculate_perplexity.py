from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
import evaluate
from evaluate import logging
import pandas as pd
from argparse import ArgumentParser
import torch
from torch.nn import CrossEntropyLoss
import datasets
import numpy as np



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



model = model.to(device)

add_start_token=False

batch_size = args.batch_size

max_length = None

predictions = input_texts

# if batch_size > 1 (which generally leads to padding being required), and
# if there is not an already assigned pad_token, assign an existing
# special token to also be the padding token
if tokenizer.pad_token is None and batch_size > 1:
    existing_special_tokens = list(tokenizer.special_tokens_map_extended.values())
    # check that the model already has at least one special token defined
    assert (
        len(existing_special_tokens) > 0
    ), "If batch_size > 1, model must have at least one special token to use for padding. Please use a different model or set batch_size=1."
    # assign one of the special tokens to also be the pad token
    tokenizer.add_special_tokens({"pad_token": existing_special_tokens[0]})


max_tokenized_len = max_length

encodings = tokenizer(
    predictions,
    add_special_tokens=False,
    padding=True,
    truncation=True if max_tokenized_len else False,
    max_length=max_tokenized_len,
    return_tensors="pt",
    return_attention_mask=True,
).to(device)

encoded_texts = encodings["input_ids"]
attn_masks = encodings["attention_mask"]

ppls = []
loss_fct = CrossEntropyLoss(reduction="none")

for start_index in logging.tqdm(range(0, len(encoded_texts), batch_size)):
    end_index = min(start_index + batch_size, len(encoded_texts))
    encoded_batch = encoded_texts[start_index:end_index]
    attn_mask = attn_masks[start_index:end_index]

    if add_start_token:
        bos_tokens_tensor = torch.tensor([[tokenizer.bos_token_id]] * encoded_batch.size(dim=0)).to(device)
        encoded_batch = torch.cat([bos_tokens_tensor, encoded_batch], dim=1)
        attn_mask = torch.cat(
            [torch.ones(bos_tokens_tensor.size(), dtype=torch.int64).to(device), attn_mask], dim=1
        )

    labels = encoded_batch

    with torch.no_grad():
        out_logits = model(encoded_batch, attention_mask=attn_mask).logits

    shift_logits = out_logits[..., :-1, :].contiguous()
    shift_labels = labels[..., 1:].contiguous()
    shift_attention_mask_batch = attn_mask[..., 1:].contiguous()

    perplexity_batch = torch.exp(
        (loss_fct(shift_logits.transpose(1, 2), shift_labels) * shift_attention_mask_batch).sum(1)
        / shift_attention_mask_batch.sum(1)
    )

    ppls += perplexity_batch.tolist()



df[new_col_name] = ppls


df.to_csv(args.input_path, index=False)


