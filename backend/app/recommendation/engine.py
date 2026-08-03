from __future__ import annotations

import json

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.config.settings import get_settings
from app.recommendation.scorer import (
    score_dividend,
    score_fundamentals,
    score_growth,
    score_momentum,
    score_news_sentiment,
    score_persona_alignment,
    score_quality,
    score_risk,
    score_value,
)
from app.recommendation.types import RecommendationResult, ScoreCard

logger = structlog.get_logger()

ENGINE_PROMPT = """\
You are an expert Indian equity research analyst producing a structured recommendation.

STOCK: {ticker}
USER QUERY: {query}

=== MULTI-FACTOR SCORECARD ===
{scorecard_text}

Composite Score: {composite:.2f}/1.00 → {action}
Data Coverage: {coverage:.0%}

=== SOURCE DATA ===

Context documents (cite as [Source N]):
{context}

Fundamentals (cite as [Fundamentals]):
{fundamentals}

Investor profile:
{persona}

=== CRITICAL RULES ===
1. ALL monetary figures in INR (Rs.). Never USD.
2. Every factual claim MUST cite [Source N] or [Fundamentals].
3. If a factor has data_available=false, state "Data unavailable for this factor" — \
never fill gaps with assumptions.
4. The scorecard above is algorithmically derived. Your job is to EXPLAIN the scores, \
NOT override them, unless you find clear contradictions in the source data.
5. If retrieval confidence is below 35%, state: "Insufficient data in corpus to make \
this recommendation."
6. Frame as analysis, NOT financial advice: "Based on available data, the analysis suggests..."

=== OUTPUT FORMAT ===
Respond with valid JSON only:
{{
  "action": "BUY|HOLD|SELL",
  "confidence_score": <0.0-1.0>,
  "summary": "<1-2 sentence headline recommendation with key driver>",
  "factor_analysis": {{
    "fundamentals": "<2-3 sentences citing [Fundamentals]>",
    "news_sentiment": "<2-3 sentences citing [Source N]>",
    "persona_alignment": "<1-2 sentences>",
    "risk": "<1-2 sentences citing data>",
    "momentum": "<1-2 sentences citing data>",
    "dividend": "<1-2 sentences citing data>",
    "value": "<1-2 sentences citing data>",
    "growth": "<1-2 sentences citing data>",
    "quality": "<1-2 sentences citing data>"
  }},
  "key_risks": ["<risk1>", "<risk2>", "<risk3>"],
  "catalysts": ["<catalyst1>", "<catalyst2>"],
  "reasoning": "<3-5 sentence comprehensive reasoning tying factors together, with citations>"
}}
"""


