from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import pandas as pd
import argparse
from prompts import set_prompts
from tqdm import tqdm
import os

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

    PROMPTS, OCCUPATIONS, TEXTS, SYSTEM_PROMPT = set_prompts()
    all_prompts = []
    for index, prompt in enumerate(PROMPTS):
        for occupation in OCCUPATIONS:
            for language in LANGUAGES:
                for text in TEXTS[language]:
                    prompt_original = prompt.format(occupation, text)
                    all_prompts.append([prompt_original, [language, occupation,]])

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



def batch_inference(input_texts, model, logits_processor, tokenizer, prompt_metadata, output_file, batch_size=16, num_return_sequences=4):
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

        # Tokenize and pad inputs for batch processing
        inputs = tokenizer(batch_texts, return_tensors="pt",
                           padding=True, truncation=True).to(DEVICE)

        # Generate predictions
        with torch.no_grad():
            outputs = model.generate(
                inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                max_new_tokens=150,
                num_return_sequences=num_return_sequences,
                pad_token_id=tokenizer.eos_token_id,  # Ensure padding if needed,
                do_sample=True,
                temperature=0.7,
                top_k=100,
                top_p=0.9,
                logits_processor=logits_processor
            )

        # Decode the predictions and append to results
        decoded_outputs = [tokenizer.decode(
            output, skip_special_tokens=True) for output in outputs]
        decoded_outputs = [decoded_outputs[i:i+num_return_sequences] for i in range(0, len(decoded_outputs), num_return_sequences)]
        results += decoded_outputs

        if i % 10 == 0:
            save_data(results, prompt_metadata, output_file)

    return results

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
    prompt_occupation = [i[1] for i in prompt_metadata[:len(results)]]
    # Step 3: Save the data
    processed_data = pd.DataFrame(
        {"language": languages, "occupation": prompt_occupation, "salary": salaries})
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


# Main workflow
def main(model_name, output_file):

    # Step 0: Load the Model
    model, tokenizer, logits_processor = load_model(model_name)

    prompts, prompt_metadata = tokenize_data(tokenizer)

    # Step 2: Perform inference
    results = batch_inference(prompts, model, logits_processor, tokenizer, prompt_metadata, output_file)

    save_data(results, prompt_metadata, output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run inference on a dataset and save the results.")
    parser.add_argument("--model_name", type=str, default="/lustre/project/ki-topml/kabecher/models/Meta-Llama-3.1-70B-Instruct",
                        help="Name of the model to use for inference.")
    parser.add_argument("--output_folder", type=str,
                        default="/lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/output", help="Path to the output CSV file.")

    args = parser.parse_args()

    model_name = args.model_name.split("/")[-3]
    output_file = os.path.join(args.output_folder, model_name + ".csv")

    main(args.model_name, output_file)
