# main.py
import os
import json
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
# import openai
from openai import OpenAI
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

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Learning Assistant",
    description="Video Context and Tutor AI Assistant",
    version="0.1.0"
)
api_key = os.getenv("OPENAI_API_KEY")
# Configure OpenAI client
client=OpenAI(api_key = api_key)
if not api_key:
    raise ValueError("No OpenAI API key found. Please set OPENAI_API_KEY in .env file.")

# Comprehensive Prompts
PROMPTS = {
    "video_context": """You are an advanced AI assistant specializing in analyzing educational video content. 
    Your task is to provide insightful, contextual responses based on the user's query and the specific video context.
    
    Guidelines:
    1. Always reference the specific video details (title, description) in your response
    2. If a timestamp is provided, explain the content around that specific moment
    3. Connect the user's question to the broader video content
    4. Provide clear, concise, and educational explanations
    5. If the query is too broad or not directly related to the video, guide the user appropriately
    
    Video Context will include:
    - Video ID
    - Video Title
    - Video Description
    
    Respond in a way that demonstrates deep understanding of the video's subject matter.""",
    
    "ai_tutor": """You are an expert AI tutor with comprehensive knowledge across multiple learning domains. 
    Your primary goals are to:
    1. Provide structured, personalized learning guidance
    2. Create detailed, actionable learning roadmaps
    3. Offer in-depth explanations and learning strategies
    4. Help users navigate complex learning paths
    
    Conversation Principles:
    - Adapt your explanations to the user's current knowledge level
    - Break down complex topics into manageable steps
    - Provide practical advice and resource recommendations
    - Encourage continuous learning and skill development
    - Be motivational and supportive in your guidance
    
    When creating roadmaps or explaining concepts:
    - Use clear, hierarchical explanations
    - Include practical milestones
    - Suggest resources (books, courses, tutorials)
    - Highlight potential challenges and how to overcome them"""
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
    
    # Add current video context
    if request.videoContext:
        context_info = f"""
        Video Details:
        - ID: {request.videoContext.id}
        - Title: {request.videoContext.title}
        - Description: {request.videoContext.description or 'No description'}
        - Timestamp: {request.timestamp or 'No specific timestamp'}
        """
        messages.append({"role": "system", "content": context_info})
    
    # Add current user message
    messages.append({"role": "user", "content": request.message})
    
    # Generate response
    response_text = generate_openai_response(messages)
    
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