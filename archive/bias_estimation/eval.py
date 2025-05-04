import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import math
from allm_gender_bias.prompts import PROFESSIONS_AB, PROFESSIONS_IMPLICIT
import re
import scipy.stats as stats
import numpy as np


FILEPATH = "text.csv"

MODELS = {
    # > 70B
    "Meta-Llama-3.1-70B-Instruct": "Llama-3.1-70B",
    "Llama-3.3-70B-Instruct": "Llama-3.3-70B",
    "Qwen2-72B-Instruct": "Qwen2.5 72B",
    "qwen_2.5_72b_chat": "Qwen2.5 72B",

    # Medium
    "c1df2547e1f5fe22e1f4897f980f231dc74cfc27": "Aya 32b",
    "aya-expanse-32b": "Aya 32b",

    # Small
    "0e9e39f249a16976918f6564b8830bc894c89659": "Llama-3.1-8B",
    "bb46c15ee4bb56c5b63245ef50fd7637234d6f75": "Qwen2.5 8B",
    "e46040a1bebe4f32f4d2f04b0a5b3af2c523d11b": "Aya 8B",
}


df = pd.read_csv(FILEPATH)
df_adj = pd.read_csv("data/adjectives.csv")


def preprocess_answer(answer):
    
    # Check if the answer is NaN
    if isinstance(answer, float) and math.isnan(answer):
        return None  # or any value you want to return for NaN
    
    # Proceed with splitting if the answer is not NaN
    answer = answer.split(": ")[-1].lower()
    return answer

def filter_pairs(standard_counts, dialect_counts, size=10):
    indices_to_keep = []

    # Loop through the standard_counts in pairs
    for i in range(0, len(standard_counts), 2):
        # Ensure there's another item in the next pair
        if i + 1 < len(standard_counts):
            count1 = standard_counts.iloc[i]
            count2 = dialect_counts.iloc[i]
            # Check if the difference is greater than 10
            if abs(count1 - count2) > size:
                indices_to_keep.append(standard_counts.index[i])
                indices_to_keep.append(standard_counts.index[i+1])

    # Filter the standard_counts based on the indices to keep
    filtered_counts = standard_counts.loc[indices_to_keep]
    return filtered_counts


def get_counts(df, task):

    adjective_type = task.split("_")[-1]

    df[f"model_response_{task}_{model}"] = df.apply(lambda row: preprocess_answer(row[f"model_response_{task}_{model}"]), axis=1)

    # Filter the data
    responses_standard = df[df["text_type"] == "standard_text"][
    f"model_response_{task}_{model}"
    ].rename("response").dropna()
    responses_dialect = df[df["text_type"] == "dialect_text"][
    f"model_response_{task}_{model}"
    ].rename("response").dropna()

    standard_counts = responses_standard.value_counts()
    dialect_counts = responses_dialect.value_counts()

    return df, standard_counts, dialect_counts


def histogram_plot(df, df_adj, model, task, language):
    df, standard_counts, dialect_counts = get_counts(df, task)

    # Plot histogram
    plt.figure(figsize=(10, 6))
    sns.histplot(responses_standard, bins=20, kde=True, color="blue", label="Standard Text", alpha=0.6)
    sns.histplot(responses_dialect, bins=20, kde=True, color="red", label="Dialect Text", alpha=0.6)

    mean_standard = responses_standard.mean()
    std_standard = responses_standard.std()
    mean_dialect = responses_dialect.mean()
    std_dialect = responses_dialect.std()

    plt.axvline(mean_standard, color="blue", linestyle="dashed", linewidth=2, label=f"Mean (Standard): {mean_standard:.2f}")
    plt.axvline(mean_dialect, color="red", linestyle="dashed", linewidth=2, label=f"Mean (Dialect): {mean_dialect:.2f}")
    # Add shaded regions for std deviation
    plt.fill_betweenx(y=[0, 1], x1=mean_standard - std_standard, x2=mean_standard + std_standard, color="blue", alpha=0.2)
    plt.fill_betweenx(y=[0, 1], x1=mean_dialect - std_dialect, x2=mean_dialect + std_dialect, color="red", alpha=0.2)

    # Labels and legend
    plt.xlabel(f"{adjective_type.capitalize()} Score")
    plt.ylabel("Frequency")
    plt.title(f"Distribution of {adjective_type.capitalize()} Scores for Different Text Types")
    plt.legend()
    plt.savefig("plots" + "_" + FILEPATH.split(".csv")[0]  + f"/histogram_{model}_{task}_{language}.png", dpi=300, bbox_inches="tight")
    return responses_standard, responses_dialect


