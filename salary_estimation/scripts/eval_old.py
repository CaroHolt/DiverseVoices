import pandas as pd
import argparse
import re
from prompts import OCCUPATIONS
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf




def load_data(file_path):
    """
    Load data from a CSV file.

    Parameters:
        file_path (str): Path to the input file.

    Returns:
        pd.DataFrame: Loaded data as a DataFrame.
    """
    data = pd.read_csv(file_path)
    data = data.assign(id=range(0, len(data)))
    # data.to_csv(file_path, index=False)
    return data


def save_data(data, output_path):
    """
    Save the processed data to a CSV file.

    Parameters:
        data (pd.DataFrame): Data with inference results to be saved.
        output_path (str): Path to the output file.
    """
    data.to_csv(output_path, index=False)


def calc_avg_for_str(data, check_str):
    print("---------" + check_str + "--------")

    subset = data[(data["prompt_prefix"] == check_str) |
                  (data["prompt_occupation"] == check_str)]
    romanized_data, original_data = get_versions_data(subset)
    print_avg(subset, romanized_data, original_data)
    return subset


def get_versions_data(data):
    # Filter rows based on even and odd IDs
    german_data = data[data["language"] == "german"]
    # Old german_sui description
    german_dia_data = data[(data["language"] == "german_dia") | (data["language"] == "german_sui")]
    return german_data, german_dia_data


def print_avg(data, verbose=0):
    german_data, german_dia_data = get_versions_data(data)
    # Calculating means and standard deviations
    min_value = data["average_salary"].dropna().min()
    max_value = data["average_salary"].dropna().max()

    print(f"Minimum value: {min_value}")
    print(f"Maximum value: {max_value}")
    average_accept = data["average_salary"].dropna().mean()
    std_accept = data["average_salary"].dropna().std()

    average_german = german_data["average_salary"].dropna().mean()
    std_german = german_data["average_salary"].dropna().std()

    average_sui = german_dia_data["average_salary"].dropna().mean()
    std_sui = german_dia_data["average_salary"].dropna().std()

    # Assuming `average_salary` columns contain salary data for both datasets
    p_value = permutation_test(german_dia_data, german_data)

    # Output the result
    # if p_value < 0.05 or verbose == 1:
    print(f"P-value: {p_value}")
    print("Average Salaries")
    print("----------------")
    print(f"Overall Average Salary: { average_accept:.2f} (Std Dev: {std_accept:.2f})")
    print(f"German: {average_german:.2f} (Std Dev: {std_german:.2f})")
    print(f"German Dialect: {average_sui:.2f} (Std Dev: {std_sui:.2f})")
    percentage_difference = (
        (average_sui - average_german) / average_german) * 100
    print(f"Diff: {percentage_difference:.2f}%")

    if p_value < 0.05:
        print_table = f"{average_german:,.0f} & {average_sui:,.0f} & \\textcolor{{darkgreen}}{{\\textit{{+{percentage_difference:.2f}\\%*}}}}"
    else:
        print_table = f"{average_german:,.0f} & {average_sui:,.0f} & \\textcolor{{darkgreen}}{{\\textit{{+{percentage_difference:.2f}\\%}}}}"

    if percentage_difference < 0:
        print_table = print_table.replace("+", "")
        print_table = print_table.replace("darkgreen", "red")
    print(print_table)

    return percentage_difference, average_accept
    # return None, average_accept


def permutation_test(romanized_data, original_data):
    # Observed difference in means between the Romanized and original data
    observed_diff = romanized_data["average_salary"].mean(
    ) - original_data["average_salary"].mean()

    # Combine the data from both groups
    combined_data = np.concatenate(
        [romanized_data["average_salary"], original_data["average_salary"]])

    # Define the number of permutations
    n_permutations = 10000

    # Initialize an array to store mean differences from each permutation
    permuted_diffs = np.zeros(n_permutations)

    # Permutation test
    for i in range(n_permutations):
        # Shuffle the combined data
        np.random.shuffle(combined_data)

        # Split the shuffled data into two new groups
        permuted_group1 = combined_data[:len(romanized_data)]
        permuted_group2 = combined_data[len(romanized_data):]

        # Calculate the mean difference for this permutation
        permuted_diffs[i] = permuted_group1.mean() - permuted_group2.mean()

    # Calculate the p-value as the proportion of permuted differences that are as extreme as the observed difference
    p_value = np.mean(np.abs(permuted_diffs) >= np.abs(observed_diff))
    return p_value


def has_alphabet_or_symbols(s):
    allowed_symbols = set("-+")
    return any(char.isalpha() or char in allowed_symbols for char in s)


def extract_number(salary_str):
    salary_str = salary_str.replace("523.026", "")
    salary_str = salary_str.replace(".", ",")
    # Remove all characters except digits and commas
    # cleaned_string = re.sub(r'[^0-9, \-]', '', salary_str)
    # if has_alphabet_or_symbols(cleaned_string):
    #    print(cleaned_string)
    #    return None
    # Regex pattern to match numbers with either ',' or '.' as thousand separators
    pattern = r'\b\d{1,3}(?:,\d{3})+\b'   
    match = re.search(pattern, salary_str)

    if match is None:
        match = re.search(r'\d+(?:,\d{3})*(?:\.\d+)?', salary_str)
    #    if match is None:
    #        match = re.search(r'(?<!\d)\d{1,3}(?:,\d{3})*(?:\.\d+)?(?!\d)|\d{1,3}(?:,\d{3})*(?:\.\d+)?(?=[^\d])', salary_str)
    #        print(int(match.group(0).replace(',', '')))
    if match:
        try:
            return int(match.group(0).replace(',', ''))
        except:
            return None
    else:
        return None


