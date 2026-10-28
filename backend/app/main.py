from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.config import settings
from app.db import (
    add_api_error,
    add_call_event,
    count_events,
    get_api_errors,
    get_call_event,
    initialize_db,
    list_call_events,
    list_webhook_events,
    record_webhook_event,
)
from app.schemas import (
    CallCreateRequest,
    CallEventRequest,
    ChatRequest,
    ChatResponse,
    ConfigStatusResponse,
    ConnectionTestResponse,
    HealthResponse,
    WebhookPayload,
)
from app.support_engine import answer_user_question, mask_phone
from app.vobiz_client import create_real_call, test_vobiz_connectivity

app = FastAPI(title="VobiAssist", version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_db()


@app.get('/api/health', response_model=HealthResponse)
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "config": {
            "ai_provider": settings.ai_provider,
            "vobiz_configured": bool(settings.vobiz_auth_id and settings.vobiz_auth_token),
            "real_calls_enabled": settings.enable_real_calls,
        },
    }


@app.post('/api/chat', response_model=ChatResponse)
def chat(payload: ChatRequest) -> dict[str, str]:
    return {"response": answer_user_question(payload.message), "mode": "rules"}


@app.get('/api/config', response_model=ConfigStatusResponse)
def get_config_status() -> dict[str, Any]:
    return {
        "version": settings.app_version,
        "health": "ok",
        "vobiz_configured": bool(settings.vobiz_auth_id and settings.vobiz_auth_token),
        "vobiz_base_url": settings.vobiz_base_url,
        "ai_provider": settings.ai_provider,
        "ollama_available": False,
        "real_calls_enabled": settings.enable_real_calls,
    }


@app.get('/api/vobiz/test-connection', response_model=ConnectionTestResponse)
async def test_connection() -> dict[str, Any]:
    result = await test_vobiz_connectivity()
    return result


@app.post('/api/vobiz/call', response_model=dict)
async def create_call(payload: CallCreateRequest) -> dict[str, Any]:
    if not settings.enable_real_calls:
        raise HTTPException(status_code=403, detail='Real calls are disabled by default in this local demo. Set ENABLE_REAL_CALLS=true and confirm before making a live call.')
    if not payload.confirm:
        raise HTTPException(status_code=400, detail='Confirmation required before a real call can be placed.')
    result = await create_real_call(payload.from_number, payload.to_number, payload.answer_url)
    if not result['ok']:
        raise HTTPException(status_code=400, detail=result['message'])
    return result


@app.get('/api/calls', response_model=list[dict[str, Any]])
def list_calls(
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    events = list_call_events(limit=limit, status=status, search=search)
    for event in events:
        event['source_number'] = mask_phone(event.get('source_number'))
        event['destination_number'] = mask_phone(event.get('destination_number'))
    return events


@app.get('/api/calls/summary')
def get_call_summary() -> dict[str, int]:
    return count_events()


@app.get('/api/calls/{call_id}')
def get_call(call_id: str) -> dict[str, Any]:
    row = get_call_event(call_id)
    if not row:
        raise HTTPException(status_code=404, detail='Call event not found.')
    row['source_number'] = mask_phone(row.get('source_number'))
    row['destination_number'] = mask_phone(row.get('destination_number'))
    return row


@app.post('/api/webhooks/receive')
def receive_webhook(payload: WebhookPayload) -> dict[str, Any]:
    event_id = payload.event_id or 'simulated-event'
    event_type = payload.event_type or 'call.completed'
    if not event_id:
        raise HTTPException(status_code=400, detail='event_id is required.')
    ok = record_webhook_event(event_id, event_type, 'local', 'accepted', payload.payload)
    if not ok:
        return {"status": "duplicate", "event_id": event_id, "message": "Duplicate event ignored."}
    return {"status": "accepted", "event_id": event_id, "message": "Webhook accepted."}


@app.post('/api/webhooks/simulate')
def simulate_webhook() -> dict[str, Any]:
    payload = {
        "event_id": "sim-001",
        "event_type": "call.completed",
        "payload": {"call_id": "call_123", "status": "completed"},
    }
    ok = record_webhook_event(payload['event_id'], payload['event_type'], 'simulator', 'accepted', payload['payload'])
    if not ok:
        return {"status": "duplicate", "event_id": payload['event_id'], "message": "Duplicate simulation ignored."}
    return {"status": "accepted", "event_id": payload['event_id'], "message": "Simulated webhook accepted."}


@app.get('/api/webhooks')
def get_webhooks() -> list[dict[str, Any]]:
    return list_webhook_events(limit=20)


@app.get('/api/errors')
def get_errors() -> list[dict[str, Any]]:
    return get_api_errors(limit=10)


@app.get('/api/troubleshooting')
def troubleshooting(query: str | None = None) -> dict[str, Any]:
    items = [
        {"id": "401", "category": "Authentication", "title": "HTTP 401 — invalid credentials", "content": "Check X-Auth-ID and X-Auth-Token and ensure the headers are correct."},
        {"id": "403", "category": "Permissions", "title": "HTTP 403 — access denied", "content": "The account exists, but the operation is restricted."},
        {"id": "429", "category": "Rate limits", "title": "HTTP 429 — rate limit exceeded", "content": "Back off and respect Retry-After."},
    ]
    if query:
        filtered = [item for item in items if query.lower() in item['title'].lower() or query.lower() in item['content'].lower()]
        return {"query": query, "items": filtered}
    return {"query": query, "items": items}


@app.get('/')
def root() -> dict[str, str]:
    return {"message": "VobiAssist backend is running."}
