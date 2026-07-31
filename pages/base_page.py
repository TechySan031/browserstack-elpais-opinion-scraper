"""Base page object with shared Selenium helpers.

Every page object inherits from BasePage to get consistent
wait strategies, scroll helpers, and cookie consent handling.
These are the operations that break most often across browsers
and viewports — centralizing them here keeps page objects lean.
"""

import logging

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

# Default timeout accounts for BrowserStack network latency.
DEFAULT_TIMEOUT = 20


class BasePage:
    """Base class for all page objects.

    Provides common Selenium operations with built-in waits
    and error handling suitable for cross-browser execution.

    Args:
        driver: Selenium WebDriver instance.
        timeout: Maximum wait time in seconds for element operations.
    """

    def __init__(self, driver: WebDriver, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(
            driver,
            timeout,
            ignored_exceptions=[StaleElementReferenceException],
        )

    def wait_for_element(self, by: By, locator: str) -> WebElement:
        """Wait for a single element to be present in the DOM.

        Args:
            by: Locator strategy (e.g., By.CSS_SELECTOR).
            locator: The locator string.

        Returns:
            The located WebElement.

        Raises:
            TimeoutException: If the element is not found within the timeout.
        """
        return self.wait.until(EC.presence_of_element_located((by, locator)))

    def wait_for_elements(self, by: By, locator: str) -> list[WebElement]:
        """Wait for multiple elements to be present in the DOM.

        Args:
            by: Locator strategy.
            locator: The locator string.

        Returns:
            List of located WebElements, or empty list if none found.
        """
        try:
            return self.wait.until(EC.presence_of_all_elements_located((by, locator)))
        except TimeoutException:
            logger.warning("No elements found for locator: %s", locator)
            return []

    def wait_for_clickable(self, by: By, locator: str) -> WebElement:
        """Wait for an element to be clickable.

        Args:
            by: Locator strategy.
            locator: The locator string.

        Returns:
            The clickable WebElement.
        """
        return self.wait.until(EC.element_to_be_clickable((by, locator)))

    def safe_get_text(self, element: WebElement) -> str:
        """Extract text from an element, handling stale references.

        Args:
            element: The WebElement to extract text from.

        Returns:
            The element's text content, or empty string on failure.
        """
        try:
            return element.text.strip()
        except StaleElementReferenceException:
            logger.warning("Stale element encountered while getting text")
            return ""

    def safe_get_attribute(self, element: WebElement, attribute: str) -> str | None:
        """Extract an attribute from an element, handling stale references.

        Args:
            element: The WebElement to query.
            attribute: The attribute name (e.g., "href", "src").

        Returns:
            The attribute value, or None on failure.
        """
        try:
            return element.get_attribute(attribute)
        except StaleElementReferenceException:
            logger.warning("Stale element encountered while getting attribute '%s'", attribute)
            return None

    def scroll_to_element(self, element: WebElement) -> None:
        """Scroll an element into view. Essential for mobile browsers
        where lazy-loaded content may not render until visible.

        Args:
            element: The WebElement to scroll to.
        """
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            element,
        )

    def accept_cookies(self) -> None:
        """Dismiss the cookie consent banner if present.

        El País displays a GDPR cookie banner that overlays the page
        and blocks element interaction. This method attempts to click
        the accept button using multiple selector strategies.
        """
        cookie_selectors = [
            (By.ID, "didomi-notice-agree-button"),
            (By.CSS_SELECTOR, "button[aria-label='Aceptar y cerrar']"),
            (By.CSS_SELECTOR, ".didomi-popup-notice-buttons button:first-child"),
            (By.XPATH, "//button[contains(text(), 'Aceptar')]"),
        ]

        for by, locator in cookie_selectors:
            try:
                button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((by, locator))
                )
                button.click()
                logger.info("Cookie consent accepted via: %s", locator)
                return
            except (TimeoutException, NoSuchElementException):
                continue

        logger.info("No cookie consent banner detected (may already be accepted)")
