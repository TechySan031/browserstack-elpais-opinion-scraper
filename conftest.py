"""pytest configuration and fixtures.

Driver fixture design:
  The BrowserStack SDK intercepts webdriver.Chrome() automatically
  when tests are run via `browserstack-sdk pytest`. This means our
  fixture is intentionally simple — no BrowserStack-specific branching,
  no Remote() connections, no capability management.

  - Local run:       `pytest tests/ -v -s`       → uses local Chrome
  - BrowserStack:    `browserstack-sdk pytest tests/ -v -s` → SDK patches driver
"""

import os

import pytest
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Load .env for local development (BrowserStack SDK handles its own env in CI)
load_dotenv()


@pytest.fixture
def driver():
    """Create a Selenium WebDriver instance.

    Local mode: Creates a Chrome browser instance. Set HEADLESS=true
    in .env to run headless (useful for CI or quick local validation).

    BrowserStack mode: The BrowserStack SDK automatically intercepts
    this webdriver.Chrome() call and creates a remote session on
    the BrowserStack grid — no code changes needed.

    Yields:
        WebDriver: A Selenium WebDriver instance.
    """
    options = Options()

    if os.getenv("HEADLESS", "false").lower() == "true":
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")

    # Standard options for stability across environments
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    
    # Safely attempt window maximization (mobile browsers on BrowserStack do not support maximize_window)
    try:
        driver.maximize_window()
    except Exception:
        pass

    driver.implicitly_wait(5)

    try:
        yield driver
    finally:
        try:
            driver.quit()
        except Exception:
            pass

