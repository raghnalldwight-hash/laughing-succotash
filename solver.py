"""Harry Potter anagram solver.
 
Normalization rule: lowercase, strip spaces and hyphens, sort letters.
This means "versuSe aSpen" matches "Severus Snape" and
"gnik-amratew lespl" matches "water-making spell".
"""
 
import json
import os
from typing import Optional
 
 
WORDS_FILE = os.path.join(os.path.dirname(__file__), "words.json")
 
 
def normalize(text: str) -> str:
    """Return the canonical anagram key for a string.
 
    Steps:
      1. Lowercase
      2. Remove spaces and hyphens (so multi-word phrases and hyphenated
         names are treated as a single letter bag)
      3. Sort the remaining characters
    """
    cleaned = text.lower().replace(" ", "").replace("-", "")
    return "".join(sorted(cleaned))
 
 
def build_index(words_file: str = WORDS_FILE) -> dict[str, list[tuple[str, str]]]:
    """Load words.json and return an index of sorted_letters -> [(word, category), ...].
 
    Each entry maps a normalized key to all original phrases that share
    the same letter bag, together with their category label.
    """
    with open(words_file, "r", encoding="utf-8") as fh:
        words_by_category: dict[str, list[str]] = json.load(fh)
 
    index: dict[str, list[tuple[str, str]]] = {}
    for category, words in words_by_category.items():
        for word in words:
            key = normalize(word)
            index.setdefault(key, []).append((word, category))
 
    return index
 
 
def solve(
    anagram: str,
    index: dict[str, list[tuple[str, str]]],
) -> list[tuple[str, str]]:
    """Return all (word, category) pairs that are anagrams of *anagram*.
 
    Matching ignores case, spaces, and hyphens, so every combination of
    those characters in the input maps to the same set of candidates.
    """
    key = normalize(anagram)
    return index.get(key, [])
