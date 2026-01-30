# backend/app/internet/google_search.py
import os
import re
import requests

from dotenv import load_dotenv
load_dotenv()

NOISE_KEYWORDS = [
    "stackoverflow", "reddit",
]

def _is_noisy(snippet: str) -> bool:
    """Filter out low-quality results"""
    s = snippet.lower()
    for k in NOISE_KEYWORDS:
        if k in s:
            return True
    if len(re.findall(r"\b(int|float|String|var|val|def|func)\b", s)) >= 2:
        return True
    return False


def _add_spacing_to_snippet(text: str) -> str:
    """
    Fix Google's concatenated text by adding spaces between words
    (Like Claude's search result formatting)
    
    Example:
    "TheofficialhomeofthePythonProgrammingLanguage" 
    → "The official home of the Python Programming Language"
    """
    # Add space before capital letters (except at start)
    spaced = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)
    
    # Add space between lowercase and digits
    spaced = re.sub(r'(?<=[a-z])(?=\d)', ' ', spaced)
    
    # Add space between digits and letters
    spaced = re.sub(r'(?<=\d)(?=[A-Za-z])', ' ', spaced)
    
    # Collapse multiple spaces
    spaced = re.sub(r'\s+', ' ', spaced)
    
    return spaced.strip()


def google_search(query: str, max_results: int = 5):
    """
    Google Custom Search API - returns structured results
    Like Claude's web search tool
    """
    API_KEY = os.getenv("GOOGLE_API_KEY")
    CX = os.getenv("GOOGLE_CX")

    print(f"[GOOGLE_SEARCH] Query: '{query}'")
    print(f"[GOOGLE_API_KEY] exists: {bool(API_KEY)}")
    print(f"[GOOGLE_CX] exists: {bool(CX)}")

    if not API_KEY or not CX:
        print("[GOOGLE_SEARCH] ERROR: Missing API credentials")
        return []

    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": API_KEY, "cx": CX, "q": query, "num": max_results}

    try:
        print(f"[GOOGLE_SEARCH] Making request to Google API...")
        r = requests.get(url, params=params, timeout=10)
        print(f"[GOOGLE_SEARCH] Response status: {r.status_code}")
        
        if r.status_code != 200:
            print(f"[GOOGLE_SEARCH] ERROR: {r.text}")
            return []
        
        data = r.json()
        clean_results = []

        if "items" in data:
            print(f"[GOOGLE_SEARCH] Found {len(data['items'])} items")
            for item in data["items"][:max_results]:
                snippet = item.get("snippet", "").strip()
                title = item.get("title", "").strip()
                link = item.get("link", "")

                if not snippet:
                    continue

                # Clean the snippet
                cleaned = re.sub(r"http\S+", "", snippet)
                cleaned = re.sub(r"[{}$$      $$]", "", cleaned)
                cleaned = re.sub(r"\s{2,}", " ", cleaned)
                
                # ✅ Fix concatenated words (like Claude does)
                cleaned = _add_spacing_to_snippet(cleaned)

                if _is_noisy(cleaned):
                    print(f"[GOOGLE_SEARCH] Skipping noisy result: {title}")
                    continue

                # Return structured dict (like Claude's search results)
                result_dict = {
                    "title": title,
                    "link": link,
                    "snippet": cleaned
                }
                clean_results.append(result_dict)
                print(f"[GOOGLE_SEARCH] Added: {title[:50]}...")

        print(f"[GOOGLE_SEARCH] Returning {len(clean_results)} clean results")
        return clean_results

    except Exception as e:
        print(f"[GOOGLE_SEARCH] Exception: {e}")
        return []