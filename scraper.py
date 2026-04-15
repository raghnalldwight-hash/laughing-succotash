"""Fetch Harry Potter Wiki category members via the MediaWiki API.
 
Usage:
    python scraper.py                  # fetches all categories, saves words.json
    python scraper.py --output my.json # custom output path
    python scraper.py --merge          # add to existing words.json instead of replacing
 
Output format (words.json):
    {
        "characters": ["Harry Potter", "Severus Snape", ...],
        "spells":     ["Expelliarmus", "water-making spell", ...],
        "potions":    [...],
        "plants":     [...],
        "creatures":  [...]
    }
"""
 
import argparse
import json
import time
from typing import Optional
 
import requests
 
 
API_URL = "https://harrypotter.fandom.com/api.php"
 
# Map label -> MediaWiki category title.
CATEGORIES: dict[str, str] = {
    "characters": "Category:Characters",
    "spells": "Category:Spells",
    "potions": "Category:Potions",
    "plants": "Category:Plants",
    "creatures": "Category:Magical_creatures",
}
 
HEADERS = {
    # A real browser UA avoids generic bot blocks on the API endpoint too.
    "User-Agent": (
        "Mozilla/5.0 (compatible; HP-Anagram-Solver/1.0; "
        "+https://github.com/raghnalldwight-hash/laughing-succotash)"
    ),
    "Accept": "application/json",
}
 
REQUEST_DELAY = 0.5  # seconds between paginated API calls
 
def fetch_category(category_title: str, label: str) -> list[str]:
    """Return all page titles in *category_title* via the MediaWiki API.
 
 
    The API returns up to 500 results per call; we follow `cmcontinue`
    tokens until all pages have been retrieved.
    """
    titles: list[str] = []
    params: dict = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category_title,
        "cmtype": "page",       # articles only — no subcategories or files
        "cmlimit": "500",       # maximum allowed without bot rights
        "format": "json",
        "formatversion": "2",
    }
    page_num = 1
 
    while True:
        print(f"  [{label}] page {page_num} …")
        try:
            response = requests.get(
                API_URL, params=params, headers=HEADERS, timeout=15
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            print(f"  [{label}] request failed: {exc}")
            break
        except json.JSONDecodeError as exc:
            print(f"  [{label}] bad JSON: {exc}")
            break
        for member in data.get("query", {}).get("categorymembers", []):
            titles.append(member["title"])
 
        # The API signals more pages via a top-level "continue" block.
        if "continue" not in data:
            break
 
        params["cmcontinue"] = data["continue"]["cmcontinue"]
        page_num += 1
        time.sleep(REQUEST_DELAY)
 
    return titles
 
 
def fetch_all(categories: dict[str, str] = CATEGORIES) -> dict[str, list[str]]:
    """Fetch every category and return a {label: [title, ...]} mapping."""
    result: dict[str, list[str]] = {}
    for label, category_title in categories.items():
        print(f"\nFetching category: {label} ({category_title})")
        titles = fetch_category(category_title, label)
        result[label] = titles
        print(f"  → {len(titles)} entries collected.")
        time.sleep(REQUEST_DELAY)
    return result
 
 
def merge_with_existing(
    fetched: dict[str, list[str]],
    existing_file: str,
) -> dict[str, list[str]]:
    """Merge fetched titles with an existing words.json, deduplicating per category."""
    try:
        with open(existing_file, "r", encoding="utf-8") as fh:
            existing: dict[str, list[str]] = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return fetched
    
    merged: dict[str, list[str]] = {}
    all_keys = set(existing) | set(fetched)
    for key in all_keys:
        seen: set[str] = set()
        combined: list[str] = []
        for title in existing.get(key, []) + fetched.get(key, []):
            if title not in seen:
                seen.add(title)
                combined.append(title)
        merged[key] = combined
    return merged
 
 
def save(data: dict[str, list[str]], output_file: str) -> None:
    with open(output_file, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    total = sum(len(v) for v in data.values())
    print(f"\nSaved {total} entries to {output_file}")
 
 
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Harry Potter Wiki categories via the MediaWiki API."
    )
    parser.add_argument(
        "--output",
        default="words.json",
        help="Output JSON file (default: words.json)",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge with an existing words.json instead of overwriting it.",
    )
    args = parser.parse_args()
 
    fetched = fetch_all()
 
    data = merge_with_existing(fetched, args.output) if args.merge else fetched
 
    save(data, args.output)
 
 
if __name__ == "__main__":
    main()
