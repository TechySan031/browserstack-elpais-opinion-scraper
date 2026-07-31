"""Utility functions for the El País scraper.

Contains the image download helper used to save article cover images.
Designed for reliability — never crashes the test on download failure.
"""

import logging
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

logger = logging.getLogger(__name__)

# Directory where downloaded images are saved.
DOWNLOADS_DIR = Path(__file__).parent / "downloads"


def download_image(url: str, filename: str, base_url: str = "https://elpais.com") -> bool:
    """Download an image from a URL and save it to the downloads directory.

    Args:
        url: The image URL (absolute or relative).
        filename: The filename to save the image as (e.g., "article_1.jpg").
        base_url: Base URL for resolving relative image paths.

    Returns:
        True if the image was downloaded successfully, False otherwise.
        Never raises — failures are logged and the test continues.
    """
    try:
        # Resolve relative URLs
        if not url.startswith(("http://", "https://")):
            url = urljoin(base_url, url)

        logger.info("Downloading image: %s", url)

        response = requests.get(url, timeout=15, stream=True)
        response.raise_for_status()

        # Ensure downloads directory exists
        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

        filepath = DOWNLOADS_DIR / filename
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = os.path.getsize(filepath)
        logger.info("Saved image: %s (%d bytes)", filepath.name, file_size)
        return True

    except requests.RequestException as e:
        logger.warning("Failed to download image from %s: %s", url, e)
        return False
    except OSError as e:
        logger.warning("Failed to save image to disk: %s", e)
        return False
