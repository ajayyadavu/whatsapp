# app/api/v1/endpoints/chat.py
# Legacy endpoint — proxies to /flow-chat/ (single source of truth).

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Optional

from app.api.v1.endpoints.flow_chat import flow_chat, FlowChatRequest

router = APIRouter()


class ChatRequest(BaseModel):
    message:    str
    session_id: Optional[str] = None


@router.post("/", response_class=PlainTextResponse)
def chat(req: ChatRequest, request: Request):
    """
    /api/v1/chat/ now mirrors /api/v1/flow-chat/ exactly.
    Both URLs return identical responses.
    """
    return flow_chat(
        FlowChatRequest(
            message=req.message,
            session_id=req.session_id,
        ),
        request=request,
    )
