from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.nodes.analysis import stock_analysis
from app.agent.nodes.citation import attach_citations
from app.agent.nodes.memory import retrieve_memory
from app.agent.nodes.memory_update import update_memory
from app.agent.nodes.persona import retrieve_persona
from app.agent.nodes.recommend import generate_recommendation
from app.agent.nodes.response import generate_response
from app.agent.nodes.retrieve import retrieve_documents
from app.agent.nodes.router import route_query
from app.agent.nodes.sentiment import update_sentiment
from app.agent.state import AgentState
from app.repositories.chat import ChatRepository

logger = structlog.get_logger()


class AgentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def process_message(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        query: str,
    ) -> AgentState:
        state: AgentState = {
            "user_id": user_id,
            "session_id": session_id,
            "query": query,
        }

        chat_repo = ChatRepository(self.db)
        await chat_repo.add_message(session_id, "user", query)
        await self.db.commit()

        logger.info("agent_processing", user_id=str(user_id), query=query[:100])

        state = await route_query(state)

        state = await retrieve_documents(state, self.db)
        state = await retrieve_memory(state, self.db)
        state = await retrieve_persona(state, self.db)

        query_type = state.get("query_type", "research")

        if query_type == "recommendation":
            state = await generate_recommendation(state)
        elif query_type != "greeting":
            state = await stock_analysis(state)

        if query_type != "greeting":
            state = await attach_citations(state, self.db)

        state = await generate_response(state)

        state = await update_memory(state, self.db)
        state = await update_sentiment(state, self.db)

        response_text = state.get("response", "")
        citations = state.get("citations", [])
        confidence = state.get("confidence_score", 0.0)

        await chat_repo.add_message(
            session_id,
            "assistant",
            response_text,
            citations=[dict(c) for c in citations] if citations else None,
        )
        await self.db.commit()

        if state.get("recommendation") and query_type == "recommendation":
            from app.repositories.recommendation import RecommendationRepository

            rec_repo = RecommendationRepository(self.db)
            rec = state["recommendation"]
            scores = {
                "retrieval_confidence": rec.get("retrieval_confidence", 0),
                "composite_score": rec.get("composite_score", 0),
            }
            if rec.get("scorecard"):
                scores["scorecard"] = rec["scorecard"]
            await rec_repo.create(
                user_id=user_id,
                ticker_symbol=rec["ticker"],
                session_id=session_id,
                action=rec["action"],
                confidence=rec["confidence"],
                scores=scores,
                reasoning=rec["reasoning"],
            )
            await self.db.commit()

        logger.info(
            "agent_complete",
            query_type=query_type,
            citations=len(citations),
            response_length=len(response_text),
            confidence=round(confidence, 3),
            retrieval_method=state.get("retrieval_method", "none"),
        )

        return state
