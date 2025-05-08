import os
import shutil

# Define main folder path
main_folder = '/lustre/project/ki-topml/minbui/repos/DialectSalary/llm_dialect_bias/output'

# Mapping of current file names to new names
mapping = {
    'c1df2547e1f5fe22e1f4897f980f231dc74cfc27.csv': 'aya-expanse-32b.csv',
    'c1df2547e1f5fe22e1f4897f980f231dc74cfc27.pkl': 'aya-expanse-32b.pkl',
    # Add more mappings as needed
}

# Function to rename CSV files
def rename_csv_files(folder_path, mapping):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.csv') or file.endswith('.pkl'):
                old_name = os.path.join(root, file)
                if file in mapping:
                    new_name = os.path.join(root, mapping[file])
                    try:
                        shutil.move(old_name, new_name)
                        print(f'Renamed "{old_name}" to "{new_name}"')
                    except Exception as e:
                        print(f'Error renaming "{old_name}": {e}')

# Call the function for each subfolder in main_folder
for folder in os.listdir(main_folder):
    folder_path = os.path.join(main_folder, folder)
    if os.path.isdir(folder_path):
        rename_csv_files(folder_path, mapping)
