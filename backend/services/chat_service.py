"""
OIL HSE Safety Assistant — Conversational Service (chat_service.py)

Coordinates intent routing, authorized data retrieval, LLM interaction,
response formatting, source citation extraction, UI action link generation,
and persistent conversation management.
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.database.models import User, ChatConversation, ChatMessage, utc_now
from backend.services import chat_tools, llm_service


def get_or_create_conversation(db: Session, user: User, conversation_id: Optional[str] = None) -> ChatConversation:
    """Get an existing conversation for current user or create a new session."""
    if conversation_id:
        conv = (
            db.query(ChatConversation)
            .filter(ChatConversation.id == conversation_id, ChatConversation.user_id == user.id)
            .first()
        )
        if conv:
            return conv
    
    # Create new conversation
    new_id = f"conv-{uuid.uuid4().hex[:12]}"
    conv = ChatConversation(
        id=new_id,
        user_id=user.id,
        title="HSE Safety Assistant Chat",
        created_at=utc_now(),
        updated_at=utc_now()
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def list_user_conversations(db: Session, user: User) -> List[Dict[str, Any]]:
    """List all active chat conversations for the current user."""
    convs = (
        db.query(ChatConversation)
        .filter(ChatConversation.user_id == user.id)
        .order_by(ChatConversation.updated_at.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "message_count": len(c.messages)
        }
        for c in convs
    ]


def get_conversation_history(db: Session, user: User, conversation_id: str) -> Optional[Dict[str, Any]]:
    """Get complete conversation transcript for current user."""
    conv = (
        db.query(ChatConversation)
        .filter(ChatConversation.id == conversation_id, ChatConversation.user_id == user.id)
        .first()
    )
    if not conv:
        return None
    
    messages = []
    for m in conv.messages:
        sources = json.loads(m.sources_json) if m.sources_json else []
        actions = json.loads(m.actions_json) if m.actions_json else []
        messages.append({
            "id": m.id,
            "sender": m.sender,
            "content": m.content,
            "sources": sources,
            "actions": actions,
            "created_at": m.created_at.isoformat() if m.created_at else None
        })
    
    return {
        "id": conv.id,
        "title": conv.title,
        "messages": messages
    }


def delete_conversation(db: Session, user: User, conversation_id: str) -> bool:
    """Delete a conversation belonging to current user."""
    conv = (
        db.query(ChatConversation)
        .filter(ChatConversation.id == conversation_id, ChatConversation.user_id == user.id)
        .first()
    )
    if not conv:
        return False
    
    db.delete(conv)
    db.commit()
    return True


def process_chat_message(
    db: Session,
    user: User,
    message_text: str,
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main Chat Pipeline:
    1. Authenticated session lookup.
    2. Intent recognition & authorized tool execution.
    3. LLM generation.
    4. Sources & UI action links extraction.
    5. Database persistence.
    """
    conv = get_or_create_conversation(db, user, conversation_id)
    p_lower = message_text.lower().strip()

    # Save User Message to DB
    user_msg = ChatMessage(
        conversation_id=conv.id,
        sender="user",
        content=message_text,
        created_at=utc_now()
    )
    db.add(user_msg)
    db.commit()

    # Build context data & sources/actions payload based on Intent
    context_data = {}
    sources = []
    actions = []

    # Intent 1: My Actions / Assigned Tasks
    if any(k in p_lower for k in ["my action", "assigned action", "overdue action", "my tasks", "assigned to me"]):
        if "overdue" in p_lower:
            actions_list = chat_tools.get_overdue_actions_data(db, user)
            context_data["overdue_actions"] = actions_list
        else:
            actions_list = chat_tools.get_my_actions_data(db, user)
            context_data["my_actions"] = actions_list
        
        actions.append({"label": "View My Actions", "path": "/actions/my"})

    # Intent 2: Dashboard / Platform Overview
    elif any(k in p_lower for k in ["how many", "dashboard", "platform summary", "total report", "sif count", "summary", "reports do we have", "report count", "stat"]):
        summary = chat_tools.get_dashboard_summary_data(db, user)
        context_data["dashboard_summary"] = summary
        actions.append({"label": "Safety Intelligence", "path": "/analytics"})
        actions.append({"label": "HSE Action Center", "path": "/action-center"})

    # Intent 3: Specific Report Query or SIF Explanation
    elif "report" in p_lower and any(char.isdigit() for char in p_lower):
        # Extract report identifier from text (e.g., "report 1" or "oil-2026-000001" or "nm-001")
        import re
        match = re.search(r'(oil-\d{4}-\d{6}|\d+)', p_lower)
        if match:
            rep_id = match.group(1)
            report_info = chat_tools.get_report_details_data(db, user, rep_id)
            if report_info:
                context_data["report_details"] = report_info
                sources.append({
                    "title": f"Report #{report_info['report_number']}",
                    "path": f"/reports/{report_info['id']}"
                })
                actions.append({"label": f"View Report #{report_info['report_number']}", "path": f"/reports/{report_info['id']}"})

    # Intent 4: Safety Intelligence / Patterns / Barriers
    elif any(k in p_lower for k in ["pattern", "barrier", "degradation", "intelligence", "recurring", "trend", "escalation"]):
        intel = chat_tools.get_safety_intelligence_data(db, user)
        context_data["safety_intelligence"] = intel
        actions.append({"label": "Safety Intelligence", "path": "/analytics"})

    # Intent 5: Action Center / Interventions
    elif any(k in p_lower for k in ["action center", "pending review", "intervention", "verification pending"]):
        summary = chat_tools.get_action_center_summary_data(db, user)
        context_data["action_center_summary"] = summary
        actions.append({"label": "HSE Action Center", "path": "/action-center"})

    # Intent 6: Submit Report Navigation
    elif any(k in p_lower for k in ["submit report", "how to submit", "file a report", "create report"]):
        actions.append({"label": "Submit Safety Report", "path": "/reports/new"})

    # Fetch recent conversation transcript for context
    recent_msgs = []
    for m in conv.messages[-6:]:
        recent_msgs.append({"sender": m.sender, "content": m.content})

    # Call LLM service
    response_text = llm_service.call_llm(
        prompt=message_text,
        context_data=context_data if context_data else None,
        conversation_history=recent_msgs
    )

    # Save Assistant Message to DB
    assistant_msg = ChatMessage(
        conversation_id=conv.id,
        sender="assistant",
        content=response_text,
        sources_json=json.dumps(sources) if sources else None,
        actions_json=json.dumps(actions) if actions else None,
        created_at=utc_now()
    )
    db.add(assistant_msg)
    
    # Update conversation title based on first user query if generic
    if conv.title == "HSE Safety Assistant Chat" or conv.title == "Safety Assistant Chat":
        conv.title = message_text[:40] + ("..." if len(message_text) > 40 else "")
    
    conv.updated_at = utc_now()
    db.commit()

    return {
        "conversation_id": conv.id,
        "message": response_text,
        "sources": sources,
        "actions": actions
    }
