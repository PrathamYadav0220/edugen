# if you dont use pipenv uncomment the following:
# from dotenv import load_dotenv
# load_dotenv()

# Step1: Setup Pydantic Model (Schema Validation)
from pydantic import BaseModel
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
import requests
import json
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os
import re  # Added for improved JSON parsing

# Step2: Setup AI Agent from FrontEnd Request
from ai_agent import get_response_from_ai_agent

class RequestState(BaseModel):
    model_name: str
    model_provider: str
    system_prompt: str
    messages: List[str]
    allow_search: bool
    language: str

class QuizRequest(BaseModel):
    topic: str
    language: str
    model_name: str
    model_provider: str

ALLOWED_MODEL_NAMES = ["llama3-70b-8192", "mixtral-8x7b-32768", "llama-3.3-70b-versatile", "gpt-4o-mini"]

app = FastAPI(title="LangGraph AI Agent")

# Language-specific system prompt enhancements
LANGUAGE_PROMPTS = {
    "hi-IN": "\n\nकृपया हिंदी में उत्तर दें। सरल और स्पष्ट भाषा का प्रयोग करें।",
    "bn-IN": "\n\nঅনুগ্রহ করে বাংলায় উত্তর দিন। সহজ এবং স্পষ্ট ভাষা ব্যবহার করুন।",
    "mr-IN": "\n\nकृपया मराठीत उत्तर द्या. सोपी आणि स्पष्ट भाषा वापरा.",
    "ta-IN": "\n\nதமிழில் பதிலளிக்கவும். எளிய மற்றும் தெளிவான மொழியைப் பயன்படுத்தவும்.",
    "te-IN": "\n\nదయచేసి తెలుగులో జవాబు ఇవ్వండి. సరళమైన మరియు స్పష్టమైన భాషను ఉపయోగించండి.",
    "gu-IN": "\n\nકૃપા કરીને ગુજરાતીમાં જવાબ આપો. સરળ અને સ્પષ્ટ ભાષા નો ઉપયોગ કરો.",
    "kn-IN": "\n\nದಯವಿಟ್ಟು ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ. ಸರಳ ಮತ್ತು ಸ್ಪಷ್ಟ ಭಾಷೆಯನ್ನು ಬಳಸಿ.",
    "ml-IN": "\n\nദയവായി മലയാളത്തിൽ മറുപടി നൽകുക. ലളിതവും വ്യക്തവുമായ ഭാഷ ഉപയോഗിക്കുക.",
    "pa-IN": "\n\nਕਿਰਪਾ ਕਰਕੇ ਪੰਜਾਬੀ ਵਿੱਚ ਜਵਾਬ ਦਿਓ। ਸਧਾਰਨ ਅਤੇ ਸਪਸ਼ਟ ਭਾਸ਼ਾ ਦੀ ਵਰਤੋਂ ਕਰੋ।",
    "ur-IN": "\n\nبراہ کرم اردو میں جواب دیں۔ سادہ اور واضح زبان استعمال کریں۔"
}

def create_pdf(content, filename, language):
    """Create a PDF file with quiz content"""
    try:
        # Create PDF with language-appropriate font
        pdf_path = f"{filename}.pdf"
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        flowables = []
        
        # Add title based on filename
        if "with_answers" in filename:
            title = "Quiz with Answers" if language.startswith("en") else "उत्तरों के साथ प्रश्नोत्तरी"
        else:
            title = "Quiz Questions" if language.startswith("en") else "प्रश्नोत्तरी"
            
        flowables.append(Paragraph(f"<b>{title}</b>", styles['Title']))
        flowables.append(Spacer(1, 12))
        
        # Check if content is a list of questions
        if isinstance(content, list) and all(isinstance(q, dict) for q in content):
            for idx, item in enumerate(content):
                # Question
                q_text = f"<b>Q{idx+1}: {item.get('question', '')}</b>"
                flowables.append(Paragraph(q_text, styles['Normal']))
                
                # Options
                options = item.get('options', [])
                for i, option in enumerate(options):
                    flowables.append(Paragraph(f"{chr(65+i)}. {option}", styles['Normal']))
                
                # Answer and explanation (only for answers PDF)
                if "with_answers" in filename:
                    answer = item.get('answer', '')
                    explanation = item.get('explanation', '')
                    flowables.append(Paragraph(f"<b>Answer:</b> {answer}", styles['Normal']))
                    if explanation:
                        flowables.append(Paragraph(f"<i>Explanation:</i> {explanation}", styles['Normal']))
                
                flowables.append(Spacer(1, 12))
        else:
            # Handle text content
            flowables.append(Paragraph(f"<b>Content:</b> {str(content)}", styles['Normal']))
        
        doc.build(flowables)
        
        # Read the created PDF
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        # Clean up temporary file
        os.remove(pdf_path)
        
        return pdf_bytes
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF creation failed: {str(e)}")

