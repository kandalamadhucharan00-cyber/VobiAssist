from __future__ import annotations

import re


def mask_phone(value: str | None) -> str:
    if not value:
        return "unknown"
    digits = re.sub(r"\D", "", value)
    if len(digits) <= 4:
        return "*" * max(len(digits), 1)
    if len(digits) <= 8:
        return "***" + digits[-2:]
    return "***" + digits[-4:]


def answer_user_question(message: str) -> str:
    text = (message or "").strip()
    lower = text.lower()

    if any(x in lower for x in ["401", "unauthorized", "invalid auth", "missing auth", "x-auth-id"]):
        return (
            "HTTP 401 usually means the Vobiz credentials are missing, expired, or being sent to the wrong endpoint. "
            "Verify the X-Auth-ID and X-Auth-Token headers, ensure the account ID matches the target auth_id, and check the exact API base URL. "
            "Also confirm the request is not being routed to a different domain or sub-account without permissions."
        )

    if any(x in lower for x in ["403", "access denied", "forbidden", "not allowed"]):
        return (
            "HTTP 403 usually indicates the account or token is valid but the action is not permitted. Check whether the account has the right subscription, whether the phone number is owned by the account, and whether the call or API action is supported for that auth_id."
        )

    if any(x in lower for x in ["429", "rate limit", "too many requests"]):
        return (
            "HTTP 429 means the account or IP hit a rate limit. Back off, respect Retry-After if present, and batch calls or retries more slowly. For Vobiz, check CPS or concurrency limits and avoid immediate retry storms."
        )

    if any(x in lower for x in ["5xx", "server error", "internal error", "upstream"]) or "500" in lower or "503" in lower:
        return (
            "A 5xx response usually points to the provider or an upstream dependency, not your credentials. Retry with backoff, inspect logs, and check the Vobiz status page if the issue is widespread."
        )

    if any(x in lower for x in ["outbound call", "make call", "call failed", "call creation", "call api"]):
        return (
            "For an outbound call, validate the destination number, the from number ownership, the answer_url, and the account permissions. A common issue is using an unowned caller ID or an invalid default route. The API call should use the documented POST /api/v1/Account/{auth_id}/Call/ pattern with X-Auth-ID and X-Auth-Token."
        )

    if any(x in lower for x in ["sip", "rtp", "one-way audio", "no audio", "trunk"]):
        return (
            "SIP handles signaling, while RTP carries the actual audio. If a call connects but there is no audio, investigate NAT/firewall rules, RTP path reachability, SIP trunk allowlisting, and codec compatibility. Do not assume a credential issue unless the provider explicitly returned one."
        )

    if any(x in lower for x in ["webhook", "duplicate event", "callback"]):
        return (
            "Webhook delivery should be treated as idempotent. Store each event_id and reject or ignore duplicates. Log the sanitized payload, check the provider signature if available, and make sure your public endpoint is reachable and not timing out."
        )

    if any(x in lower for x in ["websocket", "audio format", "streaming"]):
        return (
            "WebSocket audio streaming issues commonly come from codec mismatch or a wrong sample rate. Verify the media format is compatible with the endpoint and confirm the route is not dropping RTP or PCM payloads."
        )

    if any(x in lower for x in ["sub-account", "partner", "child account"]):
        return (
            "Sub-accounts and partner accounts often require careful auth_id selection and permission checks. Make sure the request uses the correct account context and that any owned numbers or trunks belong to the same account scope."
        )

    if any(x in lower for x in ["jpg", "hello"]):
        return "I can help with Vobiz authentication, SIP/RTP, webhooks, outbound call errors, and API troubleshooting. Ask about a 401/403/429, a failed outbound call, or a call with no audio."

    return (
        "I can help with Vobiz API authentication, outbound-call troubleshooting, SIP/RTP issues, WebSocket audio, and webhook validation. "
        "If you want the shortest path: check the auth headers, verify the account and caller IDs, and inspect the exact provider status code and error body."
    )
