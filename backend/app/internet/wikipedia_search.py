# backend/app/internet/wikipedia_search.py
import requests

HEADERS = {
    "User-Agent": "NEXORA/1.1 (teamfav19@gmail.com)"
}

def wiki_search(query: str, max_chunks=3):
    try:
        # 1️⃣ SEARCH API
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json"
        }

        search_resp = requests.get(search_url, params=search_params, headers=HEADERS, timeout=5)

        if search_resp.status_code != 200:
            print(f"[WIKI] Search HTTP {search_resp.status_code}")
            return []

        search_data = search_resp.json()
        results = search_data.get("query", {}).get("search", [])

        if not results:
            print("[WIKI] No search results")
            return []

        # 2️⃣ TAKE FIRST RESULT TITLE
        title = results[0]["title"]

        # 3️⃣ FETCH SUMMARY
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '%20')}"
        summary_resp = requests.get(summary_url, headers=HEADERS, timeout=5)

        if summary_resp.status_code != 200:
            print(f"[WIKI] Summary HTTP {summary_resp.status_code}")
            return []

        text = summary_resp.json().get("extract")

        if not text:
            print("[WIKI] No extract found")
            return []

        chunks = [text[i:i+600] for i in range(0, len(text), 600)]
        print(f"[WIKI] Returning {len(chunks[:max_chunks])} chunks")
        return chunks[:max_chunks]

    except Exception as e:
        print(f"[WIKI] Exception: {e}")
        return []
