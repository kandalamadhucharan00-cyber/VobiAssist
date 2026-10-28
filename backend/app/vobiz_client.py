from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from app.config import settings


async def test_vobiz_connectivity() -> dict[str, Any]:
    if not settings.vobiz_auth_id or not settings.vobiz_auth_token:
        return {
            "ok": False,
            "status_code": None,
            "endpoint": "not-configured",
            "duration_ms": 0,
            "message": "Vobiz credentials are not configured.",
            "response_preview": None,
            "error": "Missing auth environment variables.",
        }

    base_url = settings.vobiz_base_url.rstrip("/")
    candidate_endpoints = [
        f"{base_url}/api/v1/Account/{settings.vobiz_auth_id}/",
        f"{base_url}/api/v1/Account/{settings.vobiz_auth_id}",
    ]
    headers = {"X-Auth-ID": settings.vobiz_auth_id, "X-Auth-Token": settings.vobiz_auth_token}

    for endpoint in candidate_endpoints:
        try:
            timeout = httpx.Timeout(10.0, connect=5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                start = asyncio.get_running_loop().time()
                response = await client.get(endpoint, headers=headers)
                elapsed = int((asyncio.get_running_loop().time() - start) * 1000)
                body = response.text[:400]
                preview = body.replace(settings.vobiz_auth_token, "[REDACTED]") if settings.vobiz_auth_token else body
                if response.status_code in (200, 201, 202):
                    return {
                        "ok": True,
                        "status_code": response.status_code,
                        "endpoint": endpoint,
                        "duration_ms": elapsed,
                        "message": "Vobiz account endpoint responded successfully.",
                        "response_preview": preview,
                        "error": None,
                    }
                if response.status_code in (401, 403, 429):
                    return {
                        "ok": False,
                        "status_code": response.status_code,
                        "endpoint": endpoint,
                        "duration_ms": elapsed,
                        "message": "The request reached Vobiz but authentication or permission failed.",
                        "response_preview": preview,
                        "error": f"HTTP {response.status_code}",
                    }
                return {
                    "ok": False,
                    "status_code": response.status_code,
                    "endpoint": endpoint,
                    "duration_ms": elapsed,
                    "message": "Unexpected response from the Vobiz account endpoint.",
                    "response_preview": preview,
                    "error": f"HTTP {response.status_code}",
                }
        except httpx.HTTPError as exc:
            last_error = str(exc)
    return {
        "ok": False,
        "status_code": None,
        "endpoint": candidate_endpoints[-1],
        "duration_ms": 0,
        "message": "Could not reach the Vobiz API.",
        "response_preview": None,
        "error": last_error if 'last_error' in locals() else "Network error",
    }


async def create_real_call(from_number: str, to_number: str, answer_url: str) -> dict[str, Any]:
    if not settings.enable_real_calls:
        return {
            "ok": False,
            "status_code": 403,
            "message": "Real calls are disabled by default. Set ENABLE_REAL_CALLS=true and confirm before placing a live call.",
            "error": "Disabled by config",
            "response_preview": None,
        }

    endpoint = f"{settings.vobiz_base_url.rstrip('/')}/api/v1/Account/{settings.vobiz_auth_id}/Call/"
    headers = {"X-Auth-ID": settings.vobiz_auth_id, "X-Auth-Token": settings.vobiz_auth_token}
    payload = {"from": from_number, "to": to_number, "answer_url": answer_url}

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(12.0)) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
        return {
            "ok": response.status_code in (200, 201, 202),
            "status_code": response.status_code,
            "message": "Call request submitted." if response.status_code in (200, 201, 202) else "Call request failed.",
            "endpoint": endpoint,
            "response_preview": response.text[:500],
            "error": None if response.status_code in (200, 201, 202) else f"HTTP {response.status_code}",
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "status_code": None, "message": "Could not reach the Vobiz call API.", "endpoint": endpoint, "response_preview": None, "error": str(exc)}
