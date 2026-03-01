"""LangGraph ReAct agent wired to OpenRouter LLM and infrastructure tools."""

import logging

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from config import app_config, settings
from prompts.system_prompt import build_system_prompt
from tools import get_all_tools

logger = logging.getLogger(__name__)

_llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.openrouter_api_key,
    model=app_config.llm.model,
    temperature=app_config.llm.temperature,
)

_memory = MemorySaver()

_agent = create_react_agent(
    model=_llm,
    tools=get_all_tools(),
    checkpointer=_memory,
    state_modifier=SystemMessage(content=build_system_prompt()),
)


async def get_agent_response(user_message: str, thread_id: str) -> str:
    """Invoke the agent and return the final text response.

    Thread ID is the LangGraph checkpoint key — conversation history
    is maintained separately per Telegram chat.
    """
    config = {"configurable": {"thread_id": thread_id}}
    try:
        result = await _agent.ainvoke(
            {"messages": [{"role": "user", "content": user_message}]},
            config=config,
        )
        return result["messages"][-1].content
    except Exception:
        logger.exception("Agent error for thread %s", thread_id)
        raise
