import os
import platform
import subprocess
import requests
import speech_recognition as sr
from pydub import AudioSegment
from io import BytesIO
from elevenlabs import save
from elevenlabs.client import ElevenLabs

# ========== SETUP ==========
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")  # Or hardcode for testing
API_URL = "http://127.0.0.1:9999/chat"  # Your FastAPI backend
MODEL_NAME = "llama-3.3-70b-versatile"
PROVIDER = "Groq"
SYSTEM_PROMPT = "Act as a smart and friendly AI"
ALLOW_SEARCH = False


# ========== SPEECH TO TEXT ==========
def record_and_transcribe():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Speak now...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    print("🧠 Transcribing...")
    try:
        wav_data = audio.get_wav_data()
        audio_segment = AudioSegment.from_wav(BytesIO(wav_data))
        audio_segment.export("user_input.mp3", format="mp3")

        # Transcribe using Whisper via local or external model
        text = recognizer.recognize_google(audio)
        print(f"📝 You said: {text}")
        return text
    except Exception as e:
        print(f"❌ Error in transcription: {e}")
        return None


# ========== AI CHATBOT REQUEST ==========
def ask_ai_agent(user_text):
    payload = {
        "model_name": MODEL_NAME,
        "model_provider": PROVIDER,
        "system_prompt": SYSTEM_PROMPT,
        "messages": [user_text],
        "allow_search": ALLOW_SEARCH
    }
    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Failed to reach backend: {e}")


# ========== TEXT TO SPEECH ==========
def speak_with_elevenlabs(text, voice="Aria", output_path="response.mp3"):
    try:
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        audio = client.generate(
            text=text,
            voice=voice,
            output_format="mp3_22050_32",
            model="eleven_turbo_v2"
        )
        save(audio, output_path)

        # Play audio
        os_name = platform.system()
        if os_name == "Windows":
            subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{output_path}").PlaySync();'])
        elif os_name == "Darwin":
            subprocess.run(['afplay', output_path])
        elif os_name == "Linux":
            subprocess.run(['mpg123', output_path])
        else:
            print("⚠️ Unknown OS, cannot auto-play.")
    except Exception as e:
        print(f"❌ Error in TTS: {e}")


# ========== MAIN WORKFLOW ==========
def main():
    user_input = record_and_transcribe()
    if user_input:
        bot_response = ask_ai_agent(user_input)
        if bot_response:
            print(f"🤖 Bot says: {bot_response}")
            speak_with_elevenlabs(bot_response)


if __name__ == "__main__":
    main()
