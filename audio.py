import faster_whisper as whisper
import torch
import pyaudio
import wave
import os

def record_audio(p, stream, rec_seconds, rate, chunk):
    frames = []
    for _ in range(0, int(rate / chunk * rec_seconds)):
        data = stream.read(chunk, exception_on_overflow=False)
        frames.append(data)
    w = wave.open("temp_audio.wav", "wb")
    w.setnchannels(1)
    w.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    w.setframerate(16000)
    w.writeframes(b''.join(frames))
    w.close()

if __name__ == "__main__":
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024
    RECORD_SECONDS = 5

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_type = "tiny.en"

    model = whisper.WhisperModel(model_type, device=device, compute_type="int8")
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    try:
        while True:
            record_audio(p, stream, RECORD_SECONDS, RATE, CHUNK)
            segments, _ = model.transcribe("temp_audio.wav")
            segments = list(segments)
            
            for segment in segments:
                print(segment.text)

            os.remove("temp_audio.wav")

    except KeyboardInterrupt:
        stream.stop_stream()
        stream.close()
        p.terminate()
        os.remove("temp_audio.wav")
        print("Recording stopped")