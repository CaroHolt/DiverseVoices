import librosa
import numpy as np
import soundfile as sf
import pandas as pd


df = pd.read_csv('/work/bbc6523/diverse_voices/data/british_dialects.csv')

print(df.columns)
new_df = []
for accent in df.accent.unique():
    subset_male = df[(df['accent'] == accent) & (df['gender'] == 'male')]
    subset_female = df[(df['accent'] == accent) & (df['gender'] == 'female')]

    if set(subset_male['line_id'].tolist()) != set(subset_female['line_id'].tolist()):
        print('NOT THE SAME')
    else: 
        for id in subset_male['line_id'].unique():
            # Load MP3 files using librosa (automatically resamples)
            y1, sr1 = librosa.load(subset_male[subset_male['line_id'] == id]['audio_file'].iloc[0], sr=None)
            y2, sr2 = librosa.load(subset_female[subset_female['line_id'] == id]['audio_file'].iloc[0], sr=None)

            # Ensure same sample rate (or resample manually)
            assert sr1 == sr2, "Sample rates must match"

            # Create 2 seconds of silence
            pause_duration_sec = 2
            pause = np.zeros(int(sr1 * pause_duration_sec))

            # Concatenate audio: file1 + pause + file2
            joined = np.concatenate([y1, pause, y2])

            # Save as WAV
            file_name = f'/work/bbc6523/diverse_voices/british_dialects_audio/british_dialects_compare/{accent}_male_female_{id}.wav'
            sf.write(file_name, joined, sr1)

            row1 = {}

            row1['line_id'] = id
            row1['text'] = subset_male[subset_male['line_id'] == id]['text'].iloc[0]
            row1['audio_file'] = file_name
            row1['accent'] = accent
            row1['comparison'] = 'gender'
            row1['gender_order'] = 'male-female'

            new_df.append(row1)

            row2 = row1.copy()

            # Concatenate audio: file1 + pause + file2
            joined = np.concatenate([y2, pause, y1])

            # Save as WAV
            file_name = f'/work/bbc6523/diverse_voices/british_dialects_audio/british_dialects_compare/{accent}_female_male_{id}.wav'
            sf.write(file_name, joined, sr1)

            row2['audio_file'] = file_name
            row2['gender_order'] = 'female-male'

            new_df.append(row2)

full = pd.DataFrame(new_df)

full.to_csv('british_dialect_compare.csv')









exit()


subset_english = df[df['accent'] == 'american'].copy()
subset_rest = df[~(df['accent'] == 'american')].copy()

new_df = []
for index, row in subset_rest.iterrows():
    row1 = {}

    english_id = row['index']
    print(english_id)

    # Load MP3 files using librosa (automatically resamples)
    y1, sr1 = librosa.load(storage_path + str(english_id) + "_english_american_m.mp3", sr=None)
    y2, sr2 = librosa.load(storage_path + row['audio_file'].replace(' ', '_'), sr=None)

    # Ensure same sample rate (or resample manually)
    assert sr1 == sr2, "Sample rates must match"

    # Create 2 seconds of silence
    pause_duration_sec = 2
    pause = np.zeros(int(sr1 * pause_duration_sec))

    # Concatenate audio: file1 + pause + file2
    joined = np.concatenate([y1, pause, y2])

    # Save as WAV
    file_name = str(english_id) + '_american_' + row['accent'].replace(' ', '_') + '_m.wav'
    #sf.write(file_name, joined, sr1)

    row1['index'] = english_id
    row1['text'] = row['text']
    row1['audio_file'] = file_name
    row1['accent'] = 'american-' + row['accent']
    row1['comparison'] = 'dialect'

    new_df.append(row1)

    row2 = row1.copy()

    # Concatenate audio: file1 + pause + file2
    joined = np.concatenate([y2, pause, y1])

    # Save as WAV
    file_name = str(english_id) + '_' + row['accent'].replace(' ', '_') + '_american'+ '_m.wav'
    #sf.write(file_name, joined, sr1)

    row2['audio_file'] = file_name
    row2['accent'] = row['accent'] + '-american'
    new_df.append(row2)
    

my_df = pd.DataFrame(new_df)

new_df = []
for index in ['1', '2', '3', '4', '5', '6', '7','8','9', '10']:
    # Load MP3 files using librosa (automatically resamples)
    y1, sr1 = librosa.load( storage_path + index+ "_english_american_m.mp3", sr=None)
    y2, sr2 = librosa.load( storage_path + index+ "_english_american_f.mp3", sr=None)

    # Ensure same sample rate (or resample manually)
    assert sr1 == sr2, "Sample rates must match"

    # Create 2 seconds of silence
    pause_duration_sec = 2
    pause = np.zeros(int(sr1 * pause_duration_sec))

    # Concatenate audio: file1 + pause + file2
    joined = np.concatenate([y1, pause, y2])

    # Save as WAV
    file_name = index + '_american_male_female.wav'
    sf.write(file_name, joined, sr1)

    row1 = {}

    row1['index'] = index
    row1['text'] = df[df['index'] == index]['text'].iloc[0]
    row1['audio_file'] = file_name
    row1['accent'] = 'american'
    row1['comparison'] = 'gender'
    row1['gender_order'] = 'male-female'

    new_df.append(row1)

    row2 = row1.copy()

    # Concatenate audio: file1 + pause + file2
    joined = np.concatenate([y2, pause, y1])

    # Save as WAV
    file_name = index + '_american_female_male.wav'
    sf.write(file_name, joined, sr1)

    row2['audio_file'] = file_name
    row2['gender_order'] = 'female-male'

    new_df.append(row2)

my_df2 = pd.DataFrame(new_df)

full = pd.concat([my_df, my_df2])


full.to_csv('synthetic_compare_dataset_2.csv', index=False)

exit()

storage_path = '/work/bbc6523/diverse_voices/synthetic_audio/'


for index in ['1', '2', '3', '4', '5', '6', '7','8','9', '10']:
    # Load MP3 files using librosa (automatically resamples)
    y1, sr1 = librosa.load( storage_path + index+ "_english_american_m.mp3", sr=None)
    y2, sr2 = librosa.load( storage_path + index+ "_english_american_f.mp3", sr=None)

    # Ensure same sample rate (or resample manually)
    assert sr1 == sr2, "Sample rates must match"

    # Create 2 seconds of silence
    pause_duration_sec = 2
    pause = np.zeros(int(sr1 * pause_duration_sec))

    # Concatenate audio: file1 + pause + file2
    joined = np.concatenate([y1, pause, y2])

    # Save as WAV
    file_name = index + '_male_female.wav'
    sf.write(file_name, joined, sr1)










exit()


