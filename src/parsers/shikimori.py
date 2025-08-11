import requests

BASE_URL = "https://shikimori.one/api"
HEADERS = {"User-Agent": "Mozilla/5.0"}
VALID_TYPES = {"TV", "OVA", "ONA", "MOVIE"}

def get_ongoing_anime(limit=10):
    print("[LOG] Запрос к Shikimori...")
    try:
        resp = requests.get(
            f"{BASE_URL}/animes",
            params={"status": "ongoing", "limit": limit, "order": "ranked"},
            headers=HEADERS
        )
        resp.raise_for_status()
        data = resp.json()
        print(f"[LOG] Ответ Shikimori: {len(data)} записей")
        return [
            {
                "id": a["id"],
                "title": a.get("russian") or a.get("name"),
                "url": f"https://shikimori.one{a['url']}"
            }
            for a in data
        ]
    except Exception as e:
        print(f"[ERROR] Ошибка запроса к Shikimori: {e}")
        return []
