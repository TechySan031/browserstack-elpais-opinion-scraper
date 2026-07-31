"""pytest configuration and fixtures for El País scraper.

Driver fixture design:
  The BrowserStack SDK intercepts webdriver.Chrome() automatically
  when tests are run via `browserstack-sdk pytest`. This fixture
  remains clean and framework-agnostic.

  - Local run:       pytest tests/ -v -s
  - BrowserStack:    browserstack-sdk pytest tests/ -v -s
"""

import os
from typing import Generator

import pytest
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

# Load .env for local development
load_dotenv()


@pytest.fixture
def driver() -> Generator[WebDriver, None, None]:
    """Create and yield a Selenium WebDriver instance.

    Configures Chrome options suitable for both local execution and CI.
    When executed via `browserstack-sdk pytest`, the BrowserStack SDK
    intercepts driver creation and manages grid allocation.

    Yields:
        WebDriver: Active Selenium WebDriver session.
    """
    options = webdriver.ChromeOptions()

    if os.getenv("HEADLESS", "false").lower() == "true":
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")

    # Standard stability options across environments
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver_instance = webdriver.Chrome(options=options)

    # Safely attempt window maximization
    # (mobile WebDrivers on BrowserStack do not support maximize_window)
    try:
        driver_instance.maximize_window()
    except Exception:
        pass

    driver_instance.implicitly_wait(5)

    try:
        yield driver_instance
    finally:
        try:
            driver_instance.quit()
        except Exception:
            pass
