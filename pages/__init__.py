"""Page Object Model for the El País scraper.

Provides page-level abstractions for Selenium interactions,
isolating DOM selectors from test logic for maintainability.
"""

from pages.base_page import BasePage
from pages.opinion_page import OpinionPage
from pages.article_page import ArticlePage

__all__ = ["BasePage", "OpinionPage", "ArticlePage"]
