"""Scrape the Harry Potter Wiki (harrypotter.fandom.com) to build a word list.
 
Usage:
    python scraper.py                  # scrapes all categories, saves words.json
    python scraper.py --output my.json # custom output path
 
The script follows pagination inside each category so it collects *all*
article titles, not just the first page.  A short polite delay is inserted
between requests.
 
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
from bs4 import BeautifulSoup
 
 
BASE_URL = "https://harrypotter.fandom.com"
 
# Category paths to scrape.  Keys become category labels in words.json.
CATEGORIES: dict[str, str] = {
    "characters": "/wiki/Category:Characters",
    "spells": "/wiki/Category:Spells",
    "potions": "/wiki/Category:Potions",
    "plants": "/wiki/Category:Plants",
    "creatures": "/wiki/Category:Magical_creatures",
}
 
HEADERS = {
    "User-Agent": (
        "HP-Anagram-Solver/1.0 "
        "(https://github.com/raghnalldwight-hash/laughing-succotash)"
    )
}
 
REQUEST_DELAY = 0.75  # seconds between page requests
 
 
def get_page(url: str, retries: int = 3) -> Optional[BeautifulSoup]:
    """Fetch *url* and return a parsed BeautifulSoup, or None on failure."""
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except requests.RequestException as exc:
            print(f"  [attempt {attempt}/{retries}] Error fetching {url}: {exc}")
            if attempt < retries:
                time.sleep(2 ** attempt)
    return None
 
 
def _next_page_url(soup: BeautifulSoup) -> Optional[str]:
    """Return the absolute URL of the next category page, or None."""
    # Fandom uses both a link element and a plain <a> with class
    # 'category-page__pagination-next'.
    link = soup.select_one("a.category-page__pagination-next")
    if link and link.get("href"):
        href = link["href"]
        return href if href.startswith("http") else BASE_URL + href
    return None
 
 
def scrape_category(category_path: str, label: str) -> list[str]:
    """Collect all article titles from one wiki category, following pages."""
    titles: list[str] = []
    url: Optional[str] = BASE_URL + category_path
    page_num = 1
 
    while url:
        print(f"  [{label}] page {page_num}: {url}")
        soup = get_page(url)
        if soup is None:
            print(f"  [{label}] failed to load page, stopping.")
            break
 
        # Article titles are in <a class="category-page__member-link">
        for link in soup.select("a.category-page__member-link"):
            title = link.get_text(strip=True)
            # Skip sub-category entries (they start with "Category:")
            if title and not title.startswith("Category:"):
                titles.append(title)
 
        url = _next_page_url(soup)
        page_num += 1
        if url:
            time.sleep(REQUEST_DELAY)
 
    return titles
 
 
def scrape_all(categories: dict[str, str] = CATEGORIES) -> dict[str, list[str]]:
    """Scrape every category and return a {label: [title, ...]} mapping."""
    result: dict[str, list[str]] = {}
    for label, path in categories.items():
        print(f"\nScraping category: {label}")
        titles = scrape_category(path, label)
        result[label] = titles
        print(f"  → {len(titles)} entries collected.")
        time.sleep(REQUEST_DELAY)
    return result
 
 
def merge_with_existing(
    scraped: dict[str, list[str]],
    existing_file: str,
) -> dict[str, list[str]]:
    """Merge scraped titles with an existing words.json, deduplicating per category."""
    try:
        with open(existing_file, "r", encoding="utf-8") as fh:
            existing: dict[str, list[str]] = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return scraped
 
    merged: dict[str, list[str]] = {}
    all_keys = set(existing) | set(scraped)
    for key in all_keys:
        seen: set[str] = set()
        combined: list[str] = []
        for title in existing.get(key, []) + scraped.get(key, []):
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
    parser = argparse.ArgumentParser(description="Scrape the Harry Potter Wiki.")
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
 
    scraped = scrape_all()
 
    if args.merge:
        data = merge_with_existing(scraped, args.output)
    else:
        data = scraped
 
    save(data, args.output)
 
 
if __name__ == "__main__":
    main()
