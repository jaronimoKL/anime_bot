# handlers/anime_list.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import logging

# Подключаем парсеры — укажи путь согласно структуре проекта
from parsers import shikimori, mal  # либо from src.parsers import shikimori, mal

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("list"))
async def cmd_list(message: Message):
    logger.info("User %s called /list", message.from_user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Shikimori", callback_data="src_shikimori")],
        [InlineKeyboardButton(text="🌏 MyAnimeList", callback_data="src_mal")]
    ])
    await message.answer("Выберите источник аниме:", reply_markup=keyboard)

@router.callback_query(F.data.in_(["src_shikimori", "src_mal"]))
async def anime_source_callback(callback: CallbackQuery):
    logger.info("User %s chose %s", callback.from_user.id, callback.data)
    await callback.answer()  # чтобы убрать вращалку у пользователя asap

    if callback.data == "src_shikimori":
        animes = shikimori.get_ongoing_anime(limit=10)
    else:
        animes = mal.get_ongoing_anime(limit=10)

    logger.info("Got %d anime items from source %s", len(animes), callback.data)

    if not animes:
        await callback.message.answer("❌ Не удалось получить список аниме")
        return

    buttons = [
        [InlineKeyboardButton(text=a["title"], url=a["url"])]
        for a in animes
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("Список онгоингов:", reply_markup=kb)
