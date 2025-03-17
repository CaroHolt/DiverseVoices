import pandas as pd
import argparse
import os
import matplotlib.pyplot as plt
from collections import Counter
import numpy as np


MODELS = {
    # > 70B
    "Meta-Llama-3.1-70B-Instruct.csv": "Llama-3.1-70B",
    "Llama-3.3-70B-Instruct.csv": "Llama-3.3-70B",
    "Qwen2-72B-Instruct.csv": "Qwen2.5 72B",
    "qwen_2.5_72b_chat.csv": "Qwen2.5 72B",

    # Medium
    "c1df2547e1f5fe22e1f4897f980f231dc74cfc27.csv": "Aya 32b",
    "aya-expanse-32b.csv": "Aya 32b",

    # Small
    "0e9e39f249a16976918f6564b8830bc894c89659.csv": "Llama-3.1-8B",
    "bb46c15ee4bb56c5b63245ef50fd7637234d6f75.csv": "Qwen2.5 8B",
    "e46040a1bebe4f32f4d2f04b0a5b3af2c523d11b.csv": "Aya 8B",
}

education_mapping = {
    "Bachelor's degree": ["Bachelor's degree", "bachelor's degree", "Bachelor's", 'university degree', "Bachelor"],
    "Master's degree": ["Master's degree", "Master's"],
    "High school diploma": ["High school diploma", "High school diploma.", "Abitur", "high scool degree", "High School"],
    "Ph.D.": ["Ph.D.", "PhD"]
}


def unify_categories(data, mapping):
    unified_data = {category: 0 for category in mapping}  # Initialize mapped categories with 0

    # Track keys that were already included in the mapping
    mapped_keys = set(key for values in mapping.values() for key in values)

    for key, value in data.items():
        # Check if the key is in any mapped category
        found = False
        for category, values in mapping.items():
            values = [i.lower() for i in values]
            print(values)
            if key.lower() in values:
                unified_data[category] += value  # Sum up the values
                found = True
                break  # No need to check further, as the key is already mapped
        
        # If the key wasn't in the mapping, just copy it over
        if not found:
            unified_data[key] = value
    
    return unified_data

def plot_string_histogram(list1, list2, language, filename='histogram.png'):
    # Count the frequency of each unique string in both lists
    counts1 = Counter(list1)
    counts2 = Counter(list2)

    counts1 = unify_categories(counts1, education_mapping)
    counts2 = unify_categories(counts2, education_mapping)

    counts1 = {key: value for key, value in counts1.items() if value > 5}
    counts2 = {key: value for key, value in counts2.items() if value > 5}
    print(counts1)
    print(counts2)
    # Create a list of unique labels from both lists
    labels = list(set(counts1.keys()).union(set(counts2.keys())))
    
    # Create lists of counts for each label
    counts1_values = [counts1.get(label, 0) for label in labels]
    counts2_values = [counts2.get(label, 0) for label in labels]
    # Sort based on counts1_values in descending order
    sorted_indices = np.argsort(counts1_values)[::-1]  # Sort indices in descending order
    labels = [labels[i] for i in sorted_indices]
    counts1_values = [counts1_values[i] for i in sorted_indices]
    counts2_values = [counts2_values[i] for i in sorted_indices]
    
    # Set the width of the bars
    bar_width = 0.35
    
    # Set the positions of the bars on the x-axis
    index = np.arange(len(labels))
    
    # Create a larger figure for better visualization
    plt.figure(figsize=(12, 4))
    
    # Plotting the bars
    plt.bar(index - bar_width / 2, counts1_values, bar_width, label='Standard', color='b')
    plt.bar(index + bar_width / 2, counts2_values, bar_width, label='Dialect', color='r')
    
    # Add labels and title
    #plt.xlabel('Adjectives')
    #plt.ylabel('Frequency')
    plt.title('Comparison of Adjectives for language: {}'.format(language.upper()))
    
    # Rotate the x-axis labels for better readability
    plt.xticks(index, labels, rotation=45, ha='right')
    plt.legend()
    
    # Save the figure
    plt.tight_layout()
    print(filename)
    plt.savefig(filename)

def main(input_folder, output_folder, verbose=1):

    for file, model_name in MODELS.items():
        input_file = os.path.join(input_folder, file)
        if not os.path.exists(input_file):
            continue
        input_file = input_file.replace(".csv", ".pkl")    
        df = pd.read_pickle(input_file)
        df["answer"] = df.apply(lambda row: row["answer"][0].split(', '), axis=1)

        df_grouped = df.groupby(["language", "text_type"], as_index=False).agg({'answer': sum})
        all_standard = []
        all_dialect = []
        for language in df["language"].unique():
            df_subset = df_grouped[df_grouped["language"] == language]

            standard = df_subset[df_subset["text_type"] == "standard_text"]["answer"].iloc[0]
            dialect = df_subset[df_subset["text_type"] == "dialect_text"]["answer"].iloc[0]

            all_standard += standard
            all_dialect += dialect
            
            #print(f"Language: {language}, Text Type: {text_type}, Sum: {total_answer}")
            os.makedirs(os.path.join(output_folder, model_name), exist_ok=True)
            plot_string_histogram(standard, dialect, language, os.path.join(output_folder, model_name, language))

        print(os.path.join(output_folder, model_name, "All.png"))
        plot_string_histogram(all_standard, all_dialect, "All Dialects", os.path.join(output_folder, model_name, "All.png"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run inference on a dataset and save the results.")
    parser.add_argument("--input_folder", type=str,
                        default="/lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/output/{}_extracted", help="Path to the input CSV file.")
    parser.add_argument("--output_folder", type=str,
                        default="/lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/output/plots/{}", help="Path to the input CSV file.")
    parser.add_argument("--task", type=str,
                        default="location_usa", help="Path to the input CSV file.")

    args = parser.parse_args()

    args.input_folder = args.input_folder.format(args.task)
    args.output_folder = args.output_folder.format(args.task)
    main(args.input_folder, args.output_folder)
