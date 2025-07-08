# if you dont use pipenv uncomment the following:
from dotenv import load_dotenv
load_dotenv()

import os
import platform
import requests
import streamlit as st
import speech_recognition as sr
from io import BytesIO
from pydub import AudioSegment
from elevenlabs import save
from elevenlabs.client import ElevenLabs
import uuid
import json
import base64  # Added for PDF handling

# Initialize session state
if "user_query" not in st.session_state:
    st.session_state["user_query"] = ""
if "last_audio_path" not in st.session_state:
    st.session_state["last_audio_path"] = None
if "last_response" not in st.session_state:
    st.session_state["last_response"] = ""
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "language" not in st.session_state:
    st.session_state["language"] = "en-US"
if "voice" not in st.session_state:
    st.session_state["voice"] = "Rachel"  # Better default for multilingual

# ========== ElevenLabs Setup ==========
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# ========== Page Layout ==========
st.set_page_config(page_title="LangGraph Voice AI", layout="centered")
st.title("🎤 EDU-GEN Chatbot with Voice")
st.write("Talk with the agent using voice or text!")

# ========== AI Options ==========
system_prompt = st.text_area("🧠 Define your AI Agent: ", height=70, 
                            placeholder="Type your system prompt here...",
                            value="You are a helpful AI assistant. Respond in the user's language.")

# ========== Language and Voice Selection ==========
LANGUAGES = {
    "English": "en-US",
    "Hindi": "hi-IN",
    "Bengali": "bn-IN",
    "Marathi": "mr-IN",
    "Tamil": "ta-IN",
    "Telugu": "te-IN",
    "Gujarati": "gu-IN",
    "Kannada": "kn-IN",
    "Malayalam": "ml-IN",
    "Punjabi": "pa-IN",
    "Urdu": "ur-IN",
    "Spanish": "es-ES",
    "French": "fr-FR",
    "German": "de-DE",
    "Italian": "it-IT",
    "Portuguese": "pt-BR",
    "Japanese": "ja-JP",
    "Chinese": "zh-CN",
    "Arabic": "ar-SA"
}

# Voice mapping for better regional pronunciation
VOICE_MAPPING = {
    "hi-IN": ["Rachel", "Domi", "Bella"],
    "bn-IN": ["Rachel", "Domi"],
    "mr-IN": ["Rachel", "Elli"],
    "ta-IN": ["Rachel", "Adam"],
    "te-IN": ["Rachel", "Adam"],
    "gu-IN": ["Rachel", "Domi"],
    "kn-IN": ["Rachel", "Adam"],
    "ml-IN": ["Rachel", "Elli"],
    "pa-IN": ["Rachel", "Domi"],
    "ur-IN": ["Rachel", "Adam"],
    "en-US": ["Aria", "Rachel", "Domi"],
    "es-ES": ["Rachel", "Domi"],
    "fr-FR": ["Rachel", "Domi"],
    "de-DE": ["Rachel", "Domi"],
    "it-IT": ["Rachel", "Domi"],
    "pt-BR": ["Rachel", "Domi"],
    "ja-JP": ["Rachel", "Domi"],
    "zh-CN": ["Rachel", "Domi"],
    "ar-SA": ["Rachel", "Domi"]
}

selected_language = st.selectbox("🌐 Select Language:", list(LANGUAGES.keys()))
st.session_state["language"] = LANGUAGES[selected_language]

# Voice selection based on language
if st.session_state["language"] in VOICE_MAPPING:
    voice_options = VOICE_MAPPING[st.session_state["language"]]
    selected_voice = st.selectbox("🗣️ Select Voice:", voice_options)
    st.session_state["voice"] = selected_voice

MODEL_NAMES_GROQ = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]
MODEL_NAMES_OPENAI = ["gpt-4o-mini"]

provider = st.radio("Select Provider:", ("Groq", "OpenAI"))

