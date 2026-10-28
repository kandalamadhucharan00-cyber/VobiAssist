# VobiAssist Technology Stack

## Frontend

- React
- Vite
- TypeScript
- Tailwind CSS
- Lucide icons
- Recharts
- Browser SpeechRecognition and SpeechSynthesis APIs

## Backend

- Python 3.11+
- FastAPI
- Pydantic and Pydantic Settings
- HTTPX
- SQLite
- Pytest

## Why these choices

This stack keeps the local app fast to run, easy to inspect, and compatible with a support-engineering demo. The backend keeps secrets in environment variables and never exposes them to the browser. SQLite provides persistent local records for calls and webhooks, which is sufficient for a prototype and local developer workflow.

## Local runtime flow

Browser UI -> FastAPI backend -> VobiAssist support rules -> Vobiz connectivity adapter -> SQLite persistence

## Security notes

- Secret credentials live only in the backend `.env` file.
- The Vobiz API adapter uses `X-Auth-ID` and `X-Auth-Token` headers.
- Real calls remain disabled unless explicitly enabled.
- Webhook processing uses duplicate detection keyed by `event_id`.
