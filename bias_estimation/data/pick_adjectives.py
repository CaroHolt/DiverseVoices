import pandas as pd
import numpy as np


df = pd.read_csv("/lustre/project/ki-topml/minbui/repos/DialectSalary/bias_estimation/data/filtered_valence_adjectives.csv")

print(df)
df_sorted = df.sort_values(by='arousal')
indices = np.linspace(0, len(df_sorted) - 1, 100, dtype=int)  # 100 evenly spaced indices
df_sampled = df_sorted.iloc[indices]

print(list(df_sampled["word"]))