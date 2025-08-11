tasks = ['adjectives_masc_fem', 'adjectives_dimensions']


def parse_dimensions(row, task):
    male_dims = 0
    female_dims = 0
    for col in [f'model_response_{task}_prompt0', f'model_response_{task}_prompt1', f'model_response_{task}_prompt2']:
        if task == 'adjectives_masc_fem':
            for adj in ADJECTIVES_MASC_FEM['masculine']:
                if adj.lower() in row[col].lower():
                    male_dims+=1
                    break
            for adj in ADJECTIVES_MASC_FEM['feminine']:
                if adj.lower() in row[col].lower():
                    female_dims+=1
                    break
        elif task == 'adjectives_dimensions':
            for adj in ADJECTIVES_DIMENSIONS['agentic']:
                if adj.lower() in row[col].lower():
                    male_dims+=1
                    break
            for adj in ADJECTIVES_DIMENSIONS['communal']:
                if adj.lower() in row[col].lower():
                    female_dims+=1
                    break
    return pd.Series([male_dims, female_dims, 3-male_dims-female_dims])


all_rows = []
for task in tasks: 
    for model in os.listdir(storage_path + 'output/full_diverse_voices'):
        row = {}
        print(model)
        df = pd.read_csv(storage_path + 'output/full_diverse_voices/' + model)
        
        df[['matched_male','matched_female', 'no_match']] = df.apply(lambda row: parse_dimensions(row, task), axis=1)
        row['model'] = model[:-4]
        row['topic'] = task
        subset = df[['gender','matched_male','matched_female', 'no_match']].groupby('gender').sum().reset_index()
        male_attr_male = subset[subset['gender'] == 'male']['matched_male'].iloc[0]
        male_attr_female = subset[subset['gender'] == 'female']['matched_male'].iloc[0]
        female_attr_male = subset[subset['gender'] == 'male']['matched_female'].iloc[0]
        female_attr_female = subset[subset['gender'] == 'female']['matched_female'].iloc[0]
        bias_score = (male_attr_male - male_attr_female) + (female_attr_female - female_attr_male)
        total = male_attr_male + male_attr_female + female_attr_male + female_attr_female
        normalized_score = bias_score / total
        print('Bias Score: ' + str(normalized_score))
        print()
        table = np.array([[male_attr_male, female_attr_male], [male_attr_female, female_attr_female]])
        #print(table)
        # Chi-square test
        chi2, p, dof, expected = chi2_contingency(table)
        print(f"\nChi-square = {chi2:.3f}, p-value = {p:.4f}")
        row['Chi-square'] = round(chi2,4)
        row['p-value'] = round(p,4)
        all_rows.append(row)

results_df = pd.DataFrame(all_rows)
file_name = 'p_values_adjectives_per_model.csv'
if os.path.exists(file_name):
    df = pd.read_csv(file_name)
    df = pd.concat([df, results_df])
else:
    df = results_df.copy()
df.to_csv(file_name, index=False)



all_rows = []
for task in tasks: 
    for model in os.listdir(storage_path + 'output/full_diverse_voices'):
        
        
        print(model)
        df = pd.read_csv(storage_path + 'output/full_diverse_voices/' + model)
        for source in df.source.unique():
            row = {}
            df_copy = df[df['source'] == source].copy()
            df_copy[['matched_male','matched_female', 'no_match']] = df_copy.apply(lambda row: parse_dimensions(row, task), axis=1)
            row['model'] = model[:-4]
            row['topic'] = task
            row['source'] = source
            subset = df_copy[['gender','matched_male','matched_female', 'no_match']].groupby('gender').sum().reset_index()
            male_attr_male = subset[subset['gender'] == 'male']['matched_male'].iloc[0]
            male_attr_female = subset[subset['gender'] == 'female']['matched_male'].iloc[0]
            female_attr_male = subset[subset['gender'] == 'male']['matched_female'].iloc[0]
            female_attr_female = subset[subset['gender'] == 'female']['matched_female'].iloc[0]
            bias_score = (male_attr_male - male_attr_female) + (female_attr_female - female_attr_male)
            total = male_attr_male + male_attr_female + female_attr_male + female_attr_female
            normalized_score = bias_score / total
            print('Bias Score: ' + str(normalized_score))
            print()
            table = np.array([[male_attr_male, female_attr_male], [male_attr_female, female_attr_female]])
            #print(table)
            # Chi-square test
            chi2, p, dof, expected = chi2_contingency(table)
            print(f"\nChi-square = {chi2:.3f}, p-value = {p:.4f}")
            row['Chi-square'] = round(chi2,4)
            row['p-value'] = round(p,4)
            all_rows.append(row)

results_df = pd.DataFrame(all_rows)
file_name = 'p_values_adjectives_per_data_set.csv'
if os.path.exists(file_name):
    df = pd.read_csv(file_name)
    df = pd.concat([df, results_df])
else:
    df = results_df.copy()
df.to_csv(file_name, index=False)

# ------------------------------------------------------------
# Compute adjusted p-values with Bonferroni, Holm and BH (FDR)
# ------------------------------------------------------------

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

df = pd.read_csv('p_values_adjectives_per_model.csv')
for model in df.model.unique():
    print(model)
    raw_p = df[df['model'] == model]['p-value'].tolist()

    bonf  = multipletests(raw_p, method="bonferroni")[1]     # returns array of adj p
    holm  = multipletests(raw_p, method="holm")[1]
    bh    = multipletests(raw_p, method="fdr_bh")[1]


    results = pd.DataFrame({
        "test": df[df['model'] == model]['topic'].tolist(),
        "chi2":   df[df['model'] == model]['Chi-square'].tolist(),
        "raw":        raw_p,
        "Bonferroni": bonf,
        "Holm":       holm,
        "BH_FDR":     bh,
    }).round(3)

    print(results)
    print()
