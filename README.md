💡 Project Title: EDU-GEN AI Assistant
A voice-powered, real-time, multi-user chatbot system built with LangGraph, Agno-style memory, VAD, STT, TTS, and LLM APIs (Groq/OpenAI). It supports natural, multilingual conversations, personalized memory handling, and dynamic quiz generation.

🚀 Features
✅ Real-time voice interaction with VAD + STT (Google Speech Recognition)

✅ Natural multilingual conversations (supports 15+ languages)

✅ TTS with ElevenLabs for human-like voice responses

✅ LLM-based AI agent using LangGraph, Groq/OpenAI models

✅ Memory and state tracking (LangGraph REACT agent)

✅ Quiz generator that returns printable PDFs

✅ Responsive frontend using Streamlit

✅ Supports multiple users concurrently with session isolation

🧠 Tech Stack
Component	Technology
Frontend	Streamlit + ElevenLabs TTS
Backend API	FastAPI
Voice I/O	speech_recognition, Pydub, ElevenLabs
LLM APIs	Groq (LLaMA 3.3), OpenAI GPT-4o-mini
Agent Framework	LangGraph + Tavily Search
Quiz Engine	AI-generated + ReportLab PDFs
State Handling	Agno-style memory via LangGraph agent
System Design	Python-based modular architecture