class RecommendationEngine:
    def __init__(self) -> None:
        self.settings = get_settings()

    def compute_scorecard(
        self,
        ticker: str,
        fundamentals_data: dict | None,
        chunks: list[dict],
        retrieval_confidence: float,
        persona: dict | None,
    ) -> ScoreCard:
        info = {}
        financials = {}

        if fundamentals_data:
            info = fundamentals_data.get("info", fundamentals_data)
            financials = fundamentals_data.get("financials", {})
            info["symbol"] = ticker

        card = ScoreCard(ticker=ticker)
        card.factors = [
            score_fundamentals(info),
            score_news_sentiment(chunks, retrieval_confidence),
            score_persona_alignment(info, persona),
            score_risk(info),
            score_momentum(info),
            score_dividend(info),
            score_value(info),
            score_growth(info, financials),
            score_quality(info),
        ]

        logger.info(
            "scorecard_computed",
            ticker=ticker,
            composite=round(card.composite_score, 3),
            action=card.action,
            coverage=round(card.data_coverage, 2),
            factors_available=sum(1 for f in card.factors if f.data_available),
        )
        return card

    async def generate(
        self,
        ticker: str,
        scorecard: ScoreCard,
        context: str,
        fundamentals_text: str,
        persona_text: str,
        query: str,
        retrieval_confidence: float,
    ) -> RecommendationResult:
        if retrieval_confidence < self.settings.CONFIDENCE_THRESHOLD and scorecard.data_coverage < 0.3:
            return RecommendationResult(
                ticker=ticker,
                action="HOLD",
                composite_score=scorecard.composite_score,
                confidence=0.0,
                scorecard=scorecard,
                reasoning=(
                    "I don't have sufficient data in the corpus to make a reliable "
                    "recommendation for this stock. Please follow the ticker and wait "
                    "for data ingestion to complete."
                ),
                retrieval_confidence=retrieval_confidence,
            )

        scorecard_lines = []
        for f in scorecard.factors:
            status = "AVAILABLE" if f.data_available else "UNAVAILABLE"
            scorecard_lines.append(
                f"  {f.name}: score={f.score:.2f} weight={f.weight:.0%} "
                f"[{status}]\n    {f.reasoning}"
            )
            if f.sources:
                scorecard_lines.append(f"    Sources: {', '.join(f.sources)}")
        scorecard_text = "\n".join(scorecard_lines)

        prompt = ENGINE_PROMPT.format(
            ticker=ticker,
            query=query,
            scorecard_text=scorecard_text,
            composite=scorecard.composite_score,
            action=scorecard.action,
            coverage=scorecard.data_coverage,
            context=context,
            fundamentals=fundamentals_text,
            persona=persona_text,
        )

        llm = ChatAnthropic(
            model=self.settings.PRIMARY_MODEL,
            api_key=self.settings.ANTHROPIC_API_KEY,
            max_tokens=self.settings.LLM_MAX_TOKENS,
            temperature=0.2,
        )

        response = await llm.ainvoke([
            SystemMessage(
                content="You are an expert Indian equity research analyst. "
                "Respond ONLY with valid JSON."
            ),
            HumanMessage(content=prompt),
        ])

        raw = response.content if isinstance(response.content, str) else str(response.content)
        parsed = self._parse_response(raw, scorecard, ticker, retrieval_confidence)

        logger.info(
            "recommendation_generated",
            ticker=ticker,
            action=parsed.action,
            confidence=round(parsed.confidence, 3),
            composite=round(parsed.composite_score, 3),
        )
        return parsed

    def _parse_response(
        self,
        raw: str,
        scorecard: ScoreCard,
        ticker: str,
        retrieval_confidence: float,
    ) -> RecommendationResult:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()

        try:
            data = json.loads(clean)
        except json.JSONDecodeError:
            logger.warning("recommendation_parse_failed", raw=raw[:300])
            return RecommendationResult(
                ticker=ticker,
                action=scorecard.action,
                composite_score=scorecard.composite_score,
                confidence=scorecard.data_coverage * 0.5,
                scorecard=scorecard,
                reasoning=raw[:500],
                retrieval_confidence=retrieval_confidence,
            )

        action = data.get("action", scorecard.action).upper()
        if action not in ("BUY", "HOLD", "SELL"):
            action = scorecard.action

        confidence = float(data.get("confidence_score", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        factor_analysis = data.get("factor_analysis", {})
        key_risks = data.get("key_risks", [])
        catalysts = data.get("catalysts", [])
        summary = data.get("summary", "")
        reasoning = data.get("reasoning", "")

        full_reasoning = summary
        if reasoning:
            full_reasoning += f"\n\n{reasoning}"
        if key_risks:
            full_reasoning += "\n\nKey Risks: " + "; ".join(key_risks[:3])
        if catalysts:
            full_reasoning += "\nCatalysts: " + "; ".join(catalysts[:3])

        for factor_name, analysis in factor_analysis.items():
            matching = [f for f in scorecard.factors if f.name == factor_name]
            if matching and analysis:
                matching[0].reasoning = analysis

        return RecommendationResult(
            ticker=ticker,
            action=action,
            composite_score=scorecard.composite_score,
            confidence=confidence,
            scorecard=scorecard,
            reasoning=full_reasoning,
            retrieval_confidence=retrieval_confidence,
        )
