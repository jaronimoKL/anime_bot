import urllib.parse
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import json
from sqlalchemy import select, and_, func

# Подключаем парсеры
from ..parsers import shikimori, mal
# Подключаем сервисы
from ..services.anime_service import anime_service
from ..services.subscription_service import SubscriptionsService
# Подключаем утилиты
from ..utils.animego_link import get_anime_link_from_title

router = Router()
logger = logging.getLogger(__name__)

ITEMS_PER_PAGE = 10


@router.message(Command("list"))
async def cmd_list(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Shikimori", callback_data="src_shikimori_1")],
        [InlineKeyboardButton(text="🌏 MyAnimeList", callback_data="src_mal_1")]
    ])
    await message.answer("Выберите источник аниме:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("src_shikimori_"))
async def anime_source_callback_shikimori(callback: CallbackQuery):
    await handle_anime_list_callback(callback, "shikimori")


@router.callback_query(F.data.startswith("src_mal_"))
async def anime_source_callback_mal(callback: CallbackQuery):
    await handle_anime_list_callback(callback, "mal")


async def handle_anime_list_callback(callback: CallbackQuery, source: str):
    """Общий обработчик для обоих источников с пагинацией"""
    logger.info("User %s chose %s", callback.from_user.id, callback.data)
    await callback.answer()

    # Извлекаем номер страницы из callback_data
    try:
        page = int(callback.data.split("_")[-1])
        if page < 1:
            page = 1
    except (ValueError, IndexError):
        page = 1

    # Проверяем, есть ли данные в базе
    db_count = await anime_service.get_ongoing_count_from_database(source)

    animes = []
    total_pages = 1

    if db_count == 0:
        # База пуста - делаем полное обновление
        logger.info(f"База пуста для {source}, начинаем полное обновление...")
        await callback.message.answer(f"🔄 Загружаем все онгоинги из {source}... Это может занять некоторое время.")

        added_count = await anime_service.update_all_ongoing_from_source(source)
        await callback.message.answer(f"✅ Загружено {added_count} аниме из {source}")

        # Обновляем количество
        db_count = await anime_service.get_ongoing_count_from_database(source)

    # Получаем данные из базы
    offset = (page - 1) * ITEMS_PER_PAGE
    db_animes = await anime_service.get_ongoing_from_database(source, ITEMS_PER_PAGE, offset)
    total_pages = max(1, (db_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    logger.info("Got %d anime items from database %s (page %d/%d)", len(db_animes), source, page, total_pages)

    # Проверка на пустой список аниме
    if not db_animes:
        await callback.message.answer("❌ Не удалось получить список аниме")
        return

    # Создаем кнопки для аниме
    buttons = []

    for anime in db_animes:
        title = anime.title or "Без названия"
        anime_id = anime.source_id or anime.id
        source_prefix = anime.source or source

        # Создаем callback_data для просмотра деталей
        callback_data = f"details_{source_prefix}_{anime_id}"
        # Ограничиваем длину если нужно
        if len(callback_data) > 64:
            callback_data = f"details_{source_prefix}_{str(anime_id)[:30]}"

        buttons.append([InlineKeyboardButton(text=title, callback_data=callback_data)])

    # Создаем кнопки навигации
    nav_buttons = []
    callback_prefix = f"src_{source}"

    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{callback_prefix}_{page - 1}"))

    # Информационная кнопка с номером страницы
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="page_info"))

    # Ограничиваем навигацию разумными пределами
    max_pages = 50  # Увеличиваем лимит

    if page < total_pages and page < max_pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"{callback_prefix}_{page + 1}"))

    # Добавляем кнопки навигации, если они есть
    if nav_buttons:
        buttons.append(nav_buttons)

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    source_name = "Shikimori" if source == "shikimori" else "MyAnimeList"

    try:
        await callback.message.edit_text(f"Список онгоингов ({source_name}, стр. {page}):", reply_markup=kb)
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        try:
            await callback.message.answer(f"Список онгоингов ({source_name}, стр. {page}):", reply_markup=kb)
        except Exception as e2:
            logger.error(f"Failed to send new message: {e2}")
            await callback.message.answer("❌ Произошла ошибка при отображении списка.")


