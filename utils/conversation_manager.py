# utils/conversation_manager.py
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from models.schemas import ConversationInfo, MessageHistory

CONVERSATIONS_DIR = "conversations"
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)

def generate_conversation_id() -> str:
    """Generate a unique conversation ID."""
    return f"conv_{uuid.uuid4().hex[:10]}"

def save_conversation(conversation_id: str, messages: List[MessageHistory], title: str) -> None:
    """
    Save conversation to a JSON file.
    
    Args:
        conversation_id (str): Unique identifier for the conversation
        messages (List[MessageHistory]): List of messages in the conversation
        title (str): Title of the conversation
    """
    conversation_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    
    conversation_data = {
        "id": conversation_id,
        "title": title,
        "updatedAt": datetime.utcnow().isoformat(),
        "messages": [msg.dict() for msg in messages]
    }
    
    with open(conversation_path, 'w') as f:
        json.dump(conversation_data, f, indent=2)

def load_conversation(conversation_id: str) -> Optional[Dict]:
    """
    Load a conversation from its JSON file.
    
    Args:
        conversation_id (str): Unique identifier for the conversation
    
    Returns:
        Optional[Dict]: Conversation data or None if not found
    """
    conversation_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    
    try:
        with open(conversation_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def list_conversations() -> List[ConversationInfo]:
    """
    List all saved conversations.
    
    Returns:
        List[ConversationInfo]: List of conversation metadata
    """
    conversations = []
    
    for filename in os.listdir(CONVERSATIONS_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(CONVERSATIONS_DIR, filename)
            with open(filepath, 'r') as f:
                conversation = json.load(f)
                conversations.append({
                    "id": conversation['id'],
                    "title": conversation['title'],
                    "updatedAt": conversation['updatedAt']
                })
    
    # Sort conversations by updatedAt in descending order
    return sorted(
        conversations, 
        key=lambda x: datetime.fromisoformat(x['updatedAt']), 
        reverse=True
    )

def generate_conversation_title(initial_message: str) -> str:
    """
    Generate a conversation title based on the initial message.
    
    Args:
        initial_message (str): First message in the conversation
    
    Returns:
        str: Generated title
    """
    # Simple title generation strategy
    words = initial_message.split()
    if len(words) <= 5:
        return initial_message
    else:
        return ' '.join(words[:5]) + '...'