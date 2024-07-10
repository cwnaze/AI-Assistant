import pyaudio
import wave
import os
import requests
import requests
from tempfile import NamedTemporaryFile
from playsound import playsound

STT_URL = "https://api-inference.huggingface.co/models/openai/whisper-tiny.en"
LLM_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
TTS_URL = "https://api-inference.huggingface.co/models/facebook/mms-tts-eng"

headers = {"Authorization": "TOKEN HERE"}

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

def listen_keyword():
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024
    RECORD_SECONDS = 5

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    try:
        while True:
            record_audio(p, stream, RECORD_SECONDS, RATE, CHUNK)
            def query(filename):
                with open(filename, "rb") as f:
                    data = f.read()
                response = requests.post(STT_URL, headers=headers, data=data)
                return response.json()

            output = query("temp_audio.wav")
            print(output["text"])
            if "hey robot" in output["text"].lower() or "hey, robot" in output["text"].lower():
                os.remove("temp_audio.wav")
                stream.stop_stream()
                stream.close()
                p.terminate()
                listen_ai()
                break
            os.remove("temp_audio.wav")

    except KeyboardInterrupt:
        stream.stop_stream()
        stream.close()
        p.terminate()
        os.remove("temp_audio.wav")
        print("Recording stopped")

def listen_ai():
    print("ai is listening now")
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024
    RECORD_SECONDS = 5
    
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    prompt = ""

    try:
        while True:
            record_audio(p, stream, RECORD_SECONDS, RATE, CHUNK)
            def query(filename):
                with open(filename, "rb") as f:
                    data = f.read()
                response = requests.post(STT_URL, headers=headers, data=data)
                return response.json()

            output = query("temp_audio.wav")
            if output["text"] == " you":
                os.remove("temp_audio.wav")
                stream.stop_stream()
                stream.close()
                p.terminate()
                prompt_llm(prompt)
                break
            print(output["text"])
            prompt += output["text"] + " "
            os.remove("temp_audio.wav")

    except KeyboardInterrupt:
        stream.stop_stream()
        stream.close()
        p.terminate()
        os.remove("temp_audio.wav")
        print("Recording stopped")

def prompt_llm(prompt):
    def query(payload):
        response = requests.post(LLM_URL, headers=headers, json=payload)
        return response.json()
	
    output = query({
	    "inputs": f'You are a helpful and honest assistant. Please, respond concisely and truthfully. {prompt}',
    })

    print(output[0].get("generated_text"))
    prompt_tts(output[0].get("generated_text"))

def prompt_tts(prompt):
    def query(payload):
        response = requests.post(TTS_URL, headers=headers, json=payload)
        return response.content

    audio_bytes = query({
        "inputs": prompt,
    })

    with NamedTemporaryFile(delete=False, suffix='.wav') as f:
        f.write(audio_bytes)
        playsound(f.name)

listen_keyword()