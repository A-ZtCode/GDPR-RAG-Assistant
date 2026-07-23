"""Smoke test: confirm th Anthropic API can be called."""

import os

from anthropic import Anthropic
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not found. Check your .env file."
        )

    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": "Say hello in exactly one short sentence.",
            }
        ],
    )

    print("Claude replied:")
    print(response.content[0].text)


if __name__ == "__main__":
    main()