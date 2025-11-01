import aiohttp
import asyncio

BASE_URL = "https://api.jikan.moe/v4"
MAX_LIMIT = 25  # Максимальный лимит для seasons/now


async def get_ongoing_anime_async(limit=10, page=1):
    """Асинхронное получение онгоингов с MyAnimeList"""
    print(f"[LOG] Асинхронный запрос к MyAnimeList... Страница: {page}")
    try:
        # Ограничиваем limit максимальным значением API
        safe_limit = min(limit, MAX_LIMIT)

        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"{BASE_URL}/seasons/now",
                    params={
                        "limit": safe_limit,
                        "page": page
                    }
            ) as resp:
                resp.raise_for_status()
                json_data = await resp.json()
                data = json_data.get("data", [])
                pagination = json_data.get("pagination", {})
                last_visible_page = pagination.get("last_visible_page", 1)
                items_per_page = pagination.get("items", {}).get("per_page", safe_limit)
                total_items = pagination.get("items", {}).get("total", len(data))

                print(f"[LOG] Ответ MAL: {len(data)} записей")
                result = []
                for anime in data:
                    url = anime.get("url")
                    # Проверяем, что URL существует и корректен
                    if url and isinstance(url, str) and (url.startswith("http://") or url.startswith("https://")):
                        result.append({
                            "id": anime["mal_id"],
                            "title": anime.get("title"),
                            "url": url
                        })
                    else:
                        print(f"[WARNING] Пропущено аниме без корректного URL: {anime.get('title', 'Unknown')}")
                        # Можно попробовать сформировать URL вручную
                        mal_id = anime.get("mal_id")
                        if mal_id:
                            fallback_url = f"https://myanimelist.net/anime/{mal_id}"
                            result.append({
                                "id": mal_id,
                                "title": anime.get("title"),
                                "url": fallback_url
                            })

                return result, last_visible_page, total_items
    except Exception as e:
        print(f"[ERROR] Ошибка асинхронного запроса к MAL: {e}")
        import traceback
        traceback.print_exc()
        return [], 1, 0


async def fetch_all_ongoing_anime_mal():
    """Асинхронная загрузка всех онгоингов с MAL"""
    try:
        # Сначала получаем первую страницу чтобы узнать общее количество
        first_page_data, last_visible_page, total_items = await get_ongoing_anime_async(limit=25, page=1)

        if not first_page_data:
            return [], 0, 0

        # Создаем задачи для всех остальных страниц
        tasks = []
        for page in range(2, last_visible_page + 1):
            tasks.append(get_ongoing_anime_async(limit=25, page=page))

        # Выполняем все запросы параллельно
        all_other_pages = await asyncio.gather(*tasks)

        # Объединяем все данные
        all_anime = first_page_data.copy()
        for page_data, _, _ in all_other_pages:
            all_anime.extend(page_data)

        return all_anime, last_visible_page, total_items
    except Exception as e:
        print(f"[ERROR] Ошибка при загрузке всех онгоингов с MAL: {e}")
        return [], 1, 0