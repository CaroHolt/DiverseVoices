import soundfile as sf
from transformers import AutoModelForCausalLM, AutoProcessor, GenerationConfig, AutoModelForSpeechSeq2Seq
import librosa

file_path = '/work/bbc6523/diverse_voices/synthetic_audio/1_english_american_m.mp3'


repo_id = "MERaLiON/MERaLiON-AudioLLM-Whisper-SEA-LION"

processor = AutoProcessor.from_pretrained(
    repo_id, 
    trust_remote_code=True,
    )
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    repo_id,
    use_safetensors=True,
    trust_remote_code=True,
    cache_dir = "/work/bbc6523/cache_dir"
)

prompt = "Given the following audio context: <SpeechHere>\n\nText instruction: {query}"
transcribe_query = "Please transcribe this speech."
translate_query = "Can you please translate this speech into written Chinese?"

conversation = [
    [{"role": "user", "content": prompt.format(query=transcribe_query)}],
    [{"role": "user", "content": prompt.format(query=translate_query)}],
]

chat_prompt = processor.tokenizer.apply_chat_template(
    conversation=conversation,
    tokenize=False,
    add_generation_prompt=True
)

# Use an audio within 30 seconds, 16000hz.
audio_array, sample_rate = librosa.load(file_path, sr=16000)
audio_array = [audio_array]*2
inputs = processor(text=chat_prompt, audios=audio_array)

outputs = model.generate(**inputs, max_new_tokens=256, do_sample=True, temperature=0.1, repetition_penalty=1.1, top_p=0.9, no_repeat_ngram_size=6)
generated_ids = outputs[:, inputs['input_ids'].size(1):]
response = processor.batch_decode(generated_ids, skip_special_tokens=True)
