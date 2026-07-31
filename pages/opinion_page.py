"""Page object for the El País Opinion section listing page.

Handles navigation to the Opinion section and extraction of
article links, titles, and cover image URLs from the listing grid.

Selectors verified against live DOM (July 2026):
  - Article container: <article> tags
  - Title link: h2.c_t > a
  - Cover image: figure.c_m > img
"""

import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage

logger = logging.getLogger(__name__)

OPINION_URL = "https://elpais.com/opinion/"


class OpinionPage(BasePage):
    """Represents the El País Opinion section landing page.

    Responsibilities:
      - Navigate to the Opinion section
      - Verify the page is in Spanish
      - Extract article metadata (links, titles, image URLs)

    Args:
        driver: Selenium WebDriver instance.
    """

    # ── Locators ──────────────────────────────────────────
    ARTICLE = (By.CSS_SELECTOR, "article")
    ARTICLE_TITLE_LINK = (By.CSS_SELECTOR, "h2.c_t a")
    ARTICLE_IMAGE = (By.CSS_SELECTOR, "figure.c_m img")
    SECTION_HEADER = (By.CSS_SELECTOR, "h2.c_t")

    def __init__(self, driver: WebDriver) -> None:
        super().__init__(driver)

    def navigate(self) -> "OpinionPage":
        """Navigate to the El País Opinion section.

        Returns:
            Self for method chaining.
        """
        logger.info("Navigating to El País Opinion section: %s", OPINION_URL)
        self.driver.get(OPINION_URL)
        self.accept_cookies()
        return self

    def is_in_spanish(self) -> bool:
        """Verify the page content is displayed in Spanish.

        Checks for the presence of "Opinión" in the page source,
        which confirms the Spanish edition is loaded (not english.elpais.com).

        Returns:
            True if the page is confirmed to be in Spanish.
        """
        page_source = self.driver.page_source.lower()
        indicators = ["opinión", "opinión", "editoriales", "tribunas", "columnas"]
        found = any(indicator.lower() in page_source for indicator in indicators)

        if found:
            logger.info("✓ Page confirmed to be in Spanish")
        else:
            logger.warning("⚠ Could not confirm Spanish language on page")

        return found

    def get_article_links(self, count: int = 5) -> list[dict[str, str | None]]:
        """Extract article metadata from the first N articles on the listing page.

        For each article, extracts:
          - title: The article headline text (Spanish)
          - url: The link to the full article page
          - image_url: The cover image URL (None if unavailable)

        Args:
            count: Number of articles to fetch (default: 5).

        Returns:
            List of dicts with keys: title, url, image_url.
        """
        articles = self.wait_for_elements(*self.ARTICLE)

        if not articles:
            logger.error("No articles found on the Opinion page")
            return []

        logger.info("Found %d articles on the page, extracting first %d", len(articles), count)

        results = []
        for i, article in enumerate(articles[:count]):
            try:
                self.scroll_to_element(article)

                # Extract title and URL from the h2 > a element
                title_link = article.find_element(*self.ARTICLE_TITLE_LINK)
                title = self.safe_get_text(title_link)
                url = self.safe_get_attribute(title_link, "href")

                # Extract cover image URL (optional — not all articles have one)
                image_url = None
                try:
                    img = article.find_element(*self.ARTICLE_IMAGE)
                    image_url = self.safe_get_attribute(img, "src")
                except Exception:
                    logger.debug("Article %d has no cover image on listing page", i + 1)

                results.append({
                    "title": title,
                    "url": url,
                    "image_url": image_url,
                })

                logger.info(
                    "Article %d: %s",
                    i + 1,
                    title[:80] + "..." if len(title) > 80 else title,
                )

            except Exception as e:
                logger.warning("Failed to extract article %d: %s", i + 1, e)
                continue

        return results
