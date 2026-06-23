"""Build the LangGraph ``StateGraph`` that drives the agent."""

from __future__ import annotations

from langgraph.constants import END
from langgraph.graph import StateGraph

from l2dllm.agents.nodes import agent_node, build_tool_node, route_after_agent
from l2dllm.agents.state import AgentState


def build_agent_graph(model, tools, system_prompt: str):
    """Construct a compiled LangGraph agent.

    The graph looks like::

        agent →─ has tool_calls? ──→ tools →─→ agent
                 └─ no tool_calls ─→ END

    Parameters
    ----------
    model : BaseChatModel
        A LangChain chat model (not yet bound to tools; binding happens here).
    tools : list[BaseTool]
        Tools the agent can invoke.
    system_prompt : str
        System prompt injected on the first turn.
    """
    # Bind tools to the model so it knows about them.
    model_with_tools = model.bind_tools(tools) if tools else model

    g = StateGraph(AgentState)

    g.add_node("agent", agent_node(model_with_tools, system_prompt))
    g.add_node("tools", build_tool_node(tools))

    g.set_entry_point("agent")

    g.add_conditional_edges(
        "agent",
        route_after_agent,
        {"tools": "tools", END: END},
    )

    g.add_edge("tools", "agent")

    return g.compile()