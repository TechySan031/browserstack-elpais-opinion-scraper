"""Page object for an individual El País article page.

Handles extraction of the article title, body content, and
cover image from the full article view with strict page synchronization
and multi-tier locator strategies.

Selectors verified against live El País DOM:
  - Title: h1.a_t, h1.c_t, header h1, article h1, h1
  - Body: div[data-dtm-region="articulo_cuerpo"] p, .a_c p, article p, .c_b p
  - Cover image: figure.a_m img, article figure img, picture img
"""

import logging
import time
from urllib.parse import urlparse

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class ArticlePage(BasePage):
    """Represents a single El País article page.

    Responsibilities:
      - Synchronize page load after navigation (prevent stale previous-page state)
      - Extract article title using resilient multi-selector fallback chain
      - Extract full article body text across different section DOM layouts
      - Extract cover/hero image URL

    Args:
        driver: Selenium WebDriver instance.
    """

    # ── Title Locators (ordered from specific to generic) ──
    TITLE_LOCATORS = [
        (By.CSS_SELECTOR, "h1.a_t"),
        (By.CSS_SELECTOR, "h1.c_t"),
        (By.CSS_SELECTOR, "h1[data-dtm-region='articulo_titulo']"),
        (By.CSS_SELECTOR, "header h1"),
        (By.CSS_SELECTOR, "article h1"),
        (By.TAG_NAME, "h1"),
    ]

    # ── Body Locators (handles standard articles, opinion columns, & editorials) ──
    BODY_LOCATORS = [
        (By.CSS_SELECTOR, "div[data-dtm-region='articulo_cuerpo'] p"),
        (By.CSS_SELECTOR, ".a_c p"),
        (By.CSS_SELECTOR, "article p"),
        (By.CSS_SELECTOR, "div.article_body p"),
        (By.CSS_SELECTOR, ".c_b p"),
        (By.CSS_SELECTOR, "section.a_c p"),
    ]

    # ── Cover Image Locators ──
    IMAGE_LOCATORS = [
        (By.CSS_SELECTOR, "figure.a_m img"),
        (By.CSS_SELECTOR, "article figure img"),
        (By.CSS_SELECTOR, "header figure img"),
        (By.CSS_SELECTOR, "picture img"),
    ]

    def __init__(self, driver: WebDriver) -> None:
        super().__init__(driver)

    def navigate(self, url: str) -> "ArticlePage":
        """Navigate to an article URL and synchronize DOM loading.

        Synchronization checks:
          1. Issue driver.get(url)
          2. Wait for document.readyState == 'complete'
          3. Wait until current URL path matches target URL (prevents reading previous page state)
          4. Wait for title element (h1) to be visible in DOM

        Args:
            url: Full URL of the article.

        Returns:
            Self for method chaining.
        """
        logger.info("[SYNC] Navigating to article: %s", url)
        self.driver.get(url)

        # 1. Wait for document complete
        try:
            self.wait.until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            logger.warning("[SYNC] Page load state incomplete for: %s", url)

        # 2. Wait for URL path synchronization
        target_path = urlparse(url).path
        if target_path and len(target_path) > 5:
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: urlparse(d.current_url).path == target_path
                )
                logger.info("[SYNC] URL path synchronized: %s", target_path)
            except TimeoutException:
                logger.warning(
                    "[SYNC] URL path mismatch after 10s (expected: %s, actual: %s)",
                    target_path,
                    self.driver.current_url,
                )

        # 3. Wait for any h1 element to be present and non-empty
        try:
            WebDriverWait(self.driver, 10).until(
                lambda d: any(
                    el.text.strip()
                    for el in d.find_elements(By.TAG_NAME, "h1")
                )
            )
            logger.info("[SYNC] Article DOM title element ready")
        except TimeoutException:
            logger.warning("[SYNC] Timeout waiting for h1 element readiness")

        return self

    def get_title(self) -> str:
        """Extract the article title using multi-strategy selector chain.

        Returns:
            The article title text, or empty string if extraction fails.
        """
        for by, locator in self.TITLE_LOCATORS:
            try:
                elements = self.driver.find_elements(by, locator)
                for el in elements:
                    try:
                        text = el.text.strip()
                        if text:
                            logger.info("[TITLE] Extracted via '%s': %s", locator, text[:60])
                            return text
                    except StaleElementReferenceException:
                        logger.warning("[STALE] Element became stale during title text read, retrying")
                        continue
            except NoSuchElementException:
                continue
            except Exception as e:
                logger.debug("[TITLE] Selector '%s' error: %s", locator, e)
                continue

        logger.warning("[TITLE] All primary and fallback title selectors failed")
        return ""

    def get_content(self) -> str:
        """Extract the full article body text.

        Iterates through candidate body container paragraph selectors.
        Filters out non-content snippets (captions, disclosures, short metadata).

        Returns:
            Concatenated article body paragraphs, or empty string if paywalled/unavailable.
        """
        paragraphs_elements = []
        winning_selector = None

        for by, locator in self.BODY_LOCATORS:
            try:
                elements = self.driver.find_elements(by, locator)
                # Ensure paragraphs have actual text content
                valid_paras = []
                for el in elements:
                    try:
                        t = el.text.strip()
                        if t and len(t) > 20:  # filter out short meta tags/dates
                            valid_paras.append(t)
                    except StaleElementReferenceException:
                        continue

                if valid_paras:
                    paragraphs_elements = valid_paras
                    winning_selector = locator
                    break
            except Exception:
                continue

        if not paragraphs_elements:
            logger.warning("[BODY] Protected or paywalled article — 0 body paragraphs extracted")
            return ""

        content = "\n".join(paragraphs_elements)
        logger.info(
            "[BODY] Extracted %d paragraphs (%d chars) via '%s'",
            len(paragraphs_elements),
            len(content),
            winning_selector,
        )
        return content

    def get_cover_image_url(self) -> str | None:
        """Extract the cover/hero image URL using multi-strategy locator chain.

        Returns:
            The image URL string, or None if unavailable.
        """
        for by, locator in self.IMAGE_LOCATORS:
            try:
                images = self.driver.find_elements(by, locator)
                for img in images:
                    try:
                        src = img.get_attribute("src") or img.get_attribute("data-src")
                        if src and src.startswith("http"):
                            logger.info("[IMAGE] Found cover image via '%s': %s", locator, src[:70])
                            return src
                    except StaleElementReferenceException:
                        continue
            except Exception:
                continue

        logger.info("[IMAGE] No cover image found for this article")
        return None
