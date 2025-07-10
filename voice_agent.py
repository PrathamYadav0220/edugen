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

# Predefined voice IDs (you can add more as needed)
VOICE_IDS = {
    "Rachel": "21m00Tcm4TlvDq8ikWAM",
    "Domi": "AZnzlk1XvdvUeBnXmlld",
    "Bella": "EXAVITQu4vr4xnSDxMaL",
    "Elli": "MF3mGyEYCl7XYWbV9V6O",
    "Adam": "pNInz6obpgDQGcFmaJgB",
    "Aria": "EXAVITQu4vr4xnSDxMaL"  # Default voice
}

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

        # Transcribe using Google Speech Recognition
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
            # Extract the response text
            response_data = response.json()
            return response_data.get("response", "")
        else:
            print(f"❌ Error: {response.text}")
            return ""
    except Exception as e:
        print(f"❌ Failed to reach backend: {e}")
        return ""


# ========== TEXT TO SPEECH ==========
def speak_with_elevenlabs(text, voice_name="Aria", output_path="response.mp3"):
    try:
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        
        # Get voice ID from name
        voice_id = VOICE_IDS.get(voice_name, VOICE_IDS["Aria"])
        
        # Generate audio with the new SDK syntax
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id="eleven_turbo_v2",
            text=text,
            output_format="mp3_22050_32"
        )
        
        # Save audio chunks to file
        with open(output_path, "wb") as f:
            for chunk in audio:
                if chunk:
                    f.write(chunk)

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
            
        return output_path
    except Exception as e:
        print(f"❌ Error in TTS: {e}")
        return None


# ========== MAIN WORKFLOW ==========
def main():
    user_input = record_and_transcribe()
    if user_input:
        bot_response = ask_ai_agent(user_input)
        if bot_response:
            print(f"🤖 Bot says: {bot_response}")
            # Use Rachel as the default voice
            audio_file = speak_with_elevenlabs(bot_response, voice_name="Rachel")
            if audio_file:
                print(f"🔊 Audio response saved to: {audio_file}")


if __name__ == "__main__":
    main()