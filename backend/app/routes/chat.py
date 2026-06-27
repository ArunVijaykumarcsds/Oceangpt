from fastapi import APIRouter, HTTPException

from app.chat.agent import run_agent_turn
from app.models import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        reply, sources = await run_agent_turn(request.message, request.history)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Agent error: {exc}") from exc

    return ChatResponse(reply=reply, sources=sources)
