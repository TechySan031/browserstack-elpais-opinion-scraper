"""End-to-end test: Scrape El País Opinion section, translate, and analyze.

This test implements the full assignment workflow:
  1. Navigate to El País and verify Spanish language
  2. Scrape the first 5 Opinion articles (title, content, image)
  3. Translate article titles from Spanish to English
  4. Analyze translated headers for repeated words

Designed to run identically across local Chrome and 5 BrowserStack
parallel sessions (3 desktop + 2 mobile browsers).
"""

import logging

import pytest

from models import Article
from pages import OpinionPage, ArticlePage
from services import TranslationService, TextAnalyzer
from utils import download_image

logger = logging.getLogger(__name__)

ARTICLE_COUNT = 5


def _set_browserstack_session_name(driver, name: str) -> None:
    """Set the session name in the BrowserStack dashboard.

    Only executes when running on BrowserStack — fails silently
    during local execution.
    """
    try:
        driver.execute_script(
            f'browserstack_executor: {{"action": "setSessionName", '
            f'"arguments": {{"name": "{name}"}}}}'
        )
    except Exception:
        pass  # Not on BrowserStack — expected during local runs


def _set_browserstack_status(driver, status: str, reason: str) -> None:
    """Set the session status (passed/failed) in the BrowserStack dashboard.

    Only executes when running on BrowserStack — fails silently
    during local execution.
    """
    try:
        driver.execute_script(
            f'browserstack_executor: {{"action": "setSessionStatus", '
            f'"arguments": {{"status": "{status}", "reason": "{reason}"}}}}'
        )
    except Exception:
        pass  # Not on BrowserStack — expected during local runs


@pytest.mark.e2e
def test_scrape_elpais_opinion_articles(driver):
    """Scrape El País Opinion articles, translate titles, and analyze word frequency.

    This is a single cohesive test that exercises the full workflow.
    Each step is logged clearly for demo readability.
    """
    _set_browserstack_session_name(driver, "El País Opinion Scraper")

    try:
        # ────────────────────────────────────────────────────────
        # STEP 1: Navigate to the Opinion section
        # ────────────────────────────────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 1: Navigate to El País Opinion section")
        logger.info("=" * 60)

        opinion_page = OpinionPage(driver)
        opinion_page.navigate()

        # ────────────────────────────────────────────────────────
        # STEP 2: Verify Spanish language
        # ────────────────────────────────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 2: Verify page is in Spanish")
        logger.info("=" * 60)

        assert opinion_page.is_in_spanish(), (
            "Page is not displayed in Spanish. "
            "Ensure you are accessing elpais.com (not english.elpais.com)."
        )

        # ────────────────────────────────────────────────────────
        # STEP 3: Fetch first 5 articles
        # ────────────────────────────────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 3: Fetch first %d articles from Opinion section", ARTICLE_COUNT)
        logger.info("=" * 60)

        article_links = opinion_page.get_article_links(count=ARTICLE_COUNT)
        assert len(article_links) > 0, "No articles found on the Opinion page"

        logger.info("Found %d articles to process", len(article_links))

        # ────────────────────────────────────────────────────────
        # STEP 4: Extract title, content, and image for each article
        # ────────────────────────────────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 4: Extract article details (title, content, image)")
        logger.info("=" * 60)

        articles: list[Article] = []
        article_page = ArticlePage(driver)

        for i, link in enumerate(article_links, start=1):
            logger.info("-" * 40)
            logger.info("Processing article %d of %d", i, len(article_links))
            logger.info("-" * 40)

            # Navigate to article page
            article_page.navigate(link["url"])

            # Extract title
            title = article_page.get_title()
            if not title:
                title = link.get("title", f"Article {i}")
                logger.warning("Using listing title as fallback: %s", title)

            # Extract content
            content = article_page.get_content()

            # Extract cover image URL (prefer article page, fall back to listing)
            image_url = article_page.get_cover_image_url()
            if not image_url:
                image_url = link.get("image_url")

            # Create Article model
            article = Article(
                title=title,
                content=content,
                image_url=image_url,
            )
            articles.append(article)

            # Print title and content in Spanish (assignment requirement)
            logger.info("📰 Title (ES): %s", article.title)
            logger.info("📝 Content (ES): %s", article.content[:300] + "..." if len(article.content) > 300 else article.content)

            # Download cover image if available (assignment requirement)
            if article.image_url:
                # Create a safe filename from the article index
                ext = article.image_url.split(".")[-1].split("?")[0][:4] or "jpg"
                filename = f"article_{i}.{ext}"
                success = download_image(article.image_url, filename)
                logger.info(
                    "🖼️  Image %s: %s",
                    "saved" if success else "not available",
                    filename,
                )
            else:
                logger.info("🖼️  No cover image available for this article")

        assert len(articles) > 0, "No articles were successfully extracted"

        # ────────────────────────────────────────────────────────
        # STEP 5: Translate article titles to English
        # ────────────────────────────────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 5: Translate article titles to English")
        logger.info("=" * 60)

        translator = TranslationService()

        for article in articles:
            article.translated_title = translator.translate(article.title)
            logger.info("🌐 ES: %s", article.title)
            logger.info("   EN: %s", article.translated_title)

        # ────────────────────────────────────────────────────────
        # STEP 6: Analyze translated headers for repeated words
        # ────────────────────────────────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 6: Analyze word frequency in translated headers")
        logger.info("=" * 60)

        translated_titles = [a.translated_title for a in articles if a.translated_title]
        analyzer = TextAnalyzer()
        repeated_words = analyzer.find_repeated_words(translated_titles, min_count=2)

        if repeated_words:
            logger.info("Words repeated more than twice across all headers:")
            for word, count in repeated_words.items():
                logger.info("  %-20s → %d occurrences", word, count)
        else:
            logger.info("No words found repeated more than twice across headers")

        # ────────────────────────────────────────────────────────
        # SUMMARY
        # ────────────────────────────────────────────────────────
        logger.info("=" * 60)
        logger.info("✅ SUMMARY")
        logger.info("=" * 60)
        logger.info("Articles scraped:    %d", len(articles))
        logger.info("Articles translated: %d", len(translated_titles))
        logger.info("Repeated words:      %d", len(repeated_words))

        # Mark BrowserStack session as passed
        _set_browserstack_status(
            driver,
            "passed",
            f"Successfully scraped {len(articles)} articles",
        )

    except Exception as e:
        # Mark BrowserStack session as failed with reason
        _set_browserstack_status(driver, "failed", str(e)[:255])
        raise
