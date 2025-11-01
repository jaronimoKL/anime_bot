from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    welcome_text = (
        "Привет! 👋\n\n"
        "Я бот для отслеживания онгоингов аниме.\n\n"
        "Доступные команды:\n"
        "/list - Показать список онгоингов\n"
        "/update - Обновить базу данных аниме\n"
        "/subscriptions - Показать ваши подписки\n"
        "/help - Показать это сообщение"
    )
    await message.answer(welcome_text)

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "Помощь по боту:\n\n"
        "/list - Просмотр аниме с Shikimori или MAL\n"
        "/update - Ручное обновление базы аниме\n"
        "/subscriptions - Просмотр ваших подписок\n"
        "Чтобы подписаться на аниме, нажмите на него в списке и используйте кнопку '🔔 Подписаться'."
    )
    await message.answer(help_text)
