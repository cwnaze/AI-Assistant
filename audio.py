import pyaudio
import wave
import os
from huggingface_hub import InferenceClient
import requests
from tempfile import NamedTemporaryFile
from playsound import playsound
from google.cloud import texttospeech

STT_URL = "https://api-inference.huggingface.co/models/openai/whisper-tiny.en"

token = "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"

headers = {"Authorization": f'Bearer {token}'}

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

            if "text" not in output:
                os.remove("temp_audio.wav")
                continue

            print(output["text"])
            
            if "hey robot" in output["text"].lower() or "hey, robot" in output["text"].lower():
                os.remove("temp_audio.wav")
                stream.stop_stream()
                stream.close()
                p.terminate()
                prompt_tts("what is it, sir")
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
            if "text" not in output or output["text"] == " you":
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
    result = ""
    client = InferenceClient(
        "meta-llama/Meta-Llama-3-8B-Instruct",
        token=token,
    )

    for message in client.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        stream=True,
    ):
        result += message.choices[0].delta.content

    prompt_tts(result)
    listen_ai()

def prompt_tts(prompt):
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=str(prompt))

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Standard-G",
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        speaking_rate=1
    )

    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice, "audio_config": audio_config}
    )

    # The response's audio_content is binary.
    with NamedTemporaryFile(delete=False, suffix='.wav') as f:
        f.write(response.audio_content)
        playsound(f.name)

listen_keyword()