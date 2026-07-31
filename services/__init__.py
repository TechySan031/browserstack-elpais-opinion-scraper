"""Business logic services for the El País scraper.

These modules have no Selenium dependency and can be
unit-tested independently of browser sessions.
"""

from services.translator import TranslationService
from services.text_analyzer import TextAnalyzer

__all__ = ["TranslationService", "TextAnalyzer"]
