"""LangGraph ReAct agent wired to OpenRouter LLM and infrastructure tools."""

import logging

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from openai import APIConnectionError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

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
    prompt=SystemMessage(content=build_system_prompt()),
)


def reset_thread(thread_id: str) -> None:
    """Delete all conversation history for a given chat."""
    config = {"configurable": {"thread_id": thread_id}}
    _memory.delete(config)
    logger.info("Conversation reset for thread %s", thread_id)


@retry(
    retry=retry_if_exception_type(APIConnectionError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def get_agent_response(user_message: str, thread_id: str) -> str:
    """Invoke the agent and return the final text response.

    Retries up to 3 times on connection errors (2s → 4s → 8s backoff).
    Thread ID is the LangGraph checkpoint key — conversation history
    is maintained separately per Telegram chat.
    """
    config = {"configurable": {"thread_id": thread_id}}
    result = await _agent.ainvoke(
        {"messages": [{"role": "user", "content": user_message}]},
        config=config,
    )
    return result["messages"][-1].content
