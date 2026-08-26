"""
HTTP API exposing the OrientAI conversational agent (llm/agent.py) to the
frontend.

Sessions live only in memory (ConversationManager's dict), keyed by
session_id: there's no persistence layer, so restarting this server drops
all conversations, matching the frontend's "one session per page load"
model.

Run from the repo root with:
    uvicorn api.main:app --reload --port 8000
"""

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from llm.agent import ConversationManager

load_dotenv()

_DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:4173,http://127.0.0.1:4173"
)
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip()
]

app = FastAPI(title="OrientAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/api/files", StaticFiles(directory="data/sources"), name="files")

manager = ConversationManager()


class ChatRequest(BaseModel):
    session_id: str
    message: str


class Source(BaseModel):
    source_id: str
    file: str
    title: str
    url: str | None = None


class Step(BaseModel):
    id: str
    tool: str
    args: dict[str, Any]
    result: str


class ChatResponse(BaseModel):
    reply: str
    sources: list[Source]
    steps: list[Step]


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat")
def chat(request_ctx: Request, request: ChatRequest) -> ChatResponse:
    session = manager.get_or_create(request.session_id)
    reply, sources, steps = session.send(request.message)
    
    for s in sources:
        if not s.get("url") and s.get("file"):
            filename = os.path.basename(s["file"])
            s["url"] = f"{str(request_ctx.base_url).rstrip('/')}/api/files/{filename}"
            
    return ChatResponse(
        reply=reply,
        sources=[Source(**s) for s in sources],
        steps=[Step(**s) for s in steps],
    )
