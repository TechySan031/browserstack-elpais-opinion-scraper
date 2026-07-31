"""Unit tests for the TextAnalyzer service.

These tests run without Selenium or any external API,
making them suitable for CI and quick local validation.
"""

import pytest

from services.text_analyzer import TextAnalyzer


class TestTextAnalyzer:
    """Tests for word frequency analysis."""

    def setup_method(self):
        """Create a fresh analyzer for each test."""
        self.analyzer = TextAnalyzer(filter_stopwords=True)

    @pytest.mark.unit
    def test_finds_repeated_words(self):
        """Words appearing more than twice should be detected."""
        headers = [
            "The big humanitarian challenge",
            "A big diplomatic challenge today",
            "The big political challenge ahead",
        ]
        result = self.analyzer.find_repeated_words(headers, min_count=2)

        assert "big" in result
        assert result["big"] == 3
        assert "challenge" in result
        assert result["challenge"] == 3

    @pytest.mark.unit
    def test_stopwords_are_filtered(self):
        """Common English stopwords should not appear in results."""
        headers = [
            "The the the quick brown fox",
            "The the the slow brown dog",
            "The the the red brown cat",
        ]
        result = self.analyzer.find_repeated_words(headers, min_count=2)

        # "the" appears 9 times but should be filtered as a stopword
        assert "the" not in result
        # "brown" appears 3 times and is not a stopword
        assert "brown" in result
        assert result["brown"] == 3

    @pytest.mark.unit
    def test_stopwords_included_when_disabled(self):
        """When stopword filtering is disabled, all words are counted."""
        analyzer = TextAnalyzer(filter_stopwords=False)
        headers = [
            "The big test",
            "The big test",
            "The big test",
        ]
        result = analyzer.find_repeated_words(headers, min_count=2)

        assert "the" in result
        assert result["the"] == 3

    @pytest.mark.unit
    def test_case_insensitive(self):
        """Word matching should be case-insensitive."""
        headers = [
            "Spain is great",
            "SPAIN is wonderful",
            "spain is beautiful",
        ]
        result = self.analyzer.find_repeated_words(headers, min_count=2)

        assert "spain" in result
        assert result["spain"] == 3

    @pytest.mark.unit
    def test_punctuation_stripped(self):
        """Punctuation should not affect word matching."""
        headers = [
            "Hello, world!",
            "Hello world.",
            "Hello world?",
        ]
        result = self.analyzer.find_repeated_words(headers, min_count=2)

        assert "hello" in result
        assert result["hello"] == 3
        assert "world" in result
        assert result["world"] == 3

    @pytest.mark.unit
    def test_empty_headers(self):
        """Empty header list should return empty dict."""
        result = self.analyzer.find_repeated_words([])
        assert result == {}

    @pytest.mark.unit
    def test_no_repeated_words(self):
        """When no words repeat more than threshold, return empty."""
        headers = [
            "Alpha bravo charlie",
            "Delta echo foxtrot",
        ]
        result = self.analyzer.find_repeated_words(headers, min_count=2)
        assert result == {}

    @pytest.mark.unit
    def test_min_count_threshold(self):
        """The min_count parameter controls the threshold correctly."""
        headers = ["word word word other other"]

        # min_count=2 → words appearing more than 2 times
        result = self.analyzer.find_repeated_words(headers, min_count=2)
        assert "word" in result      # appears 3 times (> 2)
        assert "other" not in result  # appears 2 times (not > 2)

        # min_count=1 → words appearing more than 1 time
        result = self.analyzer.find_repeated_words(headers, min_count=1)
        assert "word" in result
        assert "other" in result
