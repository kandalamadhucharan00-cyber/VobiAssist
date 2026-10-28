from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    response: str
    mode: str = "rules"


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    config: dict[str, Any]


class ConfigStatusResponse(BaseModel):
    version: str
    health: str
    vobiz_configured: bool
    vobiz_base_url: str
    ai_provider: str
    ollama_available: bool
    real_calls_enabled: bool


class CallEventRequest(BaseModel):
    call_id: str | None = None
    source: str | None = None
    destination: str | None = None
    status: str | None = None
    search: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class WebhookPayload(BaseModel):
    event_id: str | None = None
    event_type: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ConnectionTestResponse(BaseModel):
    ok: bool
    status_code: int | None = None
    endpoint: str
    duration_ms: int | None = None
    message: str
    response_preview: str | None = None
    error: str | None = None


class CallCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_number: str = Field(..., alias="from", min_length=5)
    to_number: str = Field(..., alias="to", min_length=5)
    answer_url: str = Field(..., min_length=5)
    confirm: bool = False