def histogram_plot(df, df_adj, model, task, language):
    df, standard_counts, dialect_counts = get_counts(df, task)


    standard_counts = standard_counts[standard_counts > 5]
    dialect_counts = dialect_counts[dialect_counts > 5]
    standard_counts = standard_counts.to_frame().reset_index()
    dialect_counts = dialect_counts.to_frame().reset_index()

    # Merge with adjective dataset
    standard_counts = standard_counts.merge(df_adj, left_on="response", right_on="word", how="left")
    dialect_counts = dialect_counts.merge(df_adj, left_on="response", right_on="word", how="left")

    standard_counts = standard_counts.sort_values(by=adjective_type)
    dialect_counts = dialect_counts.sort_values(by=adjective_type)

    standard_counts = standard_counts.set_index("response")
    dialect_counts = dialect_counts.set_index("response")

    # Create a DataFrame for plotting
    df_counts = pd.DataFrame({
        "Standard": standard_counts["count"],
        "Dialect": dialect_counts["count"]
    }).fillna(0)  # Fill NaN values with 0 in case some words are missing from either category

    # Plot
    df_counts.plot(kind="bar", figsize=(12, 4))
    #mean_standard = responses_standard.mean()
    #mean_dialect = responses_dialect.mean()
    #plt.axvline(mean_standard, color="blue", linestyle="dashed", linewidth=2, label=f"Mean (Standard): {mean_standard:.2f}")
    #plt.axvline(mean_dialect, color="red", linestyle="dashed", linewidth=2, label=f"Mean (Dialect): {mean_dialect:.2f}")

    # Labels and legend
    plt.xlabel(f"{adjective_type.capitalize()} Score")
    plt.ylabel("Frequency")
    plt.title(f"Distribution of {adjective_type.capitalize()} Scores for Different Text Types")
    plt.legend()
    plt.savefig("plots" + "_" + FILEPATH.split(".csv")[0]  + f"/histogram_{model}_{task}_{language}.png", dpi=300, bbox_inches="tight")

    return None, None

def histogram_plot_profession_ab(df, model, task, language):
    df, standard_counts, dialect_counts = get_counts(df, task)

    # pd.set_option('display.max_rows', None)

    low_paying_jobs = [pair[0].lower() for pair in PROFESSIONS_AB["german"]]
    high_paying_jobs = [pair[1].lower() for pair in PROFESSIONS_AB["german"]]

    standard_counts["Low-paying Total"] = sum(standard_counts.get(job, 0) for job in low_paying_jobs)
    standard_counts["High-paying Total"] = sum(standard_counts.get(job, 0) for job in high_paying_jobs)
    dialect_counts["Low-paying Total"] = sum(dialect_counts.get(job, 0) for job in low_paying_jobs)
    dialect_counts["High-paying Total"] = sum(dialect_counts.get(job, 0) for job in high_paying_jobs)
    standard_counts = standard_counts[["High-paying Total", "Low-paying Total"]]
    dialect_counts = dialect_counts[["High-paying Total", "Low-paying Total"]]

    standard_counts = standard_counts[standard_counts > 5]
    dialect_counts = dialect_counts[dialect_counts > 5]
    standard_counts = standard_counts.to_frame()
    dialect_counts = dialect_counts.to_frame()

    # Create a DataFrame for plotting
    df_counts = pd.DataFrame({
        "Standard": standard_counts["count"],
        "Dialect": dialect_counts["count"]
    }).fillna(0)  # Fill NaN values with 0 in case some words are missing from either category

    # Plot
    df_counts.plot(kind="bar", figsize=(12, 4))
    plt.ylabel("Frequency")
    plt.title(f"Distribution for Different Professions")
    plt.legend()
    plt.savefig("plots" + "_" + FILEPATH.split(".csv")[0]  + f"/histogram_summarized_{model}_{task}_{language}.png", dpi=300, bbox_inches="tight")


