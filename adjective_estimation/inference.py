from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import pandas as pd
import argparse
from prompts import set_prompts
from tqdm import tqdm
import os
import torch.nn.functional as F
from collections import defaultdict

DEVICE = "cuda"

LANGUAGES = ["german", "german_dia"]


from transformers import LogitsProcessor, LogitsProcessorList, AutoModelForCausalLM, AutoTokenizer
import torch



def load_model(model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name, padding_side='left')
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token  # Option 1: Use eos_token as pad_token
    
    model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", torch_dtype=torch.bfloat16)
    model.config.pad_token_id = model.config.eos_token_id
    """
    class AllowListLogitsProcessor(LogitsProcessor):
        def __init__(self, allowed_token_ids):
            self.allowed_token_ids = set(allowed_token_ids)

        def __call__(self, input_ids, scores):
            # Set scores to -inf for disallowed tokens
            mask = torch.ones_like(scores, dtype=torch.bool)
            mask[:, list(self.allowed_token_ids)] = False
            scores = scores.masked_fill(mask, float("-inf"))
            return scores

    # Define allowed token ids
    allowed_tokens = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "€"]
    allowed_token_ids = tokenizer.convert_tokens_to_ids(allowed_tokens)
    # Remove Non
    allowed_token_ids = [token for token in allowed_token_ids if token is not None] + [tokenizer.eos_token_id]
    print(allowed_token_ids)
    # Use the custom logits processor
    logits_processor = LogitsProcessorList([AllowListLogitsProcessor(allowed_token_ids)])
    """
    logits_processor = None
    return model, tokenizer, logits_processor


def tokenize_data(tokenizer):

    PROMPTS, TEXTS, SYSTEM_PROMPT = set_prompts()
    all_prompts = []
    for index, prompt in enumerate(PROMPTS):
        for language in LANGUAGES:
            for text in TEXTS[language]:
                prompt_original = prompt.format(text)
                all_prompts.append([prompt_original, [language, prompt]])

    prompts_template = []
    prompt_metadata = []
    for id_prompt, prompt in enumerate(all_prompts):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt[0]},
        ]
        messages = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        prompts_template.append(messages)
        prompt_metadata.append(prompt[1])

    return prompts_template, prompt_metadata


def get_prob_label(model, input_ids, prompt_length, word_prob=None, mode="multi"):
    # Get model outputs
    with torch.no_grad():
        outputs = model(input_ids)

    # Extract logits for the label tokens
    logits = outputs.logits[0, prompt_length - 1:-1]  # Skip prompt logits
    label_tokens = input_ids[0, prompt_length:]  # Tokens of the label

    # Compute token probabilities
    probs = torch.softmax(logits, dim=-1)
    if mode == "single":
        token_probs = probs[0, label_tokens[0]]
    else:
        token_probs = probs[range(len(label_tokens)), label_tokens]
    
    raw_likelihood = torch.prod(token_probs).item()
    
    if word_prob is not None:
        # print(1 / word_prob)
        # normalized_likelihood = raw_likelihood ** (1 / word_prob)
        normalized_likelihood = raw_likelihood / word_prob
    else:
        normalized_likelihood = None
    return raw_likelihood, normalized_likelihood