if provider == "Groq":
    selected_model = st.selectbox("Select Groq Model:", MODEL_NAMES_GROQ)
elif provider == "OpenAI":
    selected_model = st.selectbox("Select OpenAI Model:", MODEL_NAMES_OPENAI)

allow_web_search = st.checkbox("Allow Web Search")
API_URL = "http://127.0.0.1:9999/chat"
QUIZ_URL = "http://127.0.0.1:9999/generate_quiz"  # Added quiz endpoint

# ========== Voice Recording ==========
def record_audio(timeout=10):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Listening... Speak now!")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=timeout)
        wav_data = audio.get_wav_data()
        audio_segment = AudioSegment.from_wav(BytesIO(wav_data))
        
        unique_id = uuid.uuid4().hex
        audio_filename = f"user_input_{unique_id}.mp3"
        audio_segment.export(audio_filename, format="mp3")
        
        try:
            # Use the selected language for recognition
            query = recognizer.recognize_google(audio, language=st.session_state["language"])
            return query
        except sr.UnknownValueError:
            st.error("❌ Could not understand audio")
            return ""
        except sr.RequestError as e:
            st.error(f"❌ Speech recognition error: {e}")
            return ""

# ========== Voice Output ==========
def speak_response_with_elevenlabs(text):
    try:
        unique_id = uuid.uuid4().hex
        output_path = f"response_{unique_id}.mp3"
        
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        
        # Use multilingual model for non-English languages
        model_name = "eleven_multilingual_v2" if st.session_state["language"] != "en-US" else "eleven_turbo_v2"
        
        # Add language-specific pronunciation hints
        pronunciation_text = text
        if st.session_state["language"] == "hi-IN":
            pronunciation_text = f"(Hindi pronunciation){text}"
        elif st.session_state["language"] == "ta-IN":
            pronunciation_text = f"(Tamil pronunciation){text}"
        elif st.session_state["language"] == "mr-IN":
            pronunciation_text = f"(Marathi pronunciation){text}"
        elif st.session_state["language"] == "bn-IN":
            pronunciation_text = f"(Bengali pronunciation){text}"
        
        audio = client.generate(
            text=pronunciation_text,
            voice=st.session_state["voice"],
            model=model_name,
            output_format="mp3_22050_32"
        )
        save(audio, output_path)
        
        # Save to session state
        st.session_state["last_audio_path"] = output_path
        st.session_state["last_response"] = text
        
        # Display audio player
        audio_file = open(output_path, "rb")
        audio_bytes = audio_file.read()
        st.audio(audio_bytes, format="audio/mp3")
        
        return output_path
        
    except Exception as e:
        st.error(f"❌ TTS Error: {e}")
        return None

# ========== Display Chat History ==========
st.subheader("💬 Chat History")
if st.session_state["chat_history"]:
    for idx, message in enumerate(st.session_state["chat_history"]):
        with st.expander(f"Conversation {idx + 1}", expanded=False):
            st.json(message, expanded=False)
            
            # Add replay button for each audio response
            if "audio_path" in message and message["audio_path"]:
                if st.button(f"🔊 Replay Audio {idx + 1}", key=f"replay_{idx}"):
                    st.audio(message["audio_path"], format="audio/mp3")

# ========== User Input Options ==========
use_voice = st.toggle("🎤 Use Microphone Input")
use_tts = st.toggle("🔊 Use Voice Output (ElevenLabs)")

if use_voice:
    if st.button("Record Voice and Ask"):
        try:
            query = record_audio()
            st.session_state["user_query"] = query
            st.success(f"🗣️ You said: {query}")
        except Exception as e:
            st.session_state["user_query"] = ""
            st.error(f"❌ Voice input failed: {e}")
else:
    st.session_state["user_query"] = st.text_area("💬 Type your query: ", 
                                                 height=150, 
                                                 placeholder="Ask Anything!",
                                                 value=st.session_state["user_query"])

