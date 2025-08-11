# handlers/start.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def cmd_start(message: Message):
    logger.info("User %s used /start", message.from_user.id)
    text = (
        "👋 Привет!\n\n"
        "Доступные команды:\n"
        "/start - показать это сообщение\n"
        "/list - показать список онгоингов (выбор источника)\n"
    )
    await message.answer(text)
