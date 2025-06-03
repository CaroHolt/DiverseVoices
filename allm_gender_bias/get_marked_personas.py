"""
Running this file obtains the words that distinguish a target group from the corresponding
unmarked ones.
Example usage: (To obtain the words that differentiate the 'Asian F' category)
python3 marked_words.py ../generated_personas.csv --target_val 'an Asian' F --target_col race gender --unmarked_val 'a White' M
"""

import pandas as pd
import numpy as np
from collections import Counter
import argparse
from collections import defaultdict
import math
import sys
import os


def get_log_odds(df1, df2, df0,verbose=False,lower=True):
    """Monroe et al. Fightin' Words method to identify top words in df1 and df2
    against df0 as the background corpus"""

    if lower:
        counts1 = defaultdict(int,[[i,j] for i,j in df1.str.lower().str.split(expand=True).stack().replace('[^a-zA-Z\s]','',regex=True).value_counts().items()])
        counts2 = defaultdict(int,[[i,j] for i,j in df2.str.lower().str.split(expand=True).stack().replace('[^a-zA-Z\s]','',regex=True).value_counts().items()])
        prior = defaultdict(int,[[i,j] for i,j in df0.str.lower().str.split(expand=True).stack().replace('[^a-zA-Z\s]','',regex=True).value_counts().items()])
    else:
        counts1 = defaultdict(int,[[i,j] for i,j in df1.str.split(expand=True).stack().replace('[^a-zA-Z\s]','',regex=True).value_counts().items()])
        counts2 = defaultdict(int,[[i,j] for i,j in df2.str.split(expand=True).stack().replace('[^a-zA-Z\s]','',regex=True).value_counts().items()])
        prior = defaultdict(int,[[i,j] for i,j in df0.str.split(expand=True).stack().replace('[^a-zA-Z\s]','',regex=True).value_counts().items()])
        

    sigmasquared = defaultdict(float)
    sigma = defaultdict(float)
    delta = defaultdict(float)

    for word in prior.keys():
        prior[word] = int(prior[word] + 0.5)

    for word in counts2.keys():
        counts1[word] = int(counts1[word] + 0.5)
        if prior[word] == 0:
            prior[word] = 1

    for word in counts1.keys():
        counts2[word] = int(counts2[word] + 0.5)
        if prior[word] == 0:
            prior[word] = 1

    n1 = sum(counts1.values())
    n2 = sum(counts2.values())
    nprior = sum(prior.values())
    
    for word in prior.keys():
        if prior[word] > 0:
        
            l1 = float(counts1[word] + prior[word]) / (( n1 + nprior ) - (counts1[word] + prior[word]))
            l2 = float(counts2[word] + prior[word]) / (( n2 + nprior ) - (counts2[word] + prior[word]))
            sigmasquared[word] =  1/(float(counts1[word]) + float(prior[word])) + 1/(float(counts2[word]) + float(prior[word]))
            sigma[word] =  math.sqrt(sigmasquared[word])
            delta[word] = ( math.log(l1) - math.log(l2) ) / sigma[word]

    if verbose:
        for word in sorted(delta, key=delta.get)[:10]:
            print("%s, %.3f" % (word, delta[word]))

        for word in sorted(delta, key=delta.get,reverse=True)[:10]:
            print("%s, %.3f" % (word, delta[word]))
    return delta




def marked_words_female(df_dimension, rest_texts,target_col):

    """Get words that distinguish the target group (which is defined as having 
    target_group_vals in the target_group_cols column of the dataframe) 
    from all unmarked_attrs (list of values that correspond to the categories 
    in unmarked_attrs)"""

    grams = dict()
    thr = 1.96 #z-score threshold

    for accent in df_dimension.accent.unique():

        
        subset = df_dimension[df_dimension['accent'] == accent]

        male_text =  subset[subset['gender'] == 'male'][target_col]
        female_text = subset[subset['gender'] == 'female'][target_col]

        delt = get_log_odds(female_text, male_text, rest_texts) #first one is the positive-valued one

        c1 = []
        c2 = []
        for k,v in delt.items():
            if v > thr:
                c1.append([k,v])
            elif v < -thr:
                c2.append([k,v])
        

        if 'target' in grams:
            grams['target'].extend(c1)
        else:
            grams['target'] = c1
        if accent in grams:
            grams[accent].extend(c2)
        else:
            grams[accent] = c2
    grams_refine = dict()
    

    for r in grams.keys():
        temp = []
        thr = len(df_dimension.accent.unique()) 
        for k,v in Counter([word for word, z in grams[r]]).most_common():
            if v >= thr:
                z_score_sum = np.sum([z for word, z in grams[r] if word == k])
                temp.append([k, z_score_sum])

        grams_refine[r] = temp
    return grams_refine['target']

