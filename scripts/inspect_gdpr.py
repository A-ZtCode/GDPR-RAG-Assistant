"""Inspect the structure of the downloaded GDPR JSON.

Prints the top-level shape and drills into the first article
so we can plan parsing.
"""

import json
from pathlib import Path


INPUT_PATH = Path("data/raw/gdpr.json")


def main() -> None:
    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))

    print(f"Top-level type: {type(data).__name__}")

    if isinstance(data, dict):
        print(f"Top-level keys: {list(data.keys())}")
    elif isinstance(data, list):
        print(f"Top-level list length: {len(data)}")
        if data:
            print(f"First item type: {type(data[0]).__name__}")
            if isinstance(data[0], dict):
                print(f"First item keys: {list(data[0].keys())}")
                print("First item (truncated):")
                print(json.dumps(data[0], indent=2)[:1500])


if __name__ == "__main__":
    main()