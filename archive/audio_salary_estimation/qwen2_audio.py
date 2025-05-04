from io import BytesIO
import librosa
from transformers import Qwen2AudioForConditionalGeneration, AutoProcessor
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import pandas as pd
import argparse
from allm_gender_bias.prompts import set_prompts
from tqdm import tqdm
import os

DEVICE = "cuda"

LANGUAGES = ["german", "german_sui"]


def load_model(model_name):
    processor = AutoProcessor.from_pretrained(model_name)
    model = Qwen2AudioForConditionalGeneration.from_pretrained(model_name, device_map="auto")
    return model, processor


def tokenize_data(data, tokenizer):

    SYSTEM_PROMPT, PROMPT, OCCUPATIONS = set_prompts()
    all_prompts = []

    prompts_template = []
    prompt_metadata = []
    for occupation in OCCUPATIONS:
        for prompts in PROMPT:
            for sample in data:
                prompt1 = prompts[0].format(occupation)
                messages = [
                    {'role': 'system', 'content': SYSTEM_PROMPT}, 
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt1},
                        {"type": "audio", "audio_url": sample},
                        {"type": "text", "text": prompts[1]},

                    ]}
                ]
                messages_applied = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
                prompts_template.append([messages_applied, messages])
                prompt_metadata.append([sample, occupation])

    return prompts_template, prompt_metadata



def batch_inference(prompts, model, processor, prompt_metadata, output_file, batch_size=64, num_return_sequences=4):
    """
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
    for sample in tqdm(prompts):
        audios = []
        for message in sample[1]:
            if isinstance(message["content"], list):
                for ele in message["content"]:
                    if ele["type"] == "audio":
                        audios.append(
                            librosa.load(ele['audio_url'], sr=processor.feature_extractor.sampling_rate)[0]
                        )

        inputs = processor(text=sample[0], audios=audios, return_tensors="pt", padding=True)
        inputs = inputs.to("cuda")
        with torch.no_grad():
            generate_ids = model.generate(
                **inputs,
                max_new_tokens=200,
                num_return_sequences=num_return_sequences,
                #pad_token_id=processor.eos_token_id,  # Ensure padding if needed,
                do_sample=True,
                temperature=0.7,
                top_k=100,
                top_p=0.9
            )
        generate_ids = generate_ids[:, inputs.input_ids.size(1):]
        decoded_outputs = processor.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
        decoded_outputs = [decoded_outputs[i:i+num_return_sequences] for i in range(0, len(decoded_outputs), num_return_sequences)]
        results += decoded_outputs

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
    languages = [i[0].split("/")[-1].split(".")[0] for i in prompt_metadata[:len(results)]]
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


def load_data(input_folder):
    return [os.path.abspath(os.path.join(input_folder, f)) for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]


# Main workflow
def main(model_name, input_folder, output_file):
    # Load Data
    data = load_data(input_folder)

    # Step 0: Load the Model
    model, processor = load_model(model_name)

    prompts, prompt_metadata = tokenize_data(data, processor)

    # Step 2: Perform inference
    results = batch_inference(prompts, model, processor, prompt_metadata, output_file)

    save_data(results, prompt_metadata, output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run inference on a dataset and save the results.")
    parser.add_argument("--model_name", type=str, default="/lustre/project/ki-topml/minbui/projects/models/sync/models--Qwen--Qwen2-Audio-7B-Instruct/snapshots/b825d41106cd5cef971cd2ace8d5349fd2e385ee",
                        help="Name of the model to use for inference.")
    parser.add_argument("--output_folder", type=str,
                        default="/lustre/project/ki-topml/minbui/repos/DialectSalary/audio_salary_estimation/output", help="Path to the output CSV file.")
    parser.add_argument("--input_folder", type=str,
                        default="/lustre/project/ki-topml/minbui/repos/DialectSalary/audio_salary_estimation/input/text_sentence", help="Path to the output CSV file.")

    args = parser.parse_args()

    model_name = args.model_name.split("/")[-3]
    output_file = os.path.join(args.output_folder, model_name + ".csv")

    main(args.model_name, args.input_folder, output_file)