# Обработчик для просмотра деталей аниме
@router.callback_query(F.data.startswith("details_"))
async def show_anime_details(callback: CallbackQuery):
    """Показать детали аниме с кнопками подписки и ссылками"""
    await callback.answer()

    try:
        # Извлекаем информацию из callback_data
        # Формат: details_source_id
        parts = callback.data.split("_")
        if len(parts) < 3:
            await callback.message.answer("❌ Ошибка: некорректные данные.")
            return

        source = parts[1]  # shikimori или mal
        anime_id = parts[2]  # ID аниме в источнике

        # Получаем аниме из БД
        anime = await anime_service.get_anime_by_source_and_id(source, anime_id)

        if not anime:
            # Если не нашли в БД, попробуем получить из API
            await callback.message.answer("❌ Аниме не найдено в базе данных.")
            return

        # Формируем сообщение с деталями
        info_text = f"🎬 *{anime.title}*\n\n"

        if anime.english_title and anime.english_title != anime.title:
            info_text += f"🇺🇸 _{anime.english_title}_\n"

        if anime.japanese_title:
            info_text += f"🇯🇵 _{anime.japanese_title}_\n\n"

        # Тип и статус
        if anime.type:
            type_names = {
                'tv': '📺 TV Сериал',
                'movie': '🎬 Фильм',
                'ova': '📼 OVA',
                'ona': '🌐 ONA',
                'special': '⭐ Спешл'
            }
            info_text += f"📊 *Тип:* {type_names.get(anime.type.lower(), anime.type)}\n"

        # Эпизоды
        if anime.episodes_aired is not None and anime.episodes is not None:
            info_text += f"📺 *Эпизоды:* {anime.episodes_aired}/{anime.episodes}\n"
        elif anime.episodes is not None:
            info_text += f"📺 *Эпизоды:* {anime.episodes}\n"

        # Статус
        if anime.status:
            status_names = {
                'ongoing': '🔄 Онгоинг',
                'released': '✅ Завершено',
                'announced': '📅 Анонсировано'
            }
            info_text += f"🔄 *Статус:* {status_names.get(anime.status.lower(), anime.status)}\n"

        # Рейтинг
        if anime.score:
            info_text += f"⭐ *Рейтинг:* {anime.score}\n"

        # Жанры
        if anime.genres:
            try:
                genres_list = json.loads(anime.genres)
                if genres_list:
                    info_text += f"🎭 *Жанры:* {', '.join(genres_list[:5])}\n"
            except:
                pass

        # Длительность
        if anime.duration:
            info_text += f"⏱️ *Длительность:* {anime.duration}\n"

        # Даты
        if anime.aired_on:
            info_text += f"📅 *Выход серий:* с {anime.aired_on.strftime('%d.%m.%Y')}\n"

        # Источник
        source_emoji = "🇷🇺" if anime.source == "shikimori" else "🇯🇵"
        source_name = "Shikimori" if anime.source == "shikimori" else "MyAnimeList"
        info_text += f"\n📡 *Источник:* {source_emoji} {source_name}"

        # Создаем клавиатуру с кнопками
        keyboard_buttons = []

        # Первая строка: ссылки на просмотр
        row1 = []

        # Ссылка на источник
        if anime.url:
            source_text = "Shikimori" if anime.source == "shikimori" else "MyAnimeList"
            row1.append(InlineKeyboardButton(text=f"📖 {source_text}", url=anime.url))

        # Ссылка на AnimeGO
        if anime.animego_url:
            row1.append(InlineKeyboardButton(text="👁️ AnimeGO", url=anime.animego_url))
        else:
            # Если нет прямой ссылки, создаем кнопку поиска
            search_query = urllib.parse.quote(anime.title)
            search_url = f"https://animego.me/search/anime?q={search_query}"
            row1.append(InlineKeyboardButton(text="🔍 Найти на AnimeGO", url=search_url))

        if row1:
            keyboard_buttons.append(row1)

        # Вторая строка: подписка
        user_id = callback.from_user.id
        # Проверяем, подписан ли пользователь
        subscription_service = SubscriptionsService(anime_service.db)
        is_subscribed = await subscription_service.is_user_subscribed(user_id, anime.id)

        row2 = []
        if is_subscribed:
            row2.append(InlineKeyboardButton(text="✅ Отписаться", callback_data=f"unsubscribe_{anime.id}"))
        else:
            row2.append(InlineKeyboardButton(text="🔔 Подписаться", callback_data=f"subscribe_{anime.id}"))

        keyboard_buttons.append(row2)

        # Третья строка: назад
        row3 = []
        row3.append(InlineKeyboardButton(text="🔙 Назад", callback_data="src_shikimori_1"))
        keyboard_buttons.append(row3)

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        # Отправляем сообщение
        if anime.image_url and anime.image_url.strip():  # Проверяем, что URL не пустой
            try:
                await callback.message.answer_photo(
                    photo=anime.image_url,
                    caption=info_text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки фото: {e}")
                await callback.message.answer(info_text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await callback.message.answer(info_text, reply_markup=keyboard, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка при отображении деталей аниме: {e}")
        await callback.message.answer("❌ Ошибка при отображении информации об аниме.")


# Обработчик для информационной кнопки страницы
@router.callback_query(F.data == "page_info")
async def page_info_callback(callback: CallbackQuery):
    await callback.answer()


@router.message(Command("update"))
async def update_anime_database(message: Message):
    """Обновление базы данных аниме"""
    user_id = message.from_user.id
    logger.info("User %s requested database update", user_id)

    await message.answer("🔄 Обновляю базу данных аниме...")

    try:
        # Обновляем из обоих источников (добавлен await)
        shikimori_count = await anime_service.update_all_ongoing_from_source("shikimori")
        await message.answer(f"✅ Обновлено из Shikimori: {shikimori_count} аниме")

        mal_count = await anime_service.update_all_ongoing_from_source("mal")
        await message.answer(f"✅ Обновлено из MyAnimeList: {mal_count} аниме")

        # Показываем статистику (добавлены await)
        shikimori_count_db = await anime_service.get_ongoing_count_from_database("shikimori")
        mal_count_db = await anime_service.get_ongoing_count_from_database("mal")
        total_count = shikimori_count_db + mal_count_db

        await message.answer(
            f"📊 Статистика базы данных:\n"
            f"Всего онгоингов: {total_count}"
        )

    except Exception as e:
        logger.error(f"Error updating database: {e}")
        await message.answer("❌ Ошибка при обновлении базы данных.")


# --- Обработчики подписки/отписки ---
# Эти обработчики перемещены из subscriptions.py в этот файл, так как логика тесно связана с деталями аниме

@router.callback_query(F.data.startswith("subscribe_"))
async def subscribe_callback(callback: CallbackQuery):
    """Обработчик подписки на аниме"""
    await callback.answer()

    try:
        anime_id = int(callback.data.split("_")[1])
        user_id = callback.from_user.id

        # Создаем экземпляр сервиса подписок
        subscription_service = SubscriptionsService(anime_service.db)
        success = await subscription_service.subscribe_user_to_anime(user_id, anime_id)

        if success:
            await callback.answer("✅ Вы успешно подписались на уведомления!")
            await callback.message.answer("✅ Вы подписались на уведомления о выходе новых серий!")
        else:
            await callback.answer("❌ Ошибка подписки или вы уже подписаны")

    except Exception as e:
        logger.error(f"Ошибка подписки: {e}")
        await callback.answer("❌ Ошибка подписки")


@router.callback_query(F.data.startswith("unsubscribe_"))
async def unsubscribe_callback(callback: CallbackQuery):
    """Обработчик отписки от аниме"""
    await callback.answer()

    try:
        anime_id = int(callback.data.split("_")[1])
        user_id = callback.from_user.id

        # Создаем экземпляр сервиса подписок
        subscription_service = SubscriptionsService(anime_service.db)
        success = await subscription_service.unsubscribe_user_from_anime(user_id, anime_id)

        if success:
            await callback.answer("✅ Вы успешно отписались от уведомлений!")
            await callback.message.answer("✅ Вы отписались от уведомлений о выходе новых серий!")
        else:
            await callback.answer("❌ Ошибка отписки или вы не были подписаны")

    except Exception as e:
        logger.error(f"Ошибка отписки: {e}")
        await callback.answer("❌ Ошибка отписки")


@router.message(Command("subscriptions"))
async def show_user_subscriptions(message: Message):
    """Показать список подписок пользователя"""
    user_id = message.from_user.id
    logger.info(f"User {user_id} requested subscriptions list")

    try:
        subscription_service = SubscriptionsService(anime_service.db)
        subscriptions = await subscription_service.get_user_subscriptions(user_id)

        if not subscriptions:
            await message.answer("❌ Вы пока не подписаны ни на одно аниме.")
            return

        # Формируем список подписок
        text = "🔔 *Ваши подписки:*\n\n"
        buttons = []

        for anime in subscriptions:
            title = anime.title or "Без названия"
            source_prefix = anime.source or "unknown"
            anime_id = anime.source_id or anime.id

            # Создаем callback_data для просмотра деталей
            callback_data = f"details_{source_prefix}_{anime_id}"
            if len(callback_data) > 64:
                callback_data = f"details_{source_prefix}_{str(anime_id)[:30]}"

            text += f"🎬 {title}\n"
            if anime.episodes_aired is not None and anime.episodes is not None:
                text += f"📺 Эпизоды: {anime.episodes_aired}/{anime.episodes}\n"
            text += "\n"

            buttons.append([InlineKeyboardButton(text=title, callback_data=callback_data)])

        # Добавляем кнопку "Назад"
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="src_shikimori_1")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка при показе подписок пользователя {user_id}: {e}")
        await message.answer("❌ Ошибка при получении списка подписок.")