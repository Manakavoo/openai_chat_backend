# main.py
import os
import json
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
# import openai
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
from models.schemas import (
    OpenAIRequest, OpenAIResponse, 
    TutorRequest, TutorResponse,
    MessageHistory
)
from utils.conversation_manager import (
    generate_conversation_id, 
    save_conversation, 
    list_conversations,
    generate_conversation_title
)
from youtube.video_transcripts import get_transcript

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Learning Assistant",
    description="Video Context and Tutor AI Assistant",
    version="0.1.0"
)

# Allow frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific frontend domain for security (e.g., ["https://your-frontend.com"])
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

api_key = os.getenv("OPENAI_API_KEY")
# Configure OpenAI client
client=OpenAI(api_key = api_key)
if not api_key:
    raise ValueError("No OpenAI API key found. Please set OPENAI_API_KEY in .env file.")

# Comprehensive Prompts
# PROMPTS = {
#     "video_context": """You are an advanced AI assistant specializing in analyzing educational video content. 
#     Your task is to provide insightful, contextual responses based on the user's query and the specific video context.
    
#     Guidelines:
#     1. Always reference the specific video details (title, description) in your response
#     2. If a timestamp is provided, explain the content around that specific moment
#     3. Connect the user's question to the broader video content
#     4. Provide clear, concise, and educational explanations
#     5. If the query is too broad or not directly related to the video, guide the user appropriately
    
#     Video Context will include:
#     - Video ID
#     - Video Title
#     - Video Description
    
#     Respond in a way that demonstrates deep understanding of the video's subject matter.""",
    
#     "ai_tutor": """You are an expert AI tutor with comprehensive knowledge across multiple learning domains. 
#     Your primary goals are to:
#     1. Provide structured, personalized learning guidance
#     2. Create detailed, actionable learning roadmaps
#     3. Offer in-depth explanations and learning strategies
#     4. Help users navigate complex learning paths
    
#     Conversation Principles:
#     - Adapt your explanations to the user's current knowledge level
#     - Break down complex topics into manageable steps
#     - Provide practical advice and resource recommendations
#     - Encourage continuous learning and skill development
#     - Be motivational and supportive in your guidance
    
#     When creating roadmaps or explaining concepts:
#     - Use clear, hierarchical explanations
#     - Include practical milestones
#     - Suggest resources (books, courses, tutorials)
#     - Highlight potential challenges and how to overcome them"""
# }

PROMPTS = {
    "video_context": """You are a knowledgeable and friendly AI assistant that helps users understand educational videos. Your goal is to answer questions in a clear and engaging way, making complex ideas easy to grasp.  
    your name is Manakavoo
    How to Respond:  
    1. Mention the video title or key details when relevant to provide context.  
    2. If a timestamp is provided, explain what happens around that moment.  
    3. Relate the user’s question to the broader topic of the video.  
    4. Keep responses simple, structured, and easy to follow—avoid overwhelming the user with too much information at once.  
    5. If the question is too broad or not related to the video, kindly guide the user toward a more relevant query.  
    6.  Always have a short response with a clear focus on the video content.
    7. use transcripts to provide context and help the user understand the video content better.

    Guidelines:
    Video details provided will include:   
    - Video Title  
    - Video transcripts with timestamps  
    - specific timestamps ( if provided)

    Always aim for a conversational and helpful tone, making the interaction feel natural and engaging!""",

    "ai_tutor": """You are an AI tutor designed to guide learners, answer their questions, and help them build strong knowledge in their chosen subjects. Your job is to make learning **interactive, personalized, and motivating**.  
    your name is Manakavoo
    How to Respond:  
    1. Start by understanding the learner’s level and goals—ask follow-up questions when needed.  
    2. Give clear and step-by-step explanations, avoiding overly technical or long-winded answers.  
    3. Offer practical advice, study techniques, and useful learning resources (books, courses, tutorials).  
    4. Encourage curiosity by suggesting what to learn next or asking thought-provoking questions.  
    5. Keep your tone supportive and engaging, making the learner feel motivated and confident. 

    important Note:
    Dont use  "#" ," ** " for headings instead uses spaces. 

    When explaining concepts or creating learning plans:  
    - Break topics into simple steps with clear examples.  
    - Provide real-world applications to make learning relevant.  
    - Help learners overcome challenges by offering practical solutions.  

    Make sure every response **feels like a conversation, not a lecture**—engage with the learner and keep it friendly!"""
}