@app.post("/chat")
def chat_endpoint(request: RequestState) -> Dict[str, Any]:
    """
    API Endpoint to interact with the Chatbot using LangGraph and search tools.
    It dynamically selects the model specified in the request
    """
    if request.model_name not in ALLOWED_MODEL_NAMES:
        return {"error": "Invalid model name. Kindly select a valid AI model"}
    
    llm_id = request.model_name
    query = request.messages
    allow_search = request.allow_search
    system_prompt = request.system_prompt
    provider = request.model_provider
    language = request.language

    # Add language-specific instruction if available
    if language in LANGUAGE_PROMPTS:
        system_prompt += LANGUAGE_PROMPTS[language]
    else:
        # Default instruction for other languages
        system_prompt += f"\n\nPlease respond in {language} language. Use simple and clear language."

    # Create AI Agent and get response from it! 
    try:
        response = get_response_from_ai_agent(llm_id, query, allow_search, system_prompt, provider)
        return {"response": response}
    except Exception as e:
        return {"error": f"Error processing request: {str(e)}"}

@app.post("/generate_quiz")
def generate_quiz(request: QuizRequest):
    """Generate a quiz PDF based on a topic"""
    try:
        # Generate quiz using the AI model
        prompt = f"""
        Generate a 10-question quiz about the following topic. 
        For each question, provide:
        - The question text
        - 4 multiple choice options (labeled A, B, C, D)
        - The correct answer (specify the letter)
        - A brief explanation of why it's correct
        
        Topic: {request.topic}
        
        Format the response as a JSON array of objects with these keys:
        "question", "options", "answer", "explanation"
        
        Return ONLY the JSON array without any additional text.
        """
        
        # Get quiz content from AI
        quiz_data = get_response_from_ai_agent(
            request.model_name,
            [prompt],
            False,  # Don't allow web search for quiz
            "You are an expert quiz creator who creates educational quizzes. Return only JSON format.",
            request.model_provider
        )
        
        # Improved JSON extraction
        try:
            # Find the first [ and last ] to extract JSON array
            start_index = quiz_data.find('[')
            end_index = quiz_data.rfind(']') + 1
            json_str = quiz_data[start_index:end_index]
            quiz_questions = json.loads(json_str)
        except Exception as e:
            # If parsing fails, try to extract with regex
            try:
                json_match = re.search(r'\[.*\]', quiz_data, re.DOTALL)
                if json_match:
                    quiz_questions = json.loads(json_match.group())
                else:
                    quiz_questions = [{
                        "question": "Quiz parsing error",
                        "options": ["A: Error in parsing", "B: Contact support"],
                        "answer": "A",
                        "explanation": f"Original response: {quiz_data}"
                    }]
            except:
                quiz_questions = [{
                    "question": "Quiz parsing error",
                    "options": ["A: Critical error", "B: Try again later"],
                    "answer": "A",
                    "explanation": quiz_data
                }]
        
        # Create PDF with questions and answers
        qa_pdf = create_pdf(
            quiz_questions, 
            "quiz_with_answers", 
            request.language
        )
        
        # Create PDF with only questions (using same structure)
        questions_only = []
        for q in quiz_questions:
            questions_only.append({
                "question": q.get("question", ""),
                "options": q.get("options", [])
            })
        
        questions_pdf = create_pdf(
            questions_only, 
            "quiz_questions", 
            request.language
        )
        
        # Return base64 encoded PDFs
        return {
            "quiz_with_answers": base64.b64encode(qa_pdf).decode('utf-8'),
            "quiz_questions": base64.b64encode(questions_pdf).decode('utf-8'),
            "quiz_data": quiz_questions  # Return structured data for frontend
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")

# Step3: Run app & Explore Swagger UI Docs
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9999)