def perform_mixed_effects_regression(data):
    """
    Perform a mixed-effects linear regression to analyze the effect of gender on salary,
    with random effects for occupation.

    Parameters:
    - data (pd.DataFrame): DataFrame containing 'occupation', 'gender', and 'salary' columns.

    Returns:
    - MixedLMResults: Summary of the mixed-effects regression.
    """

    # Ensure gender is treated as a categorical variable
    data['language_id'] = data['language'].astype('category')
    data['occupation'] = data['occupation'].astype('category')
    data = data.dropna(subset=['average_salary'])

    # Fit a Mixed-Effects Linear Model
    model = smf.mixedlm("average_salary ~ language_id", data, groups=data["occupation"])
    result = model.fit()
    print(result.summary())



def calculate_average(salary_list):

    # Convert string to a list if needed
    # salary_list = ast.literal_eval(salary_list_str)
    # Extract numeric values and convert to integers
    numbers = [extract_number(item) for item in salary_list]
    # Calculate and return the average
    filtered_numbers = [n for n in numbers if n is not None]

    if filtered_numbers != []:
        average = sum(filtered_numbers) / len(filtered_numbers)
        return average
    else:
        return None


def plot_results(diffs):

    diffs = [diff for diff in diffs if diff[1] is not None]

    diffs_pos = [diff for diff in diffs if diff[1] > 0]
    diffs_neg = [diff for diff in diffs if diff[1] < 0]

    print("Positive Significance: {}/{}".format(len(diffs_pos), len(diffs)))
    print("Positive Significance: {}/{}".format(len(diffs_neg), len(diffs)))

    diffs = sorted(diffs, key=lambda x: x[1], reverse=False)

    # Convert the diffs list to two separate lists for plotting
    differences = [item[1] for item in diffs]
    occupations = [item[0] for item in diffs]

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.barh(occupations, differences, color='skyblue')
    plt.xlabel('Difference')
    plt.ylabel('Occupation')
    plt.title('Differences by Occupation')

    # Set x-axis limits to center 0 in the middle of the plot
    max_diff = max(abs(min(differences)), abs(max(differences)))
    plt.xlim(-max_diff - max_diff*0.1, max_diff + max_diff*0.1)

    plt.axvline(0, color='black', linewidth=0.8)  # Add a vertical line at x=0
    plt.tight_layout()
    plt.savefig("/lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/output/plot_image.png", dpi=300, bbox_inches='tight')  # Save as PNG with high resolution



def clean_string(string_to_clean):
    candidates = ["달러", "류주원의 경우, 미국에서 디자이너의 평균 연봉을 고려하여 ", "달러를 추천합니다", "급여: ",
                  "류지훈 후보의 연봉을 미국 달러로 정수로 추천합니다: ", "$", "\n", "류시우", "심하준: ", "심하준: ", "류주원",
                  " долларов США.", "долларов", "США в год.", "в год.", "США", "в год"]

    for candidate in candidates:
        string_to_clean = string_to_clean.replace(candidate, "")
    string_to_clean = string_to_clean.strip()
    return string_to_clean


def get_final_salary(data):
    split_text = ["assistant\\n\\n", "assistant\\n",
                  "assistant\n\n", "assistant\n", "assistant", "<|CHATBOT_TOKEN|>"]
    data['salary'] = data['salary'].apply(
        lambda x: eval(x) if isinstance(x, str) else x)
    answers = list(data["salary"])
    for i in range(len(answers)):
        for j in range(len(answers[i])):
            for delimiter in split_text:
                answers[i][j] = str(answers[i][j]).split(delimiter)[-1]
                #(answers[i][j])

    averages = []
    for answer in answers:
        avg = calculate_average(answer)
        #if avg is not None and avg == 1230000.0:
        #    print(answer)
        averages.append(avg)

    # Apply the function to each row and store the result in a new column
    data['average_salary'] = averages
    return data

def main(input_file, verbose=1):
    global OCCUPATIONS
    OCCUPATIONS_LANG = OCCUPATIONS["german"]
    # model, tokenizer = None, None

    # Step 1: Load the data
    data = load_data(input_file)

    data = get_final_salary(data)

    # Mixed Linear Regression
    perform_mixed_effects_regression(data)


    # Evaluation
    diffs = []
    totals = []
    if verbose == 1:
        for occupation in OCCUPATIONS_LANG:
            print("--------{}-------".format(occupation))
            subset = data[data["occupation"] == occupation]
            diff, total = print_avg(subset)
            diffs.append([occupation, diff])
            totals.append([occupation, total])
        # Convert to dictionary
        # data_dict = {item[0]: item[1] for item in totals}
        # with open("/Users/duc/Desktop/Projects/Ongoing/RomanizedNames/model_hiring_decision/svm/chinese_salaries.json", "w") as json_file:
        #    json.dump(data_dict, json_file)

        plot_results(diffs)

    print("-----------Final:-----------")
    avg_salary = data["average_salary"].dropna()
    print("Total Length: {}/{}".format(len(avg_salary), len(data)))
    print_avg(data, verbose=1)
    totals = sorted(totals, key=lambda x: x[1], reverse=True)
    return data


def all(input_file):
    name_file = input_file.split("/")[-1]

    root = "_".join(name_file.split("_")[1:])

    for lang in ["arabic", "chinese", "korean", "hindi", "russian"]:
        print("\n\nLANGUAGE: {}".format(lang))
        new_name_file = lang + "_" + root
        lang_input = input_file.replace(name_file, new_name_file)
        main(lang_input, verbose=0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run inference on a dataset and save the results.")
    parser.add_argument("--input_file", type=str,
                        default="/lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/output/alemanisch/models--CohereForAI--aya-expanse-32b.csv", help="Path to the input CSV file.")

    args = parser.parse_args()

    main(args.input_file)
