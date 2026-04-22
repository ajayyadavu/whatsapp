# app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import webhook
from app.api.v1.endpoints import (
    chat, upload, lead, whatsapp, whatsapp_admin, ingest, auth, logs, flow_chat
)

api_router = APIRouter()
api_router.include_router(auth.router,            tags=["Auth"])
api_router.include_router(chat.router,            prefix="/chat",            tags=["Chat"])
api_router.include_router(flow_chat.router,       prefix="/flow-chat",       tags=["Flow Chat"])
api_router.include_router(upload.router,          prefix="/upload",          tags=["Upload"])
api_router.include_router(lead.router,            prefix="/lead",            tags=["Lead"])
api_router.include_router(whatsapp.router,        prefix="/whatsapp",        tags=["WhatsApp"])
api_router.include_router(whatsapp_admin.router,  prefix="/whatsapp-admin",  tags=["WhatsApp Admin"])
api_router.include_router(ingest.router,          prefix="/ingest",          tags=["Ingest"])
api_router.include_router(logs.router,            prefix="/logs",            tags=["Logs"])
api_router.include_router(webhook.router)
