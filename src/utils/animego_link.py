import logging
import urllib.parse
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

async def get_anime_link_from_title(title: str) -> str:
    """
    Получает ссылку на аниме на AnimeGO по названию.
    Возвращает URL или None, если не найдено.
    """
    if not title:
        return None

    # Формируем URL для поиска
    search_query = urllib.parse.quote(title)
    search_url = f"https://animego.me/search/anime?q={search_query}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    links = soup.find_all('a', href=lambda x: x and x.startswith('/anime/'))

                    for link in links:
                        # Проверяем текст ссылки или атрибуты title
                        link_text = link.get_text(strip=True).lower()
                        title_lower = title.lower()
                        if title_lower in link_text:
                            # Нашли подходящую ссылку
                            full_url = f"https://animego.me{link['href']}"
                            logger.info(f"Найдена ссылка для '{title}': {full_url}")
                            return full_url

                    # Если не нашли по точному совпадению текста, можно вернуть первую ссылку
                    # Это менее точно, но лучше, чем ничего, если структура сложная
                    # for link in links:
                    #     full_url = f"https://animego.me{link['href']}"
                    #     logger.info(f"Найдена первая ссылка для '{title}': {full_url}")
                    #     return full_url

                    logger.warning(f"Ссылка для аниме '{title}' не найдена на AnimeGO.")
                    return None
                else:
                    logger.error(f"Ошибка при поиске '{title}' на AnimeGO: статус {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Исключение при поиске '{title}' на AnimeGO: {e}")
        return None

# Пример использования (для тестирования)
# async def main():
#     link = await get_anime_link_from_title("Cowboy Bebop")
#     print(link)
#
# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())