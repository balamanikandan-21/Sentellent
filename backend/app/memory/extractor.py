from __future__ import annotations

import json
from dataclasses import dataclass

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.config.settings import get_settings

logger = structlog.get_logger()

EXTRACTION_PROMPT = """\
Analyze this conversation turn and extract ANY investment-related preferences, \
constraints, or profile information the user has shared — whether explicit or implied.

Extract into these categories (only include categories where you find signal):

1. risk_appetite: "conservative", "moderate", "aggressive" — or a nuanced description
2. investment_style: "value", "growth", "dividend", "index", "momentum", "swing", \
"day_trading", "buy_and_hold" etc.
3. sector_preferences: sectors they're interested in (IT, pharma, banking, FMCG, etc.)
4. investment_goals: what they're trying to achieve (retirement, wealth building, \
passive income, etc.)
5. avoided_stocks: specific tickers or companies they want to avoid, or have expressed \
negative sentiment about repeatedly
6. preferred_stocks: specific tickers or companies they like, follow closely, or have \
expressed positive sentiment about
7. general: any other investment-relevant preference (e.g., "prefers large caps", \
"doesn't trust IPOs", "interested in ESG")

Also detect if the user is CORRECTING or OVERRIDING a previous preference — if so, \
set "supersedes" to describe what it replaces.

Return ONLY valid JSON:
{{
  "memories": [
    {{
      "category": "<category>",
      "content": "<clear, concise statement of the preference>",
      "confidence": <0.0-1.0>,
      "supersedes": "<what this replaces, or null>"
    }}
  ]
}}

If no investment preferences are found, return: {{"memories": []}}

User message: {query}
Recent conversation:
{history}
"""


@dataclass
class ExtractedMemory:
    category: str
    content: str
    confidence: float
    supersedes: str | None = None


async def extract_memories(
    query: str,
    chat_history: list[dict],
) -> list[ExtractedMemory]:
    settings = get_settings()
    llm = ChatAnthropic(
        model=settings.TAGGING_MODEL,
        api_key=settings.ANTHROPIC_API_KEY,
        max_tokens=1024,
        temperature=0,
    )

    history_text = "\n".join(f"{m['role']}: {m['content'][:150]}" for m in chat_history[-6:])

    response = await llm.ainvoke(
        [
            SystemMessage(
                content="You extract investment preferences from conversations. "
                "Be precise — only extract what the user actually said or clearly implied."
            ),
            HumanMessage(content=EXTRACTION_PROMPT.format(query=query, history=history_text)),
        ]
    )

    raw = response.content if isinstance(response.content, str) else str(response.content)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("memory_extraction_parse_failed", raw=raw[:200])
        return []

    memories_data = parsed.get("memories", [])
    if not isinstance(memories_data, list):
        return []

    valid_categories = {
        "risk_appetite",
        "investment_style",
        "sector_preferences",
        "investment_goals",
        "avoided_stocks",
        "preferred_stocks",
        "general",
    }

    extracted: list[ExtractedMemory] = []
    for item in memories_data:
        category = item.get("category", "")
        content = item.get("content", "")
        confidence = float(item.get("confidence", 0.5))

        if category not in valid_categories or not content:
            continue

        extracted.append(
            ExtractedMemory(
                category=category,
                content=content,
                confidence=min(max(confidence, 0.1), 1.0),
                supersedes=item.get("supersedes"),
            )
        )

    logger.info("memories_extracted", count=len(extracted))
    return extracted
