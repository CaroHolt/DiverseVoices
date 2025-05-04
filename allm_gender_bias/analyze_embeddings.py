from transformers import AutoModelForSpeechSeq2Seq, AutoFeatureExtractor, AutoProcessor, Qwen2AudioForConditionalGeneration, AutoTokenizer, AutoModel, AutoModelForCausalLM, Qwen2_5OmniModel, Wav2Vec2Model
import librosa
import torch
import pandas as pd

model_name_or_path = "Qwen/Qwen2-Audio-7B-Instruct"
cache_dir="/work/bbc6523/cache_dir"

#model = Qwen2AudioForConditionalGeneration.from_pretrained(
#            model_name_or_path,
#            use_safetensors=True,
#            trust_remote_code=True,
#            cache_dir = cache_dir,
#            output_hidden_states=True
#        ).to("cuda")      

model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-large-960h-lv60-self", 
                                      torch_dtype=torch.float16, 
                                      cache_dir = cache_dir,
                                      attn_implementation="flash_attention_2").to('cuda')

processor = AutoProcessor.from_pretrained(
            model_name_or_path, 
            trust_remote_code=True,
            cache_dir = cache_dir
            )

feature_extractor = AutoFeatureExtractor.from_pretrained("facebook/wav2vec2-base-960h")


df = pd.read_csv('synthetic_data.csv')

for index, row in df.iterrows():

    audio_array, sr = librosa.load('synthetic_audio/' + row['audio_file'], sr=processor.feature_extractor.sampling_rate)  # e.g., load and resample to 16kHz

    input_values = feature_extractor(sample["audio"]["array"], return_tensors="pt").input_values

    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True)
        embeddings = outputs.hidden_states[-1]
        print(embeddings)

    # Mean pooling across time
    audio_embedding = embeddings.mean(dim=1)  # shape: [1, embedding_dim]


