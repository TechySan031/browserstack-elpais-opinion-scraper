"""Page object for an individual El País article page.

Handles extraction of the article title, body content, and
cover image from the full article view.

Selectors verified against live DOM (July 2026):
  - Title: h1.a_t
  - Body paragraphs: .a_c p
  - Cover image: figure.a_m img
"""

import logging

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class ArticlePage(BasePage):
    """Represents a single El País article page.

    Responsibilities:
      - Extract the article title
      - Extract the full article body text
      - Extract the cover/hero image URL

    Args:
        driver: Selenium WebDriver instance.
    """

    # ── Locators ──────────────────────────────────────────
    TITLE = (By.CSS_SELECTOR, "h1.a_t")
    BODY_PARAGRAPHS = (By.CSS_SELECTOR, ".a_c p")
    COVER_IMAGE = (By.CSS_SELECTOR, "figure.a_m img")

    # Fallback locators in case primary selectors change
    TITLE_FALLBACK = (By.TAG_NAME, "h1")
    BODY_FALLBACK = (By.CSS_SELECTOR, "article p")
    IMAGE_FALLBACK = (By.CSS_SELECTOR, "article figure img")

    def __init__(self, driver: WebDriver) -> None:
        super().__init__(driver)

    def navigate(self, url: str) -> "ArticlePage":
        """Navigate to a specific article URL.

        Args:
            url: Full URL of the article.

        Returns:
            Self for method chaining.
        """
        logger.info("Navigating to article: %s", url)
        self.driver.get(url)
        return self

    def get_title(self) -> str:
        """Extract the article title.

        Tries the primary selector (h1.a_t) first, then falls back
        to a generic h1 tag if the class-based selector fails.

        Returns:
            The article title text, or empty string if extraction fails.
        """
        try:
            title_el = self.wait_for_element(*self.TITLE)
            return self.safe_get_text(title_el)
        except TimeoutException:
            logger.warning("Primary title selector failed, trying fallback")
            try:
                title_el = self.wait_for_element(*self.TITLE_FALLBACK)
                return self.safe_get_text(title_el)
            except TimeoutException:
                logger.error("Could not extract article title")
                return ""

    def get_content(self) -> str:
        """Extract the full article body text.

        Collects text from all <p> tags within the article body container.
        Some articles may be behind a paywall, in which case only the
        available (preview) content is returned.

        Returns:
            The concatenated article body text, or empty string if extraction fails.
        """
        try:
            paragraphs = self.wait_for_elements(*self.BODY_PARAGRAPHS)
        except TimeoutException:
            logger.warning("Primary body selector failed, trying fallback")
            paragraphs = self.wait_for_elements(*self.BODY_FALLBACK)

        if not paragraphs:
            logger.warning("No body paragraphs found — article may be paywalled")
            return ""

        content_parts = []
        for p in paragraphs:
            text = self.safe_get_text(p)
            if text:
                content_parts.append(text)

        content = "\n".join(content_parts)

        if not content:
            logger.warning("Article body is empty after extraction")

        return content

    def get_cover_image_url(self) -> str | None:
        """Extract the cover/hero image URL.

        Returns:
            The image URL string, or None if no cover image is present.
        """
        for locator in [self.COVER_IMAGE, self.IMAGE_FALLBACK]:
            try:
                img = self.driver.find_element(*locator)
                url = self.safe_get_attribute(img, "src")
                if url:
                    return url
            except NoSuchElementException:
                continue

        logger.info("No cover image found for this article")
        return None
