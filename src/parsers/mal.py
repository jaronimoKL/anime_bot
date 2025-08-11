import requests

BASE_URL = "https://api.jikan.moe/v4"

def get_ongoing_anime(limit=10):
    print("[LOG] Запрос к MyAnimeList...")
    try:
        resp = requests.get(f"{BASE_URL}/seasons/now")
        resp.raise_for_status()
        data = resp.json().get("data", [])
        print(f"[LOG] Ответ MAL: {len(data)} записей")
        return [
            {
                "id": a["mal_id"],
                "title": a.get("title"),
                "url": a.get("url")
            }
            for a in data[:limit]
        ]
    except Exception as e:
        print(f"[ERROR] Ошибка запроса к MAL: {e}")
        return []
