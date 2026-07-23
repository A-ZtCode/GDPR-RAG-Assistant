"""Inspect a middle chapter to check for section nesting."""

import json
from pathlib import Path


INPUT_PATH = Path("data/raw/gdpr.json")


def main() -> None:
    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    chapters = data["chapters"]

    for chapter in chapters:
        print(f"Chapter {chapter['number']}: {chapter['title']}")
        contents = chapter.get("contents", [])
        types_seen = [item.get("type") for item in contents]
        print(f"  Number of top-level items: {len(contents)}")
        print(f"  Types of those items: {set(types_seen)}")

        # For any section, count what's inside it
        for item in contents:
            if item.get("type") == "section":
                inner = item.get("contents", [])
                inner_types = [x.get("type") for x in inner]
                print(f"  Section {item.get('number', '?')}: "
                      f"{item.get('title', '?')} "
                      f"(contains {len(inner)} items, types: {set(inner_types)})")
        print()


if __name__ == "__main__":
    main()