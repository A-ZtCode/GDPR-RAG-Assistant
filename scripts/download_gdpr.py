"""Download GDPR text from the GDPRtEXT academic dataset.

Source: Pandit et al. (2018), GDPRtEXT - GDPR as a Linked Data Resource.
GitHub: coolharsh55/GDPRtEXT, licensed CC-BY 4.0.
"""

from pathlib import Path

import requests


GDPR_URL = (
    "https://raw.githubusercontent.com/coolharsh55/GDPRtEXT/"
    "master/gdpr.json"
)
OUTPUT_PATH = Path("data/raw/gdpr.json")


def main() -> None:
    print(f"Downloading GDPR JSON from {GDPR_URL}")
    response = requests.get(GDPR_URL, timeout=30)
    response.raise_for_status()

    if len(response.text) < 10_000:
        raise RuntimeError(
            f"Response suspiciously small ({len(response.text)} chars). "
            "Expected roughly 500 KB of JSON."
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(response.text, encoding="utf-8")

    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"Saved {size_kb:.1f} KB to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()