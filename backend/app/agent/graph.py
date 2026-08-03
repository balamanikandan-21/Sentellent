from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agent.state import AgentState


def _routing_decision(state: AgentState) -> str:
    query_type = state.get("query_type", "research")
    if query_type == "greeting":
        return "response"
    if query_type == "recommendation":
        return "recommend"
    return "analysis"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("router", _placeholder)
    graph.add_node("retrieve", _placeholder)
    graph.add_node("memory", _placeholder)
    graph.add_node("persona", _placeholder)
    graph.add_node("analysis", _placeholder)
    graph.add_node("recommend", _placeholder)
    graph.add_node("citation", _placeholder)
    graph.add_node("response", _placeholder)
    graph.add_node("memory_update", _placeholder)
    graph.add_node("sentiment_update", _placeholder)

    graph.set_entry_point("router")

    graph.add_edge("router", "retrieve")
    graph.add_edge("router", "memory")
    graph.add_edge("router", "persona")

    graph.add_conditional_edges(
        "retrieve",
        _routing_decision,
        {
            "greeting": "response",
            "recommend": "recommend",
            "analysis": "analysis",
        },
    )

    graph.add_edge("analysis", "citation")
    graph.add_edge("recommend", "citation")
    graph.add_edge("citation", "response")
    graph.add_edge("response", "memory_update")
    graph.add_edge("memory_update", "sentiment_update")
    graph.add_edge("sentiment_update", END)

    return graph


async def _placeholder(state: AgentState) -> AgentState:
    return state