def generate_openai_response(messages: list, model: str = "gpt-4o-mini", max_tokens: int = 300):
    """
    Generate response using OpenAI's Chat Completion API
    
    Args:
        messages (list): List of message dictionaries
        model (str): OpenAI model to use
        max_tokens (int): Maximum tokens for response
    
    Returns:
        str: Generated response
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/openai", response_model=OpenAIResponse)
async def video_context_assistant(request: OpenAIRequest):
    """
    Video Context AI Assistant Endpoint
    
    Provides contextual responses based on video content
    """
    print("")
    # Generate conversation ID
    conversation_id = generate_conversation_id()
    
    # Prepare messages for OpenAI
    messages = [
        {"role": "system", "content": PROMPTS["video_context"]}
    ]
    
    # Add conversation history
    messages.extend([
        {"role": "user" if msg.role == "user" else "assistant", "content": msg.content} 
        for msg in request.history
    ])
    
    try:
        result = get_transcript(request.videoId)
    except Exception as e:
        result = {"error": str(e)}
    title = result.get('title', 'Title Not Found')
    transcript = result.get('transcript', 'Transcript Not Found')

    # Add current video context
    if request.videoContext:
        context_info = f"""
        Video Details:
        - Title: { title or 'No title available'}
        - transcript: {transcript or 'No transcript available'}
        - Timestamp: {request.timestamp or 'No specific timestamp'}
        """
        messages.append({"role": "system", "content": context_info})
    
    # Add current user message
    messages.append({"role": "user", "content": request.message})
    
    # Generate response
    response_text = generate_openai_response(messages)
    response_text =  response_text.replace("*", "")
    response_text = response_text.replace("#", "")
    
    # Prepare conversation history for saving
    full_history = request.history + [
        MessageHistory(role="user", content=request.message),
        MessageHistory(role="assistant", content=response_text)
    ]
    
    # Generate conversation title
    title = generate_conversation_title(request.message)
    
    # Save conversation
    save_conversation(conversation_id, full_history, title)
    
    return OpenAIResponse(
        response=response_text,
        conversationId=conversation_id
    )

@app.post("/tutor", response_model=TutorResponse)
async def ai_tutor(request: TutorRequest):
    """
    AI Tutor Endpoint
    
    Provides learning guidance, roadmaps, and in-depth explanations
    """
    # Generate conversation ID
    conversation_id = generate_conversation_id()
    
    # Prepare messages for OpenAI
    messages = [
        {"role": "system", "content": PROMPTS["ai_tutor"]}
    ]
    
    # Add conversation history
    messages.extend([
        {"role": "user" if msg.role == "user" else "assistant", "content": msg.content} 
        for msg in request.history
    ])
    
    # Add current user message
    messages.append({"role": "user", "content": request.message})
    
    # Generate response
    response_text = generate_openai_response(
        messages, 
        max_tokens=500  # More tokens for detailed explanations
    )

    response_text =  response_text.replace("*", "")
    response_text = response_text.replace("#", "")
    
    # Prepare conversation history for saving
    full_history = request.history + [
        MessageHistory(role="user", content=request.message),
        MessageHistory(role="assistant", content=response_text)
    ]
    
    # Generate conversation title
    title = generate_conversation_title(request.message)
    
    # Save conversation
    save_conversation(conversation_id, full_history, title)
    
    return TutorResponse(
        response=response_text,
        conversationId=conversation_id
    )

@app.get("/tutor/conversations")
async def get_conversations():
    """
    List all saved conversations
    """
    return {"conversations": list_conversations()}

# Optional: Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)