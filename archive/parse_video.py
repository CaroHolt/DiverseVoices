import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from audio_extract import extract_audio




device = 'cuda:3'
torch_dtype=torch.float16

model_id = "openai/whisper-large-v3"

video_title='38 Different German Dialects_audio.mp4'

model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, use_safetensors=True, cache_dir='/work/bbc6523/cache_dir'
)

model.to(device)

processor = AutoProcessor.from_pretrained(model_id)


pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    chunk_length_s=30,
    torch_dtype=torch_dtype,
    device=device,
)


transcription = pipe(video_title, return_timestamps=True)

print(transcription)

#print(transcription["text"])


exit()

extract_audio(input_path="Regional German Dialects Comparedaudio.mp4", 
start_time="00:25",
              duration=15.0,
output_path="audio.mp3")

exit()
