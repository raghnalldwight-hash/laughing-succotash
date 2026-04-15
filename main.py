"""Harry Potter Anagram Solver — CLI entry point.
 
Usage:
    python main.py                          # interactive mode
    python main.py "versuSe aSpen"          # solve a single anagram
    python main.py "gnik-amratew lespl"     # hyphens are ignored automatically
    python main.py --words custom.json ...  # use a different word list
 
Matching is case-insensitive and ignores spaces and hyphens, so every
rearrangement of the letters (regardless of spacing and capitalisation)
will find the same answers.
"""
 
import argparse
import os
import sys
 
from solver import WORDS_FILE, build_index, solve
 
 
def print_results(anagram: str, results: list[tuple[str, str]]) -> None:
    if results:
        print(f"Anagram of '{anagram}':")
        for word, category in results:
            print(f"  {word}  [{category}]")
    else:
        print(f"No Harry Potter matches found for '{anagram}'.")
 
 
def interactive(index: dict) -> None:
    print("Harry Potter Anagram Solver")
    print("Enter an anagram (or 'quit' to exit):\n")
    while True:
        try:
            anagram = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not anagram:
            continue
        if anagram.lower() in {"quit", "exit", "q"}:
            break
        print_results(anagram, solve(anagram, index))
        print()
 
 
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Solve Harry Potter anagrams.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python main.py "versuSe aSpen"\n'
            '  python main.py "gnik-amratew lespl"\n'
            "  python main.py          # interactive mode"
        ),
    )
    parser.add_argument(
        "anagram",
        nargs="*",
        help="Anagram string(s) to solve (omit for interactive mode).",
    )
    parser.add_argument(
        "--words",
        default=WORDS_FILE,
        metavar="FILE",
        help="Path to words JSON file (default: words.json).",
    )
    args = parser.parse_args()
 
    if not os.path.exists(args.words):
        print(
            f"Word list not found at '{args.words}'.\n"
            "Run 'python scraper.py' to build it, or use --words to point at "
            "an existing file.",
            file=sys.stderr,
        )
        sys.exit(1)
 
    print("Loading word list...", end=" ", flush=True)
    index = build_index(args.words)
    total = sum(len(v) for v in index.values())
    print(f"{total} entries loaded.\n")
 
    if args.anagram:
        # One or more anagrams supplied as positional arguments
        for anagram in args.anagram:
            print_results(anagram, solve(anagram, index))
            print()
    else:
        interactive(index)
 
 
if __name__ == "__main__":
    main()
