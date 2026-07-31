"""Utility functions for the El País scraper.

Contains the image download helper used to save article cover images.
Designed for reliability — never crashes the test on download failure.
"""

import logging
import os
import time
from pathlib import Path
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)

# Directory where downloaded images are saved.
DOWNLOADS_DIR = Path(__file__).parent / "downloads"

# Standard User-Agent to prevent CDN throttling from imagenes.elpais.com
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}

MAX_DOWNLOAD_RETRIES = 3
DEFAULT_DOWNLOAD_TIMEOUT = 25


def download_image(url: str, filename: str, base_url: str = "https://elpais.com") -> bool:
    """Download an image from a URL and save it to the downloads directory.

    Includes user-agent headers, increased timeout (25s), and exponential backoff
    retries to handle transient CDN latency on imagenes.elpais.com.

    Args:
        url: The image URL (absolute or relative).
        filename: The filename to save the image as (e.g., "article_1.jpg").
        base_url: Base URL for resolving relative image paths.

    Returns:
        True if the image was downloaded successfully, False otherwise.
        Never raises — failures are logged and the test continues.
    """
    if not url:
        logger.warning("Download skipped: empty image URL")
        return False

    try:
        # Resolve relative URLs
        if not url.startswith(("http://", "https://")):
            url = urljoin(base_url, url)

        # Ensure downloads directory exists
        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        filepath = DOWNLOADS_DIR / filename

        for attempt in range(1, MAX_DOWNLOAD_RETRIES + 1):
            try:
                logger.info("Downloading image (attempt %d/%d): %s", attempt, MAX_DOWNLOAD_RETRIES, url)
                response = requests.get(
                    url,
                    headers=HTTP_HEADERS,
                    timeout=DEFAULT_DOWNLOAD_TIMEOUT,
                    stream=True,
                )
                response.raise_for_status()

                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                file_size = os.path.getsize(filepath)
                logger.info("Saved image: %s (%d bytes)", filepath.name, file_size)
                return True

            except requests.RequestException as e:
                logger.warning(
                    "Image download attempt %d/%d failed for %s: %s",
                    attempt,
                    MAX_DOWNLOAD_RETRIES,
                    url,
                    e,
                )
                if attempt < MAX_DOWNLOAD_RETRIES:
                    sleep_time = 2 * attempt
                    logger.info("Retrying image download in %d seconds...", sleep_time)
                    time.sleep(sleep_time)

        logger.error("Failed to download image after %d attempts: %s", MAX_DOWNLOAD_RETRIES, url)
        return False

    except OSError as e:
        logger.warning("Failed to save image to disk: %s", e)
        return False