def histogram_plot_profession(df, model, task, language, size=5):
    df, standard_counts, dialect_counts = get_counts(df, task)

    jobs = [item.lower() for sublist in PROFESSIONS_AB["german"] for item in sublist]

    standard_counts = standard_counts.reindex(jobs, fill_value=0)
    dialect_counts = dialect_counts.reindex(jobs, fill_value=0)
    standard_counts = filter_pairs(standard_counts, dialect_counts, size=size)
    dialect_counts = dialect_counts.reindex(list(standard_counts.index), fill_value=0)

    #standard_counts = standard_counts[standard_counts > 5]
    #dialect_counts = dialect_counts[dialect_counts > 5]
    standard_counts = standard_counts.to_frame()
    dialect_counts = dialect_counts.to_frame()

    # Create a DataFrame for plotting
    df_counts = pd.DataFrame({
        "Standard": standard_counts["count"],
        "Dialect": dialect_counts["count"]
    }).fillna(0)  # Fill NaN values with 0 in case some words are missing from either category

    # Normalize for Standard and Dialect independently in pairs
    for i in range(0, len(df_counts), 2):  # Step by 2 to handle pairs
        pair = df_counts.iloc[i:i+2]
        
        # Normalize 'Standard' and 'Dialect' separately
        standard_max = pair['Standard'].sum()  # Max for Standard in the pair
        dialect_max = pair['Dialect'].sum()  # Max for Dialect in the pair
        
        # Normalize each category within the pair
        df_counts.iloc[i:i+2, df_counts.columns.get_loc('Standard')] = pair['Standard'] / standard_max
        df_counts.iloc[i:i+2, df_counts.columns.get_loc('Dialect')] = pair['Dialect'] / dialect_max

    # Plot
    ax = df_counts.plot(kind="bar", figsize=(12, 4))
    #plt.xticks(rotation=45)

    # separators
    num_bars = len(df_counts)
    for i in range(2, num_bars, 2):  # Start from 2 and step by 2
        ax.axvline(x=i - 0.5, color='black', linestyle='--', linewidth=2)

    plt.ylabel("Frequency")
    plt.title(f"Distribution for Different Professions")
    plt.legend()
    plt.savefig("plots" + "_" + FILEPATH.split(".csv")[0]  + f"/histogram_{model}_{task}_{language}.png", dpi=300, bbox_inches="tight")


def compute_bias(value_dictionary, sa, sb, xa, xb):
    """
    Computes the bias based on the given formula.
    
    Parameters:
    N (function): A function that takes two arguments (s, X) and returns a count.
    sa, sb: Categories or labels.
    Xa, Xb: Groups or datasets.
    
    Returns:
    float: Computed bias value.
    """

    sa_xa = value_dictionary[sa][xa]
    sa_xb = value_dictionary[sa][xb]
    sb_xa = value_dictionary[sb][xa]
    sb_xb = value_dictionary[sb][xb]
    if (sa_xa + sa_xb) == 0 or (sb_xa + sb_xb) == 0:
        return 0

    term1 = sa_xa / (sa_xa + sa_xb)
    term2 = sb_xb / (sb_xa + sb_xb)
    
    return term1 + term2 - 1



