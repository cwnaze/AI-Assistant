import faster_whisper as whisper
import torch

device="cuda" if torch.cuda.is_available() else "cpu"
model_type="tiny.en"

model = whisper.WhisperModel(model_type, device=device, compute_type="int8")
segments, _ = model.transcribe("test.mp3")
segments = list(segments)

for segment in segments:
    print(segment.text)
