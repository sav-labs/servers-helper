"""Telegram bot entry point — aiogram 3.x."""

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import BotCommand, Message

from agent import get_agent_response
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(token=settings.telegram_token)
dp = Dispatcher()

# Telegram message length limit
_TG_MAX_LENGTH = 4096


def _is_allowed(user_id: int) -> bool:
    if not settings.allowed_user_ids:
        return True
    return user_id in settings.allowed_user_ids


def _split_message(text: str) -> list[str]:
    """Split long text into Telegram-sized chunks."""
    chunks = []
    while text:
        chunks.append(text[:_TG_MAX_LENGTH])
        text = text[_TG_MAX_LENGTH:]
    return chunks


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        return
    await message.answer(
        "Привет! Я DevOps-ассистент для твоей инфраструктуры.\n\n"
        "Спрашивай про серверы:\n"
        "• *vdsina-netherlands* — VPS в Нидерландах\n"
        "• *aeza-germany* — VPS в Германии\n"
        "• *servers-helper* — домашний сервер\n\n"
        "Примеры: «что с германией?», «покажи контейнеры на vdsina», «перезапусти nginx на germany»",
        parse_mode="Markdown",
    )


@dp.message(F.text)
async def handle_message(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        logger.warning("Blocked unauthorized user %s", message.from_user.id)
        return

    await bot.send_chat_action(message.chat.id, "typing")
    status_msg = await message.answer("⏳ Думаю...")

    try:
        response = await get_agent_response(
            user_message=message.text,
            thread_id=str(message.chat.id),
        )

        chunks = _split_message(response)
        await status_msg.edit_text(chunks[0], parse_mode="Markdown")
        for chunk in chunks[1:]:
            await message.answer(chunk, parse_mode="Markdown")

    except Exception as exc:
        logger.exception("Unhandled error for user %s", message.from_user.id)
        await status_msg.edit_text(f"❌ Ошибка: {exc}")


async def main() -> None:
    await bot.set_my_commands([
        BotCommand(command="start", description="Начало работы"),
    ])
    logger.info("Bot started. Model: %s", settings.openrouter_model)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
