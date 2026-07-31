"""Data models for the El País scraper.

Provides structured representations for scraped article data,
keeping the test layer clean and self-documenting.
"""

from dataclasses import dataclass, field


@dataclass
class Article:
    """Represents a single opinion article from El País.

    Attributes:
        title: Original article title in Spanish.
        content: Full article body text in Spanish.
        image_url: URL of the cover image, or None if unavailable.
        translated_title: English translation of the title (populated after translation step).
    """

    title: str
    content: str
    image_url: str | None = None
    translated_title: str | None = None

    def __str__(self) -> str:
        """Human-readable representation for demo output."""
        return (
            f"Article: {self.title}\n"
            f"  Content: {self.content[:120]}{'...' if len(self.content) > 120 else ''}\n"
            f"  Image: {'Yes' if self.image_url else 'No'}\n"
            f"  Translated: {self.translated_title or 'Pending'}"
        )
