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
from elevenlabs.client import ElevenLabs
import uuid
import json
import base64
import time
from datetime import datetime

# Voice ID mapping (replace with your actual voice IDs)
VOICE_IDS = {
    "Rachel": "21m00Tcm4TlvDq8ikWAM",
    "Domi": "AZnzlk1XvdvUeBnXmlld",
    "Bella": "EXAVITQu4vr4xnSDxMaL",
    "Elli": "MF3mGyEYCl7XYWbV9V6O",
    "Adam": "pNInz6obpgDQGcFmaJgB",
    "Aria": "EXAVITQu4vr4xnSDxMaL"
}

# ========== Helper Functions ==========
def record_audio(timeout=10):
    """Record audio from microphone"""
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
            query = recognizer.recognize_google(audio, language=st.session_state["language"])
            return query
        except sr.UnknownValueError:
            st.error("❌ Could not understand audio")
            return ""
        except sr.RequestError as e:
            st.error(f"❌ Speech recognition error: {e}")
            return ""

def speak_response_with_elevenlabs(text):
    """Generate speech from text using ElevenLabs"""
    try:
        unique_id = uuid.uuid4().hex
        output_path = f"response_{unique_id}.mp3"
        
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        
        model_id = "eleven_multilingual_v2" if st.session_state["language"] != "en-US" else "eleven_turbo_v2"
        
        pronunciation_text = text
        if st.session_state["language"] == "hi-IN":
            pronunciation_text = f"(Hindi pronunciation){text}"
        elif st.session_state["language"] == "ta-IN":
            pronunciation_text = f"(Tamil pronunciation){text}"
        elif st.session_state["language"] == "mr-IN":
            pronunciation_text = f"(Marathi pronunciation){text}"
        elif st.session_state["language"] == "bn-IN":
            pronunciation_text = f"(Bengali pronunciation){text}"
        
        # Get voice ID from name
        voice_name = st.session_state["voice"]
        voice_id = VOICE_IDS.get(voice_name, VOICE_IDS["Rachel"])  # Fallback to Rachel
        
        # Generate audio with the new SDK syntax
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id=model_id,
            text=pronunciation_text,
            output_format="mp3_22050_32"
        )
        
        # Save audio chunks to file
        with open(output_path, "wb") as f:
            for chunk in audio:
                if chunk:
                    f.write(chunk)
        
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
    st.session_state["voice"] = "Rachel"
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "show_convai" not in st.session_state:
    st.session_state.show_convai = False