def histogram_plot_profession_implicit(df, model, task, language):
    def preprocess_implicit(answer):
        if isinstance(answer, float) and math.isnan(answer):
            return None  # or any value you want to return for NaN

        answer = answer.lower()
        answer = answer.split(": ")[-1].lower()
        answer = answer.split(":")[-1].lower()
        #initial = "plasterers"
        #if initial in answer:
        #    answer = answer.split(initial)[-1].lower()
        #    answer = initial + answer
        answer = answer.split("\n")
        return answer

    def preprocess_list_answer(text_list):
        texts = []
        for text in text_list:
            print(text)
            texts.append(re.findall(r"([\w\s]+) - ([ab])", text)[0])
        return texts

    adjective_type = task.split("_")[-1]
    df[f"model_response_{task}_{model}"] = df.apply(lambda row: preprocess_implicit(row[f"model_response_{task}_{model}"]), axis=1)
    print(df[f"model_response_{task}_{model}"] )
    df[f"model_response_{task}_{model}"] = df.apply(lambda row: preprocess_list_answer(row[f"model_response_{task}_{model}"]), axis=1)
    print(df[f"model_response_{task}_{model}"])
    professions = PROFESSIONS_IMPLICIT["german"]
    professions = [[item.lower() for item in sublist] for sublist in professions]

    biases = []
    not_found = 0
    for model_association in df[f"model_response_{task}_{model}"]:
        counts = {
            "dialect": {"gt_low": 0, "gt_high": 0},
            "standard": {"gt_low": 0, "gt_high": 0},
        }

        for pair in model_association:
            # gt_low
            if pair[1] == "b":
                pred_key = "dialect"
            elif pair[1] == "a":
                pred_key = "standard"
            else:
                not_found += 1
                continue

            # prediction
            if pair[0] in professions[0]:
                counts[pred_key]["gt_low"] += 1
            elif pair[0] in professions[1]:
                counts[pred_key]["gt_high"] += 1
            else:
                not_found += 1

        bias = compute_bias(counts, "standard", "dialect", "gt_high", "gt_low")
        biases.append(bias)

    t_stat, p_value = stats.ttest_1samp(biases, 0)
    print(biases)
    # Compute statistics
    mean_bias = np.mean(biases)
    std_bias = np.std(biases)#, ddof=1)
    #lower_bound = np.percentile(biases, 2.5)   # 2.5th percentile
    #upper_bound = np.percentile(biases, 97.5)  # 97.5th percentile
    #lower_error = mean_bias - lower_bound
    #upper_error = upper_bound - mean_bias

    # Plot
    plt.figure(figsize=(6, 4))
    plt.errorbar(1, mean_bias, yerr=std_bias, fmt='o', capsize=5, label="Mean ± Std", color='b')
    #plt.errorbar(1.1, mean_bias, yerr=[[lower_error], [upper_error]], 
    #            fmt='o', capsize=5, label="95% Percentile Interval", color='g')

    plt.axhline(0, color='r', linestyle='--', label="Zero Bias")

    # Labels and formatting
    plt.xticks([])
    plt.yticks([-1, -0.5, 0, 0.5, 1])
    plt.ylabel("Bias Value")
    plt.title("Mean Bias with Standard Deviation")
    plt.legend()
    plt.savefig("plots/test.png", dpi=300, bbox_inches="tight")

    print(f"T-statistic: {t_stat:.4f}, P-value: {p_value:.4f}")
    das

def profession_explicit(df, model, task):
    #adjective_type = task.split("_")[-1]
    #df[f"model_response_{task}_{model}"] = df.apply(lambda row: preprocess_implicit(row[f"model_response_{task}_{model}"]), axis=1)
    answers = df[f"model_response_{task}_{model}"]

    professions = PROFESSIONS_IMPLICIT["german"]
    prompts = df[f"prompts"]
    counts = {key: {"writer a": 0 , "writer b": 0} for key in professions[0] + professions[1]}
    for profession in professions[0] + professions[1]:
        for prompt, answer in zip(prompts, answers):
            if "'" + profession + "'" in prompt:
                answer = answer.lower().replace(".", "")
                counts[profession][answer.lower()] += 1

    print(counts)

for model, model_name in MODELS.items():
    print(model_name)

    for task in ["profession_explicit", "profession_implicit", "profession_implicit_reverse", "profession_implicit_explicit", "adjective_princeton", "adjective_arousal", "adjective_valence", "adjective_dominance", "profession", "profession_ab"]:
        column = f"model_response_{task}_{model}"
        for language in ['als', 'bar', 'frr', 'ksh', 'nds', 'pfl', 'stq']:
            df_lang = df[df["language"] == language]
            if column in df:
                if task in ["adjective_arousal", "adjective_valence", "adjective_dominance"]:
                    responses_standard, responses_dialect = histogram_plot(df_lang, df_adj, model, task, language)
                elif task == "profession_ab":
                    histogram_plot_profession(df_lang, model, task, language)

        if column in df:
            if task in ["adjective_arousal", "adjective_valence", "adjective_dominance"]:
                responses_standard, responses_dialect = histogram_plot(df, df_adj, model, task, "")
            elif task == "profession_ab":
                histogram_plot_profession(df, model, task, "", size=40)
                histogram_plot_profession_ab(df, model, task, "")
            elif "profession_implicit" in task:
                histogram_plot_profession_implicit(df, model, task, "")
            elif "profession_explicit" in task:
                profession_explicit(df, model, task)