# ========== Ask AI Agent ==========
# ... (previous imports and setup) ...

# ========== Ask AI Agent ==========
if st.button("Ask Agent!"):
    user_query = st.session_state["user_query"]

    if user_query and user_query.strip():
        payload = {
            "model_name": selected_model,
            "model_provider": provider,
            "system_prompt": system_prompt,
            "messages": [user_query],
            "allow_search": allow_web_search,
            "language": st.session_state["language"]  # Send language to backend
        }

        with st.spinner("🤖 Getting response..."):
            response = requests.post(API_URL, json=payload)

        if response.status_code == 200:
            response_data = response.json()
            
            # Handle response format
            if isinstance(response_data, dict):
                if "error" in response_data:
                    st.error(response_data["error"])
                    response_text = response_data["error"]
                elif "response" in response_data:
                    response_text = response_data["response"]
                else:
                    response_text = str(response_data)
            else:
                response_text = str(response_data)
            
            st.subheader("Agent Response")
            st.markdown(f"**💡 Response:** {response_text}")
            
            audio_path = None
            if use_tts:
                audio_path = speak_response_with_elevenlabs(response_text)
            
            # Add to chat history
            chat_entry = {
                "user_query": user_query,
                "agent_response": response_text,
                "audio_path": audio_path,
                "timestamp": st.session_state.get("timestamp", ""),
                "language": st.session_state["language"],
                "model": f"{provider} - {selected_model}",
                "voice": st.session_state["voice"]
            }
            
            st.session_state["chat_history"].append(chat_entry)
            
            # Store the response for quiz generation
            st.session_state["last_response"] = response_text
            
        else:
            st.error(f"❌ Failed to reach chatbot backend (Status {response.status_code})")
    else:
        st.warning("⚠️ Please enter a query or record your voice.")

# ... (previous code) ...

# ======== QUIZ GENERATION SECTION ======== 
if st.session_state.get("last_response"):
    st.divider()
    st.subheader("📚 Quiz Generator")
    st.write("Generate a quiz based on the last agent response")
    
    # Initialize quiz state
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = None
    
    if st.button("📝 Generate Quiz on this Topic"):
        with st.spinner("🧠 Creating quiz..."):
            payload = {
                "topic": st.session_state["last_response"],
                "language": st.session_state["language"],
                "model_name": selected_model,
                "model_provider": provider
            }
            quiz_response = requests.post(QUIZ_URL, json=payload)
            
            if quiz_response.status_code == 200:
                quiz_data = quiz_response.json()
                st.session_state.quiz_data = quiz_data
                st.success("✅ Quiz generated successfully! Download using buttons below.")
            else:
                st.error(f"❌ Quiz generation failed: {quiz_response.text}")
    
    # Show download buttons if quiz data exists
    if st.session_state.quiz_data:
        # Create download buttons
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download Quiz with Answers",
                data=base64.b64decode(st.session_state.quiz_data["quiz_with_answers"]),
                file_name="quiz_with_answers.pdf",
                mime="application/pdf"
            )
        with col2:
            st.download_button(
                label="Download Quiz Questions",
                data=base64.b64decode(st.session_state.quiz_data["quiz_questions"]),
                file_name="quiz_questions.pdf",
                mime="application/pdf"
            )
        
        # Optional: Show quiz preview
        if st.checkbox("Show Quiz Preview"):
            st.subheader("Quiz Preview")
            quiz_items = st.session_state.quiz_data.get("quiz_data", [])
            for idx, item in enumerate(quiz_items):
                st.markdown(f"**Q{idx+1}: {item.get('question', '')}**")
                options = item.get('options', [])
                for i, option in enumerate(options):
                    st.markdown(f"{chr(65+i)}. {option}")
                st.markdown(f"**Answer:** {item.get('answer', '')}")
                st.markdown(f"*Explanation:* {item.get('explanation', '')}")
                st.divider()