def marked_words_male(df_dimension, rest_texts, target_col):

    """Get words that distinguish the target group (which is defined as having 
    target_group_vals in the target_group_cols column of the dataframe) 
    from all unmarked_attrs (list of values that correspond to the categories 
    in unmarked_attrs)"""

    grams = dict()
    thr = 1.96 #z-score threshold

    for accent in df_dimension.accent.unique():

        subset = df_dimension[df_dimension['accent'] == accent]

        male_text =  subset[subset['gender'] == 'male'][target_col]
        female_text = subset[subset['gender'] == 'female'][target_col]

        delt = get_log_odds(male_text, female_text, rest_texts) #first one is the positive-valued one

        c1 = []
        c2 = []
        for k,v in delt.items():
            if v > thr:
                c1.append([k,v])
            elif v < -thr:
                c2.append([k,v])
        

        if 'target' in grams:
            grams['target'].extend(c1)
        else:
            grams['target'] = c1
        if accent in grams:
            grams[accent].extend(c2)
        else:
            grams[accent] = c2
    grams_refine = dict()
    

    for r in grams.keys():
        temp = []
        thr = len(df_dimension.accent.unique()) 
        for k,v in Counter([word for word, z in grams[r]]).most_common():
            if v >= thr:
                z_score_sum = np.sum([z for word, z in grams[r] if word == k])
                temp.append([k, z_score_sum])

        grams_refine[r] = temp
    return grams_refine['target']


def main():
    parser = argparse.ArgumentParser(description="Just an example",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--decision_folder", default="output/british_dialects/", type=str, help="Generated personas file")
    parser.add_argument("--target_col", type=str, help="Which column to look at.")
    parser.add_argument("--unmarked_val", nargs="*",
    type=str,
    default=[''],help="List of unmarked default values for relevant demographic categories")
    parser.add_argument("--per_lang", default=False, type=bool, help="Do generate per dialect")
    parser.add_argument("--verbose", action='store_true',help="If set to true, prints out top words calculated by Fightin' Words")

    args = parser.parse_args()

    storage_path = '/work/bbc6523/diverse_voices/'

    rows = []
    for file in os.listdir(storage_path + args.decision_folder):
        print(file)

        df = pd.read_csv(storage_path + args.decision_folder + file)

        for accent in df.accent.unique():
            subset = df[df['accent'] == accent]
            rest_texts = df['model_response_reference_letter']#df['model_response_story']
        
            top_words = marked_words_female(subset, rest_texts, args.target_col)
            print("Top words:")
            print(top_words)
            for word, value in top_words:
                rows.append(['female', file[:-4] , accent, word, float(value)])
            
            top_words = marked_words_male(subset, rest_texts, args.target_col)
            print("Top words:")
            print(top_words)
            for word, value in top_words:
                rows.append(['male', file[:-4] , accent, word, float(value)])


    df_results = pd.DataFrame(rows, columns=["Target Group", "Model" , "Accent", "Word", "Value"])
    os.makedirs(os.path.dirname(args.decision_folder + 'eval/'), exist_ok=True)
    df_results['Value'] = df_results['Value'].round(2)
    df_results = df_results.sort_values(by=['Target Group', 'Model','Accent','Value'], ascending=False)
    df_results['Word+Value'] = df_results['Word'] + ' (' + df_results['Value'].astype(str) + '), '
    df_results.to_csv(args.decision_folder + 'marked_personas/results.csv' , index=False)
    grouped = df_results.groupby(["Target Group", "Model" , "Accent"])['Word+Value'].sum().reset_index()
    grouped.to_csv(args.decision_folder + 'marked_personas/results_grouped.csv' , index=False)




if __name__ == '__main__':
    
    main()

