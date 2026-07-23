"""Quick check: parse GDPR and print sanity-check stats."""

from pathlib import Path

from gdpr_rag.parser import parse_gdpr


INPUT_PATH = Path("data/raw/gdpr.json")


def main() -> None:
    articles = parse_gdpr(INPUT_PATH)

    print(f"Total articles parsed: {len(articles)}")
    print(f"Expected: 99 articles in GDPR")
    print()

    print("First 3 articles:")
    for article in articles[:3]:
        print(f"  Article {article.article_number} "
              f"(Chapter {article.chapter_number}): "
              f"{article.article_title}")
    print()

    print("Last 3 articles:")
    for article in articles[-3:]:
        print(f"  Article {article.article_number} "
              f"(Chapter {article.chapter_number}): "
              f"{article.article_title}")
    print()

    print("Example rendered article (Article 5):")
    print("-" * 60)
    for article in articles:
        if article.article_number == "5":
            print(article.text)
            print()
            print("Metadata:", article.metadata())
            break

    print()
    print(f"Longest article by character count:")
    longest = max(articles, key=lambda a: len(a.text))
    print(f"  Article {longest.article_number}: {longest.article_title}")
    print(f"  Length: {len(longest.text)} chars")

    print(f"Shortest article by character count:")
    shortest = min(articles, key=lambda a: len(a.text))
    print(f"  Article {shortest.article_number}: {shortest.article_title}")
    print(f"  Length: {len(shortest.text)} chars")


if __name__ == "__main__":
    main()