def compute_label_likelihood(model, tokenizer, prompts, meta_data, words, normalized_prob):
    """Compute the likelihood of each multi-token label given the prompt."""
    
    results = {}
    # For now without batching
    for prompt, all_meta_sample in zip(prompts, meta_data):
        meta_sample = all_meta_sample[1]

        # Tokenize the prompt
        prompt_ids = tokenizer(prompt, return_tensors="pt", add_special_tokens=True)["input_ids"]
        prompt_length = prompt_ids.size(1)

        raw_likelihoods = {}
        normalized_likelihoods = {}

        # Iterate through all words (possible labels)
        for label in words:
            
            # Tokenize the label (disable adding special tokens again)
            label_ids = tokenizer(label, return_tensors="pt", add_special_tokens=False)["input_ids"]

            input_ids = torch.cat([prompt_ids, label_ids], dim=-1).to("cuda")

            # decoded_outputs = [tokenizer.decode(input_ids[0], skip_special_tokens=False)]

            raw_likelihood, normalized_likelihood = get_prob_label(model, input_ids, prompt_length, normalized_prob[label + "_" + meta_sample])

            raw_likelihoods[label.strip()] = raw_likelihood
            normalized_likelihoods[label.strip()] = normalized_likelihood

        # Normalize raw probabilites (so that they sum 1)
        total_norm = sum(raw_likelihoods.values())
        raw_likelihoods = {label: prob / total_norm for label, prob in raw_likelihoods.items()}

        # Normalize normalized probabilites (so that they sum 1)
        total_raw = sum(normalized_likelihoods.values())

        normalized_likelihoods = {label: prob / total_raw for label, prob in normalized_likelihoods.items()}

        # Sort the normalized_likelihoods dictionary by values in descending order
        sorted_likelihoods = sorted(normalized_likelihoods.items(), key=lambda x: x[1], reverse=True)
        if meta_sample[0] in results:
            results[all_meta_sample[0]].append(sorted_likelihoods)
        else:
            results[all_meta_sample[0]] = [sorted_likelihoods]

    return results


def aggregate_rankings(sorted_lists):
    scores = defaultdict(int)
    
    for sorted_list in sorted_lists:
        sorted_list = sorted(sorted_list, key=lambda x: x[1], reverse=True)
        for rank, word in enumerate(sorted_list, start=1):
            # Higher rank (lower index) gets a higher score; use inverse of rank
            scores[word[0]] += 1 / rank
    
    # Sort words by their aggregated scores in descending order
    final_ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Return only the words, sorted
    return [word for word, score in final_ranking]

def batch_inference(input_texts, prompt_metadata, model, logits_processor, tokenizer,
                    attribute_list, output_file, normalized_prob, batch_size=16, num_return_sequences=4):
    """
    Perform batch inference on a list of input texts:

        Perform batch inference on a list of input texts.

    Parameters:
    - input_texts: List of strings, the texts to run inference on.
    - batch_size: int, the number of texts to process per batch.
    - max_length: int, maximum length of generated response.

    Returns:
    - List of generated responses.
    """
    results = []

    # Process each batch
    for i in tqdm(range(0, len(input_texts), batch_size)):
        batch_texts = input_texts[i:i + batch_size]
        meta_data = prompt_metadata[i:i + batch_size]

        # Generate predictions
        with torch.no_grad():
            probs = compute_label_likelihood(model, tokenizer, batch_texts, meta_data, attribute_list, normalized_prob)

        results.append(probs)
        # if i % 10 == 0:
        #    save_data(results, prompt_metadata, output_file)
    
    # Iterate through the list of dictionaries
    merged_dict = {}
    for d in results:
        for key, value in d.items():
            if key not in merged_dict:
                merged_dict[key] = value  # Initialize if the key doesn't exist
            else:
                merged_dict[key].extend(value)  # Append if the key already exists

    print(merged_dict)
    return merged_dict

# Save the data
def save_data(results, prompt_metadata, output_path):
    """
    Save the processed data to a CSV file.

    Parameters:
        data (pd.DataFrame): Data with inference results to be saved.
        output_path (str): Path to the output file.
    """
    salaries = [[salary for salary in n_seq] for n_seq in results]
    languages = [i[0] for i in prompt_metadata[:len(results)]]
    # Step 3: Save the data
    processed_data = pd.DataFrame(
        {"language": languages, "salary": salaries})
    processed_data.to_csv(output_path, index=False)


def extract_prediction(df):
    def extract_logic(answer, prompt_id):
        answer = answer.split("[/INST] ")[-1]

        splitting_words = [".", "\n", ":"]
        for split_word in splitting_words:
            answer = answer.split(split_word)[0]

        if answer == "a":
            if prompt_id % 2 == 0:
                return 1
            else:
                return 0
        elif answer == "b":
            if prompt_id % 2 == 0:
                return 0
            else:
                return 1
        else:
            return None
    df['predictions'] = df.apply(lambda x: extract_logic(
        x['answer'], x['prompt_id']), axis=1)
    return df


