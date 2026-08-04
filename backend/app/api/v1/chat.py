from __future__ import annotations

import json
import uuid

import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.service import AgentService
from app.api.deps import get_chat_repo, get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.repositories.chat import ChatRepository

logger = structlog.get_logger()

router = APIRouter(prefix="/chat", tags=["chat"])


def _sse(payload: dict) -> str:
    """Serialize one Server-Sent Events frame."""
    return f"data: {json.dumps(payload)}\n\n"


class MessageRequest(BaseModel):
    content: str


class SessionResponse(BaseModel):
    id: str
    title: str | None
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    citations: list[dict] | None
    created_at: str


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    user: User = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(get_chat_repo),
):
    sessions = await chat_repo.list_sessions(user.id)
    return [
        SessionResponse(
            id=str(s.id),
            title=s.title,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
        )
        for s in sessions
    ]


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    user: User = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(get_chat_repo),
    db: AsyncSession = Depends(get_db),
):
    session = await chat_repo.create_session(user.id)
    await db.commit()
    return SessionResponse(
        id=str(session.id),
        title=session.title,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )


@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(get_chat_repo),
):
    session = await chat_repo.get_session(session_id, user.id)
    if not session:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Chat session not found")

    messages = await chat_repo.get_messages(session_id)
    return [
        MessageResponse(
            id=str(m.id),
            session_id=str(m.session_id),
            role=m.role,
            content=m.content,
            citations=m.citations,
            created_at=m.created_at.isoformat(),
        )
        for m in messages
    ]


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: uuid.UUID,
    body: MessageRequest,
    user: User = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(get_chat_repo),
    db: AsyncSession = Depends(get_db),
):
    session = await chat_repo.get_session(session_id, user.id)
    if not session:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Chat session not found")

    agent = AgentService(db)

    async def event_stream():
        yield _sse({"type": "start"})
        try:
            state = await agent.process_message(user.id, session_id, body.content)
            response_text = state.get("response", "")
            citations = state.get("citations", [])

            yield _sse({"type": "content", "content": response_text})

            if citations:
                yield _sse({"type": "citations", "citations": citations})

            confidence = state.get("confidence_score", 0.0)
            yield _sse(
                {
                    "type": "metadata",
                    "confidence": round(confidence, 3),
                    "retrieval_method": state.get("retrieval_method", ""),
                    "sources_count": len(citations),
                }
            )

            rec = state.get("recommendation")
            if rec and rec.get("scorecard"):
                yield _sse({"type": "scorecard", "scorecard": rec["scorecard"]})

            yield _sse({"type": "done"})
        except Exception:
            logger.exception("agent_error", session_id=str(session_id))
            yield _sse(
                {
                    "type": "error",
                    "error": (
                        "Something went wrong while generating the response. Please try again."
                    ),
                }
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(get_chat_repo),
    db: AsyncSession = Depends(get_db),
):
    session = await chat_repo.get_session(session_id, user.id)
    if not session:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Chat session not found")

    await chat_repo.delete_session(session)
    await db.commit()
