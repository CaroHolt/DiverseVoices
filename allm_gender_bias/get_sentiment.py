from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F
import torch
import fire
import pandas as pd
from tqdm import tqdm




storage_path = '/p/project1/westai0056/code/DiverseVoices/allm_gender_bias/'

def main(
        # data parameters
        target_col: str,
        experiment: str,

        # model parameters
        modelname: str,
          
        batch_size:int,

        task:str

):
    if task == 'sentiment':
        model_name = "/p/project1/westai0056/code/cache_dir/models--distilbert-base-multilingual-cased-sentiments-student/snapshots/cf991100d706c13c0a080c097134c05b7f436c45" 
    elif task == 'emotion':
        model_name = "/p/project1/westai0056/code/cache_dir/models--ModernBERT-large-english-go-emotions/snapshots/e0d192593ee93435d5b8b38c0302ab594b1d8fe6"


    tokenizer  = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        torch_dtype=torch.float16          # half-precision to save VRAM (optional)
    ).to("cuda").eval()  

    df = pd.read_csv(storage_path + f'output/{experiment}/{modelname}.csv')
    target_cols = [f'model_response_{target_col}_prompt{i}' for i in range(3)]
    print(target_cols)


    if task == 'sentiment':
        print("Running sentiment")
        for col in target_cols:
            print(col)
            pos_vals = []
            neg_vals = []
            neut_vals = []
            texts = df[col].tolist()

            for i in tqdm(range(0, len(texts), batch_size)):
                text_batch = texts[i:i + batch_size]
                tokenized_batch = tokenizer(text_batch, padding=True, truncation=True, return_tensors="pt").to("cuda")
        

                with torch.no_grad():
                    logits = model(**tokenized_batch).logits
                    probs = F.softmax(logits, dim=-1)

                pos_vals.extend(probs[:, 0].cpu().tolist())   
                neut_vals.extend(probs[:, 1].cpu().tolist())  
                neg_vals.extend(probs[:, 2].cpu().tolist())   

            df = pd.read_csv(storage_path + f'output/{experiment}/{modelname}.csv') 
            df[f'{col}_pos'] = pos_vals
            df[f'{col}_neut'] = neut_vals
            df[f'{col}_neg'] = neg_vals
            df.to_csv(storage_path + f'output/{experiment}/{modelname}.csv', index=False) 
    
    elif task == 'emotion':
        print("Running emotions")
        for col in target_cols:
            print(col)
            texts = df[col].tolist()
            results = []

            for i in tqdm(range(0, len(texts), batch_size)):
                text_batch = texts[i:i + batch_size]
                tokenized_batch = tokenizer(text_batch, padding=True, truncation=True, return_tensors="pt").to("cuda")
        

                with torch.no_grad():
                    logits = model(**tokenized_batch).logits
                    probs = F.softmax(logits, dim=-1)


                results.extend(probs.cpu().tolist())   
                print(results)

            df = pd.read_csv(storage_path + f'output/{experiment}/{modelname}.csv') 
            df[f'{col}_emotion'] = results
            df.to_csv(storage_path + f'output/{experiment}/{modelname}.csv', index=False) 





if __name__ == "__main__":
    fire.Fire(main)