def calculate_accuracy(df):
    # Calculate accuracy
    accuracy = (df['labels'] == df['predictions']).mean()

    # Display the accuracy
    print(f'Accuracy: {accuracy:.2f}')


def load_attributes(file_path):
    # Load the file into a list
    with open(file_path, "r", encoding="utf-8") as file:
        words_list = [line.strip() for line in file if line.strip()]
    return words_list


def calculate_normalization(model, tokenizer, prompt_metadata, attribute_list):
    prefix_str_normalization = ["N/A", "[MASK]", ""]  # Add more prefixes as needed
    normalized_prob = {}

    for prompt in tqdm(prompt_metadata):
        prompt = prompt[1]

        # Initialize a dictionary to accumulate probabilities for averaging
        prefix_accumulator = {label: 0 for label in attribute_list}

        for prefix in prefix_str_normalization:
            prompt_norm = prompt.format(prefix)

            # Tokenize the prompt
            prompt_ids = tokenizer(prompt_norm, return_tensors="pt", add_special_tokens=True)["input_ids"]
            prompt_length = prompt_ids.size(1)

            # Iterate through all words (possible labels)
            for label in attribute_list:
                # Tokenize the label (disable adding special tokens again)
                label_ids = tokenizer(label, return_tensors="pt", add_special_tokens=False)["input_ids"]
                input_ids = torch.cat([prompt_ids, label_ids], dim=-1).to("cuda")

                # Get model outputs
                raw_likelihood, normalized_likelihood = get_prob_label(model, input_ids, prompt_length, word_prob=None)

                # Accumulate probabilities for this prefix
                prefix_accumulator[label] += raw_likelihood

        # Compute the average for each label
        for label in attribute_list:
            normalized_prob[label + "_" + prompt] = prefix_accumulator[label] / len(prefix_str_normalization)

    return normalized_prob

# Main workflow
def main(model_name, output_file):

    # Step 0: Load the Model
    model, tokenizer, logits_processor = load_model(model_name)

    prompts, prompt_metadata = tokenize_data(tokenizer)

    positive_file_path = "/lustre/project/ki-topml/minbui/repos/DialectSalary/adjective_estimation/data/positive.txt"
    negative_file_path = "/lustre/project/ki-topml/minbui/repos/DialectSalary/adjective_estimation/data/negative.txt"
    pos_attribute_list = load_attributes(positive_file_path)
    neg_attribute_list = load_attributes(positive_file_path)
    pos_attribute_list = pos_attribute_list[:10]
    neg_attribute_list = neg_attribute_list[:10]
    attribute_list = pos_attribute_list + neg_attribute_list

    normalized_prob = calculate_normalization(model, tokenizer, prompt_metadata, attribute_list)

    # Step 2: Perform inference
    results = batch_inference(prompts, prompt_metadata, model, logits_processor, tokenizer, attribute_list, output_file, normalized_prob)

    for language in LANGUAGES:
        agg_results = aggregate_rankings(results[language])
        print(language)
        print(agg_results)
        # Extract the top 10 attributes
        top_10 = agg_results[:10]

        # Count positive and negative attributes in the top 10
        pos_count = sum(1 for attr in top_10 if attr in pos_attribute_list)
        neg_count = sum(1 for attr in top_10 if attr in neg_attribute_list)

        print(f"Positive in top 10: {pos_count}")
        print(f"Negative in top 10: {neg_count}")

    save_data(results, prompt_metadata, output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run inference on a dataset and save the results.")
    parser.add_argument("--model_name", type=str, default="/lustre/project/ki-topml/minbui/projects/models/sync/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659",
                        help="Name of the model to use for inference.")
    parser.add_argument("--output_folder", type=str,
                        default="/lustre/project/ki-topml/minbui/repos/DialectSalary/adjective_estimation/output", help="Path to the output CSV file.")

    args = parser.parse_args()

    model_name = args.model_name.split("/")[-3]
    output_file = os.path.join(args.output_folder, model_name + ".csv")

    main(args.model_name, output_file)
