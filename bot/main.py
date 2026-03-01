"""Telegram bot entry point — aiogram 3.x."""

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, Message
from openai import APIConnectionError, APIStatusError

from agent import get_agent_response, reset_thread
from config import app_config, settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(token=settings.telegram_token)
dp = Dispatcher()

_TG_MAX_LENGTH = 4096


def _is_allowed(user_id: int) -> bool:
    if not settings.allowed_user_ids:
        return True
    return user_id in settings.allowed_user_ids


def _split_message(text: str) -> list[str]:
    chunks = []
    while text:
        chunks.append(text[:_TG_MAX_LENGTH])
        text = text[_TG_MAX_LENGTH:]
    return chunks


async def _safe_send(message: Message, text: str) -> None:
    """Send a message, falling back to plain text if HTML is invalid."""
    for parse_mode in ("HTML", None):
        try:
            await message.answer(text, parse_mode=parse_mode)
            return
        except Exception:
            if parse_mode is None:
                raise


async def _keep_typing(chat_id: int, stop: asyncio.Event) -> None:
    """Send 'typing' action every 4s until stop is set.

    Telegram's typing indicator disappears after 5s, so we refresh it
    periodically to keep it visible while the agent is thinking.
    """
    while not stop.is_set():
        try:
            await bot.send_chat_action(chat_id, "typing")
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop.wait(), timeout=4)
        except asyncio.TimeoutError:
            pass


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        return
    await message.answer(
        "Привет! Я DevOps-ассистент для твоей инфраструктуры.\n\n"
        "Спрашивай про серверы:\n"
        "• <code>vdsina-netherlands</code> — VPS в Нидерландах\n"
        "• <code>aeza-germany</code> — VPS в Германии\n"
        "• <code>servers-helper</code> — домашний сервер\n\n"
        "Примеры: «что с германией?», «покажи контейнеры на vdsina», «перезапусти nginx на germany»",
        parse_mode="HTML",
    )


@dp.message(Command("reset"))
async def cmd_reset(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        return
    reset_thread(str(message.chat.id))
    await message.answer("История диалога очищена. Начинаем с чистого листа.")


@dp.message(F.text)
async def handle_message(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        logger.warning("Blocked unauthorized user %s", message.from_user.id)
        return

    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(_keep_typing(message.chat.id, stop_typing))

    try:
        response = await get_agent_response(
            user_message=message.text,
            thread_id=str(message.chat.id),
        )
        for chunk in _split_message(response):
            await _safe_send(message, chunk)

    except APIConnectionError:
        logger.error("OpenRouter unreachable after retries for user %s", message.from_user.id)
        await message.answer("⚠️ OpenRouter недоступен после нескольких попыток. Попробуй позже.")
    except APIStatusError as exc:
        logger.error("OpenRouter API error %s for user %s", exc.status_code, message.from_user.id)
        await message.answer(f"⚠️ Ошибка API ({exc.status_code}): {exc.message}")
    except Exception as exc:
        logger.exception("Unhandled error for user %s", message.from_user.id)
        await message.answer(f"❌ Неожиданная ошибка: {type(exc).__name__}")
    finally:
        stop_typing.set()
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass


async def main() -> None:
    await bot.set_my_commands([
        BotCommand(command="start", description="Начало работы"),
        BotCommand(command="reset", description="Очистить историю диалога"),
    ])
    logger.info("Bot started. Model: %s", app_config.llm.model)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
