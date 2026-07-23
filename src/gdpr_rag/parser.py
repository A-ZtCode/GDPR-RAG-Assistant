"""Parse GDPR JSON into article-level chunks with metadata.

Input: the GDPRtEXT JSON dataset (Pandit et al. 2018).
Output: a list of Article objects, each carrying full text and
chapter/article metadata for downstream indexing and citation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


SOURCE_ATTRIBUTION = "GDPRtEXT (Pandit et al. 2018), CC-BY 4.0"


@dataclass(frozen=True)
class Article:
    """One GDPR article with its text and full context metadata."""

    chapter_number: str
    chapter_title: str
    article_number: str
    article_title: str
    text: str
    source: str = SOURCE_ATTRIBUTION

    def metadata(self) -> dict[str, str]:
        """Return metadata dict for vector-store indexing."""
        return {
            "chapter_number": self.chapter_number,
            "chapter_title": self.chapter_title,
            "article_number": self.article_number,
            "article_title": self.article_title,
            "source": self.source,
        }

    def citation(self) -> str:
        """Return a short human-readable citation, e.g. 'Article 5'."""
        return f"Article {self.article_number}"


def _render_article_text(article: dict) -> str:
    """Turn an article's structured content into flat text for embedding.

    Preserves point numbers so the LLM can cite specific paragraphs.
    Includes subpoint labels (a, b, c...) inline.
    """
    lines: list[str] = []
    lines.append(f"Article {article['number']}: {article['title']}")
    lines.append("")

    for point in article.get("contents", []):
        point_num = point.get("number", "")
        point_text = point.get("text", "").strip()

        if point_text:
            lines.append(f"{point_num}. {point_text}")

        for subpoint in point.get("subpoints", []) or []:
            sub_num = subpoint.get("number", "")
            sub_text = subpoint.get("text", "").strip()
            if sub_text:
                lines.append(f"    ({sub_num}) {sub_text}")

    return "\n".join(lines)


def _make_article(
    chapter_number: str,
    chapter_title: str,
    article_dict: dict,
) -> Article:
    """Build an Article from a raw article dict plus chapter context."""
    return Article(
        chapter_number=chapter_number,
        chapter_title=chapter_title,
        article_number=article_dict.get("number", ""),
        article_title=article_dict.get("title", ""),
        text=_render_article_text(article_dict),
    )


def parse_gdpr(json_path: Path) -> list[Article]:
    """Parse the GDPRtEXT JSON file into a list of Article objects.

    GDPR chapters may hold articles either directly, or nested inside
    sections. Both shapes are handled. Any other type of container is
    ignored defensively so the parser survives schema surprises.
    """
    data = json.loads(json_path.read_text(encoding="utf-8"))
    articles: list[Article] = []

    for chapter in data.get("chapters", []):
        if chapter.get("type") != "chapter":
            continue

        chapter_number = chapter.get("number", "")
        chapter_title = chapter.get("title", "")

        for item in chapter.get("contents", []):
            item_type = item.get("type")

            if item_type == "article":
                articles.append(
                    _make_article(chapter_number, chapter_title, item)
                )
            elif item_type == "section":
                for inner in item.get("contents", []):
                    if inner.get("type") == "article":
                        articles.append(
                            _make_article(
                                chapter_number, chapter_title, inner,
                            )
                        )

    return articles