import aiohttp
from datetime import datetime

BASE_URL = "https://shikimori.one/api"
HEADERS = {"User-Agent": "MyAnimeBot/1.0"}
VALID_TYPES = {"TV", "OVA", "ONA", "MOVIE", "SPECIAL"}
DEFAULT_LIMIT = 50

def parse_date(date_str):
    """Парсинг даты из строки в формате YYYY-MM-DD в объект datetime или возвращает None"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

async def get_ongoing_anime_async(limit=DEFAULT_LIMIT, page=1):
    """Асинхронное получение онгоингов с Shikimori с полной информацией"""
    print(f"[LOG] Асинхронный запрос к Shikimori... Страница: {page}, Лимит: {limit}")
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(
                f"{BASE_URL}/animes",
                params={
                    "status": "ongoing",
                    "limit": limit,
                    "order": "ranked",
                    "page": page
                }
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                print(f"[LOG] Ответ Shikimori: {len(data)} записей")
                result = []
                for anime in data:
                    # Фильтр по типам аниме
                    kind = anime.get("kind", "").upper()
                    if kind not in VALID_TYPES:
                        continue

                    # Парсим даты
                    aired_on = parse_date(anime.get("aired_on"))
                    released_on = parse_date(anime.get("released_on"))

                    # Формируем URL
                    url_path = anime.get("url", "")
                    full_url = f"https://shikimori.one{url_path}" if url_path else None

                    # Извлекаем жанры и синонимы
                    genres = ", ".join([g.get("russian", g.get("name")) for g in anime.get("genres", [])])
                    synonyms = ", ".join(anime.get("synonyms", []))

                    result.append({
                        "id": anime["id"],
                        "title": anime.get("russian") or anime.get("name"),
                        "english_title": anime.get("name"),
                        "japanese_title": anime.get("japanese"),
                        "synonyms": synonyms,
                        "source": "shikimori",
                        "source_id": str(anime["id"]),
                        "url": full_url,
                        "type": kind,
                        "status": anime.get("status"),
                        "episodes": anime.get("episodes"),
                        "episodes_aired": anime.get("episodes_aired"),
                        "score": anime.get("score"),
                        "aired_on": aired_on,
                        "released_on": released_on,
                        "image_url": anime.get("image", {}).get("original"),
                        "genres": genres,
                        "duration": anime.get("duration"),
                        "description": anime.get("description"),
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    })
                return result
    except Exception as e:
        print(f"[ERROR] Ошибка асинхронного запроса к Shikimori: {e}")
        import traceback
        traceback.print_exc()
        return []

async def get_ongoing_anime_count_async():
    """Асинхронное получение приблизительного количества онгоингов"""
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(
                f"{BASE_URL}/animes",
                params={
                    "status": "ongoing",
                    "limit": 1, # Запрашиваем только 1, чтобы получить X-Total-Count
                    "order": "ranked"
                }
            ) as resp:
                resp.raise_for_status()
                total_count = int(resp.headers.get('X-Total-Count', 0))
                print(f"[LOG] Общее количество онгоингов на Shikimori: {total_count}")
                return total_count
    except Exception as e:
        print(f"[ERROR] Ошибка получения количества онгоингов с Shikimori: {e}")
        return 100