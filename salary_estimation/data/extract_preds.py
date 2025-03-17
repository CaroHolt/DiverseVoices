import os
import pandas as pd




if __name__ == "__main__":
    input_folder = "/lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/output"
    output_folder = "/lustre/project/ki-topml/minbui/repos/DialectSalary/salary_estimation/data/prompts/extraction"
    tasks = ["adjective", "profession", "location_usa", "degree"]

    for task in tasks:
        folder = os.path.join(input_folder, task)

        for file in os.listdir(folder):
            if file.endswith(".pkl"):  # Ensure it's a pickle file
                file_path = os.path.join(folder, file)
                df = pd.read_pickle(file_path)  # Load and store
                if task == "adjective":
                    prompt = "Extract the adjective that were explicitly mentioned. Text: '<TEXT>'. Only answer with the chosen adjective:"
                elif task == "profession":
                    prompt = "Extract the profession that were explicitly mentioned. Text: '<TEXT>'. Only answer with the chosen profession:"
                elif task == "location_usa":
                    prompt = "Extract the location that were explicitly mentioned. Text: '<TEXT>'. Only answer with the chosen location:"
                elif task == "degree":
                    prompt = "Extract the degree that were explicitly mentioned. Text: '<TEXT>'. Only answer with the chosen degree:"

                df["prompts"] = df.apply(lambda row: prompt.replace("<TEXT>", row["answer"][0]).replace("\n", ""), axis=1)

                os.makedirs(os.path.join(output_folder, task), exist_ok=True)

                file_path = os.path.join(output_folder, task, file)
                df.to_pickle(file_path)
                file_path = file_path.replace(".pkl", ".csv")
                df.to_csv(file_path)


