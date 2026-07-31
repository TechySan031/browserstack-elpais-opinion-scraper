"""Page object for the El País Opinion section listing page.

Handles navigation to the Opinion section and extraction of
article links, titles, and cover image URLs from the listing grid.
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
    ARTICLE_CONTAINERS = (By.CSS_SELECTOR, "article")

    # Title link candidate locators within an <article> container
    TITLE_LINK_LOCATORS = [
        (By.CSS_SELECTOR, "h2.c_t a"),
        (By.CSS_SELECTOR, "h2 a"),
        (By.CSS_SELECTOR, "header h2 a"),
        (By.CSS_SELECTOR, "h3 a"),
    ]

    # Image candidate locators within an <article> container
    IMAGE_LOCATORS = [
        (By.CSS_SELECTOR, "figure.c_m img"),
        (By.CSS_SELECTOR, "figure img"),
        (By.CSS_SELECTOR, "img"),
    ]

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

        Checks for Spanish edition markers in the page source.

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

        Uses fallback locator chains to guarantee extraction across different card formats.

        Args:
            count: Number of articles to fetch (default: 5).

        Returns:
            List of dicts with keys: title, url, image_url.
        """
        articles = self.wait_for_elements(*self.ARTICLE_CONTAINERS)

        if not articles:
            logger.error("No articles found on the Opinion page")
            return []

        logger.info("Found %d article cards on page, fetching first %d", len(articles), count)

        results = []
        for i, article in enumerate(articles):
            if len(results) >= count:
                break

            try:
                self.scroll_to_element(article)

                # 1. Extract title link
                title = ""
                url = None
                for by, locator in self.TITLE_LINK_LOCATORS:
                    try:
                        links = article.find_elements(by, locator)
                        for link in links:
                            t = self.safe_get_text(link)
                            u = self.safe_get_attribute(link, "href")
                            if u and u.startswith("http"):
                                title = t
                                url = u
                                break
                        if url:
                            break
                    except Exception:
                        continue

                if not url:
                    logger.debug("Article card %d has no valid article link, skipping", i + 1)
                    continue

                # 2. Extract cover image
                image_url = None
                for by, locator in self.IMAGE_LOCATORS:
                    try:
                        imgs = article.find_elements(by, locator)
                        for img in imgs:
                            src = self.safe_get_attribute(img, "src") or self.safe_get_attribute(img, "data-src")
                            if src and src.startswith("http"):
                                image_url = src
                                break
                        if image_url:
                            break
                    except Exception:
                        continue

                results.append({
                    "title": title or f"Article {len(results) + 1}",
                    "url": url,
                    "image_url": image_url,
                })

                logger.info(
                    "Article card %d extracted: %s (%s)",
                    len(results),
                    title[:60] if title else "No title",
                    url[:60],
                )

            except Exception as e:
                logger.warning("Failed to process article card %d: %s", i + 1, e)
                continue

        logger.info("Successfully extracted %d article links from listing", len(results))
        return results
