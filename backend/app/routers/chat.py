from fastapi import APIRouter

from app.models.chat import ChatRequest, ChatResponse
from app.services.chat import chat

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat_endpoint(body: ChatRequest):
    return await chat(body.messages)
