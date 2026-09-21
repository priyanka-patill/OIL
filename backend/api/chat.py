"""
OIL HSE Safety Assistant — Conversational API Router

Exposes REST endpoints to query the OIL HSE Safety Assistant, process messages,
retrieve conversation history, and delete chat sessions.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.database.database import get_db
from backend.database.models import User
from backend.security.dependencies import get_current_user
from backend.services import chat_service

router = APIRouter(prefix="/chat", tags=["OIL HSE Safety Assistant"])


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User question or prompt")
    conversation_id: Optional[str] = Field(None, description="Optional conversation session ID")


@router.post("", status_code=status.HTTP_200_OK)
def send_chat_message(
    req: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a message to the OIL HSE Safety Assistant.
    Processes user intent, queries authorized database/analytics tools, and returns the response.
    """
    try:
        res = chat_service.process_chat_message(
            db=db,
            user=current_user,
            message_text=req.message,
            conversation_id=req.conversation_id
        )
        return {
            "success": True,
            "message": "Message processed successfully.",
            "data": res
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chatbot processing error: {str(e)}"
        )


@router.get("/conversations", status_code=status.HTTP_200_OK)
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List chat conversations for the current authenticated user."""
    convs = chat_service.list_user_conversations(db, current_user)
    return {
        "success": True,
        "count": len(convs),
        "data": convs
    }


@router.get("/conversations/{conversation_id}", status_code=status.HTTP_200_OK)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete transcript of a chat conversation."""
    history = chat_service.get_conversation_history(db, current_user, conversation_id)
    if not history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return {
        "success": True,
        "data": history
    }


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_200_OK)
def delete_conversation_endpoint(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation session."""
    success = chat_service.delete_conversation(db, current_user, conversation_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return {
        "success": True,
        "message": "Conversation deleted successfully."
    }
