"""
generate_tutorial.py
Endpoint listening for POST requests from frontend, handles user questions and uses Runnable from
memory_store.py to communicate with Llama3
"""

from memory_store import with_message_history
from fastapi import APIRouter, HTTPException
from models import ChatbotRequest
from langchain_core.messages import HumanMessage
import uuid

# Initialize router for 'generate_tutorial' endpoint handler
router = APIRouter()

@router.post('/generate_tutorial/')
def generate_tutorial(request: ChatbotRequest):
    '''
    This decorated function listens for POST requests made to server and returns
    a Llama3 response based on user input in ChatbotRequest
    '''
    try:
        # Generate a unique session ID for each conversation
        session_id = str(uuid.uuid4())
        
        # Session ID in config identifies the user's unique conversation when Runnable is made
        config = {"configurable": {"session_id": session_id}}
        prompt = request.prompt 

        # Llama3 runnable invoked with user question and config
        response = with_message_history.invoke(
            [HumanMessage(content=prompt)],
            config=config,
        )

        # Return Llama3 response as dictionary so frontend can read JSON payload
        return {"tutorial": response.content, "session_id": session_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error has occurred: {str(e)}")
    
