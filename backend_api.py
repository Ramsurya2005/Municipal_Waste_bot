"""
FastAPI backend adapter for Municipal Chatbot frontend.
Provides /api/chat and /api/history endpoints expected by the Next.js UI.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from smart_chatbot import SmartChatbot


class ChatRequest(BaseModel):
    message: str
    session_id: str
    attachment: Optional[Dict[str, Any]] = None


class ChatHistoryItem(BaseModel):
    role: str
    content: str
    timestamp: str


app = FastAPI(title="Municipal Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chatbot = SmartChatbot()
session_history: Dict[str, List[ChatHistoryItem]] = {}


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "ai_available": bool(getattr(chatbot, "ai_available", False)),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/api/chat")
def chat(payload: ChatRequest) -> Dict[str, Any]:
    user_message = payload.message.strip()
    if not user_message:
        return {
            "reply": "Please enter a message.",
            "session_id": payload.session_id,
            "metadata": {},
        }

    attachment_context = ""
    if payload.attachment:
        attachment_name = payload.attachment.get("name", "uploaded-image")
        attachment_type = payload.attachment.get("type", "image")
        attachment_size = payload.attachment.get("size", 0)
        attachment_context = (
            f"\n\n[User uploaded image: {attachment_name}, type={attachment_type}, size={attachment_size} bytes]"
        )

    result = chatbot.chat(f"{user_message}{attachment_context}")
    assistant_reply = str(result.get("message", "I could not generate a response right now."))

    if payload.session_id not in session_history:
        session_history[payload.session_id] = []

    session_history[payload.session_id].append(
        ChatHistoryItem(
            role="user",
            content=user_message,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    )
    session_history[payload.session_id].append(
        ChatHistoryItem(
            role="assistant",
            content=assistant_reply,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    )

    metadata: Dict[str, Any] = {
        "service_type": result.get("service_type"),
        "department": result.get("department"),
        "complaint_id": result.get("complaint_id"),
        "extracted_info": result.get("extracted_info") or {},
        "follow_up_questions": result.get("follow_up_questions") or [],
        "attachment": payload.attachment,
    }

    return {
        "reply": assistant_reply,
        "session_id": payload.session_id,
        "metadata": metadata,
    }


@app.get("/api/history")
def history(session_id: str) -> List[Dict[str, Any]]:
    items = session_history.get(session_id, [])
    return [item.model_dump() for item in items]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend_api:app", host="0.0.0.0", port=5000, reload=True)