# ========== ElevenLabs Setup ==========
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# ========== Custom CSS for Professional Look ==========
def load_custom_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    /* Main app styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Poppins', sans-serif;
    }
    
    /* Title styling */
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        animation: fadeInDown 1s ease-out;
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: #e1e8ff;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    
    /* Card styling */
    .custom-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.18);
        backdrop-filter: blur(10px);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #ff6b6b, #ee5a24);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
    }
    
    /* Primary button variant */
    .primary-button {
        background: linear-gradient(45deg, #4ecdc4, #44a08d) !important;
        box-shadow: 0 4px 15px rgba(78, 205, 196, 0.3) !important;
    }
    
    /* Voice button */
    .voice-button {
        background: linear-gradient(45deg, #a8e6cf, #7fcdcd) !important;
        box-shadow: 0 4px 15px rgba(168, 230, 207, 0.3) !important;
    }
    
    /* Quiz button */
    .quiz-button {
        background: linear-gradient(45deg, #ffd93d, #ff6b6b) !important;
        box-shadow: 0 4px 15px rgba(255, 217, 61, 0.3) !important;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e1e8ff;
        padding: 0.75rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .stTextArea > div > div > textarea {
        border-radius: 10px;
        border: 2px solid #e1e8ff;
        padding: 0.75rem;
        font-size: 1rem;
        font-family: 'Poppins', sans-serif;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div > select {
        border-radius: 10px;
        border: 2px solid #e1e8ff;
        padding: 0.5rem;
        font-size: 1rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    .css-1d391kg .stSelectbox > div > div > select {
        background: rgba(255, 255, 255, 0.9);
        color: #333;
    }
    
    /* Chat history styling */
    .chat-message {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #4ecdc4;
    }
    
    .user-message {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border-left: 4px solid #ff6b6b;
    }
    
    .bot-message {
        background: linear-gradient(45deg, #4ecdc4, #44a08d);
        color: white;
        border-left: 4px solid #ffd93d;
    }
    
    /* Status indicators */
    .status-success {
        background: linear-gradient(45deg, #a8e6cf, #7fcdcd);
        color: #2d3748;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: 600;
    }
    
    .status-error {
        background: linear-gradient(45deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: 600;
    }
    
    .status-warning {
        background: linear-gradient(45deg, #ffd93d, #ff9f43);
        color: #2d3748;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: 600;
    }
    
    /* Animations */
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-50px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
        100% {
            transform: scale(1);
        }
    }
    
    .pulse-animation {
        animation: pulse 2s infinite;
    }
    
    /* Progress bars */
    .stProgress > div > div > div {
        background: linear-gradient(45deg, #4ecdc4, #44a08d);
        border-radius: 10px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(45deg, #e1e8ff, #c7d2fe);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        color: #2d3748;
    }
    
    /* Feature icons */
    .feature-icon {
        font-size: 2rem;
        margin: 0.5rem;
        display: inline-block;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }
        
        .custom-card {
            padding: 1rem;
        }
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(45deg, #667eea, #764ba2);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(45deg, #764ba2, #667eea);
    }
    
    /* ConvAI button styling */
    .convai-button {
        background: linear-gradient(45deg, #9b5de5, #00bbf9) !important;
        box-shadow: 0 4px 15px rgba(155, 93, 229, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ========== Page Configuration ==========
st.set_page_config(
    page_title="EDU-GEN AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
load_custom_css()

# ========== Header Section ==========
st.markdown("""
    <div class="custom-card">
        <h1 class="main-title">🤖 EDU-GEN AI Assistant</h1>
        <p class="subtitle">Your Intelligent Voice-Powered Learning Companion</p>
    </div>
""", unsafe_allow_html=True)

# ========== Sidebar Configuration ==========
with st.sidebar:
    st.markdown("### 🎛️ Configuration Panel")
    
    # Language Settings
    st.markdown("#### 🌐 Language Settings")
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
    
    selected_language = st.selectbox("Select Language", list(LANGUAGES.keys()))
    st.session_state["language"] = LANGUAGES[selected_language]
    
    # Voice Settings
    st.markdown("#### 🗣️ Voice Settings")
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
    
    if st.session_state["language"] in VOICE_MAPPING:
        voice_options = VOICE_MAPPING[st.session_state["language"]]
        selected_voice = st.selectbox("Select Voice", voice_options)
        st.session_state["voice"] = selected_voice
    
    # Model Settings
    st.markdown("#### 🧠 AI Model Settings")
    MODEL_NAMES_GROQ = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]
    MODEL_NAMES_OPENAI = ["gpt-4o-mini"]
    
    provider = st.radio("Select Provider", ("Groq", "OpenAI"))
    
    if provider == "Groq":
        selected_model = st.selectbox("Select Model", MODEL_NAMES_GROQ)
    elif provider == "OpenAI":
        selected_model = st.selectbox("Select Model", MODEL_NAMES_OPENAI)
    
    # Advanced Settings
    st.markdown("#### ⚙️ Advanced Settings")
    allow_web_search = st.checkbox("🔍 Enable Web Search", value=False)
    use_voice = st.checkbox("🎤 Voice Input", value=False)
    use_tts = st.checkbox("🔊 Voice Output", value=False)
    
    # ConvAI Widget Toggle
    st.markdown("#### 🔊 ElevenLabs ConvAI")
    st.session_state.show_convai = st.checkbox("🎤 Enable Voice Conversation", value=st.session_state.show_convai)

# ========== Main Content Area ==========
# System Prompt Configuration
st.markdown("### 🧠 AI Assistant Configuration")
with st.expander("📝 System Prompt Settings", expanded=False):
    system_prompt = st.text_area(
        "Define your AI Assistant's personality and behavior:",
        height=100,
        placeholder="You are a helpful AI assistant. Respond in the user's language.",
        value="You are a helpful AI assistant. Respond in the user's language."
    )

# ========== Chat Interface ==========
st.markdown("### 💬 Chat Interface")

# Create columns for better layout
col1, col2 = st.columns([3, 1])

with col1:
    if use_voice:
        st.markdown("""
        <div class="info-box">
            <span class="feature-icon">🎤</span>
            <strong>Voice Input Enabled</strong><br>
            Click the button below to start recording your voice message.
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🎤 Start Voice Recording", key="voice_record"):
            try:
                with st.spinner("🎙️ Listening... Please speak now!"):
                    query = record_audio()
                    if query:
                        st.session_state["user_query"] = query
                        st.success(f"🗣️ Voice recorded: {query}")
                    else:
                        st.error("❌ Could not understand the audio. Please try again.")
            except Exception as e:
                st.error(f"❌ Voice recording failed: {str(e)}")
    else:
        st.session_state["user_query"] = st.text_area(
            "Type your message:",
            height=120,
            placeholder="Ask me anything! I'm here to help with your learning journey...",
            value=st.session_state["user_query"]
        )

with col2:
    st.markdown("""
    <div class="glass-card">
        <h4>🎯 Quick Actions</h4>
        <p>🔍 Search enabled: {}</p>
        <p>🎤 Voice input: {}</p>
        <p>🔊 Voice output: {}</p>
        <p>🌐 Language: {}</p>
        <p>🎧 ConvAI: {}</p>
    </div>
    """.format(
        "✅" if allow_web_search else "❌",
        "✅" if use_voice else "❌", 
        "✅" if use_tts else "❌",
        selected_language,
        "✅" if st.session_state.show_convai else "❌"
    ), unsafe_allow_html=True)

# Send Message Button
if st.button("🚀 Send Message", key="send_message", type="primary"):
    user_query = st.session_state["user_query"]
    
    if user_query and user_query.strip():
        # API Configuration
        API_URL = "http://127.0.0.1:9999/chat"
        
        payload = {
            "model_name": selected_model,
            "model_provider": provider,
            "system_prompt": system_prompt,
            "messages": [user_query],
            "allow_search": allow_web_search,
            "language": st.session_state["language"]
        }
        
        with st.spinner("🤖 Processing your request..."):
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            response = requests.post(API_URL, json=payload)
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Handle response format
            if isinstance(response_data, dict):
                if "error" in response_data:
                    st.markdown(f"""
                    <div class="status-error">
                        ❌ Error: {response_data["error"]}
                    </div>
                    """, unsafe_allow_html=True)
                    response_text = response_data["error"]
                elif "response" in response_data:
                    response_text = response_data["response"]
                else:
                    response_text = str(response_data)
            else:
                response_text = str(response_data)
            
            # Display response
            st.markdown("### 🤖 AI Response")
            st.markdown(f"""
            <div class="bot-message">
                <strong>🎯 Response:</strong><br>
                {response_text}
            </div>
            """, unsafe_allow_html=True)
            
            # Handle TTS if enabled
            audio_path = None
            if use_tts:
                with st.spinner("🔊 Generating voice response..."):
                    audio_path = speak_response_with_elevenlabs(response_text)
            
            # Add to chat history
            chat_entry = {
                "user_query": user_query,
                "agent_response": response_text,
                "audio_path": audio_path,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "language": st.session_state["language"],
                "model": f"{provider} - {selected_model}",
                "voice": st.session_state["voice"]
            }
            
            st.session_state["chat_history"].append(chat_entry)
            st.session_state["last_response"] = response_text
            
            st.markdown("""
            <div class="status-success">
                ✅ Message sent successfully!
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.markdown(f"""
            <div class="status-error">
                ❌ Failed to connect to AI service. Status: {response.status_code}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-warning">
            ⚠️ Please enter a message or record your voice first.
        </div>
        """, unsafe_allow_html=True)

# ========== Quiz Generation Section ==========
if st.session_state.get("last_response"):
    st.markdown("---")
    st.markdown("### 📚 Quiz Generator")
    
    st.markdown("""
    <div class="info-box">
        <span class="feature-icon">📝</span>
        <strong>Generate Educational Quiz</strong><br>
        Create an interactive quiz based on the AI's last response to test your understanding.
    </div>
    """, unsafe_allow_html=True)
    
    quiz_col1, quiz_col2 = st.columns([2, 1])
    
    with quiz_col1:
        if st.button("📝 Generate Quiz", key="generate_quiz"):
            QUIZ_URL = "http://127.0.0.1:9999/generate_quiz"
            
            with st.spinner("🧠 Creating your personalized quiz..."):
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
                    
                    st.markdown("""
                    <div class="status-success">
                        ✅ Quiz generated successfully! Download options available below.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="status-error">
                        ❌ Quiz generation failed: {quiz_response.text}
                    </div>
                    """, unsafe_allow_html=True)
    
    with quiz_col2:
        if st.session_state.quiz_data:
            st.markdown("#### 📥 Download Options")
            
            # Download buttons
            st.download_button(
                label="📋 Quiz with Answers",
                data=base64.b64decode(st.session_state.quiz_data["quiz_with_answers"]),
                file_name="quiz_with_answers.pdf",
                mime="application/pdf",
                key="download_answers"
            )
            
            st.download_button(
                label="❓ Quiz Questions Only",
                data=base64.b64decode(st.session_state.quiz_data["quiz_questions"]),
                file_name="quiz_questions.pdf",
                mime="application/pdf",
                key="download_questions"
            )
    
    # Quiz Preview
    if st.session_state.quiz_data:
        with st.expander("👁️ Preview Quiz", expanded=False):
            quiz_items = st.session_state.quiz_data.get("quiz_data", [])
            
            for idx, item in enumerate(quiz_items):
                st.markdown(f"""
                <div class="glass-card">
                    <h4>Question {idx + 1}</h4>
                    <p><strong>{item.get('question', '')}</strong></p>
                </div>
                """, unsafe_allow_html=True)
                
                options = item.get('options', [])
                for i, option in enumerate(options):
                    st.markdown(f"**{chr(65+i)}.** {option}")
                
                st.markdown(f"""
                <div class="info-box">
                    <strong>Answer:</strong> {item.get('answer', '')}<br>
                    <strong>Explanation:</strong> {item.get('explanation', '')}
                </div>
                """, unsafe_allow_html=True)

# ========== Chat History Section ==========
if st.session_state["chat_history"]:
    st.markdown("---")
    st.markdown("### 📜 Chat History")
    
    for idx, message in enumerate(reversed(st.session_state["chat_history"])):
        with st.expander(f"💬 Conversation {len(st.session_state['chat_history']) - idx}", expanded=False):
            st.markdown(f"""
            <div class="user-message">
                <strong>👤 You:</strong> {message['user_query']}<br>
                <small>🕐 {message['timestamp']} | 🌐 {message['language']} | 🤖 {message['model']}</small>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="bot-message">
                <strong>🤖 AI:</strong> {message['agent_response']}
            </div>
            """, unsafe_allow_html=True)
            
            if message.get("audio_path"):
                st.audio(message["audio_path"], format="audio/mp3")

# ========== ElevenLabs ConvAI Section ==========
if st.session_state.show_convai:
    st.markdown("---")
    st.markdown("### 🎙️ Voice Conversation with ElevenLabs ConvAI")
    
    st.markdown("""
    <div class="info-box">
        <span class="feature-icon">🎧</span>
        <strong>Real-time Voice Conversation</strong><br>
        Have a natural voice conversation with the AI assistant using ElevenLabs' ConvAI technology.
        Click the button below to open the voice conversation interface in a new tab.
    </div>
    """, unsafe_allow_html=True)
    
    # Button to open ConvAI in a new tab
    convai_url = "https://elevenlabs.io/app/talk-to?agent_id=agent_01jztc1pbmfzw9qw2dv4a4gshq"
    st.markdown(f"""
    <a href="{convai_url}" target="_blank">
        <div style="text-align: center;">
            <button style="
                background: linear-gradient(45deg, #9b5de5, #00bbf9);
                color: white;
                border: none;
                border-radius: 25px;
                padding: 1rem 2.5rem;
                font-weight: 600;
                font-size: 1.2rem;
                cursor: pointer;
                box-shadow: 0 6px 20px rgba(155, 93, 229, 0.4);
                transition: all 0.3s ease;
                margin: 1rem 0;
            ">
                🎤 Open Voice Conversation
            </button>
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <strong>Troubleshooting Tips:</strong>
        <ul>
            <li>Make sure you're signed in to your ElevenLabs account</li>
            <li>Grant microphone permissions when prompted</li>
            <li>Check if your browser is blocking pop-ups</li>
            <li>Ensure you have a stable internet connection</li>
            <li>Try refreshing the page if the interface doesn't load</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ========== Footer ==========
st.markdown("---")
st.markdown("""
<div class="custom-card">
    <div style="text-align: center; color: #666;">
        <p>🚀 <strong>EDU-GEN AI Assistant</strong> - Powered by Advanced AI Models</p>
        <p>✨ Features: Voice Recognition • Multi-language Support • Quiz Generation • Smart Search • ConvAI Integration</p>
    </div>
</div>
""", unsafe_allow_html=True)