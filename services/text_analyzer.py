"""Text analysis for translated article headers.

Identifies words that appear more than twice across all
translated headers combined, as required by the assignment.
"""

import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)

# Common English stopwords filtered from results.
# These are articles, prepositions, and conjunctions that would
# dominate the frequency count without providing useful insight.
STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "it", "as", "be",
    "was", "are", "been", "has", "had", "have", "do", "does", "did",
    "not", "no", "its", "that", "this", "these", "those", "what",
    "which", "who", "whom", "when", "where", "how", "than", "so",
})


class TextAnalyzer:
    """Analyzes word frequency across a collection of text headers.

    Example:
        analyzer = TextAnalyzer()
        repeated = analyzer.find_repeated_words(
            ["The big challenge", "A big diplomatic move", "The big test"],
            min_count=2,
        )
        # Returns: {"big": 3, "the": 2} (if stopwords disabled)
        # Returns: {"big": 3}           (if stopwords enabled, default)
    """

    def __init__(self, filter_stopwords: bool = True) -> None:
        """Initialize the analyzer.

        Args:
            filter_stopwords: If True, common English stopwords are excluded
                from the frequency count. Defaults to True for meaningful output.
        """
        self.filter_stopwords = filter_stopwords

    def find_repeated_words(
        self, headers: list[str], min_count: int = 2
    ) -> dict[str, int]:
        """Find words that appear more than `min_count` times across all headers.

        Processing steps:
          1. Combine all headers into a single text
          2. Tokenize into words (lowercase, strip punctuation)
          3. Optionally filter stopwords
          4. Count occurrences
          5. Return words exceeding the threshold

        Args:
            headers: List of translated article header strings.
            min_count: Minimum occurrence threshold (default: 2, meaning
                the assignment's ">2" requirement returns words with count >= 3).

        Returns:
            Dictionary of {word: count} for words appearing more than
            `min_count` times, sorted by count descending.
        """
        if not headers:
            logger.warning("No headers provided for analysis")
            return {}

        # Tokenize: lowercase, extract only alphabetic words
        all_words = []
        for header in headers:
            words = re.findall(r"[a-zA-Z]+", header.lower())
            all_words.extend(words)

        logger.info("Total words extracted from %d headers: %d", len(headers), len(all_words))

        # Optionally filter stopwords
        if self.filter_stopwords:
            all_words = [w for w in all_words if w not in STOPWORDS]
            logger.info("Words after stopword filtering: %d", len(all_words))

        # Count and filter by threshold
        word_counts = Counter(all_words)
        repeated = {
            word: count
            for word, count in word_counts.most_common()
            if count > min_count
        }

        if repeated:
            logger.info("Found %d repeated words (count > %d)", len(repeated), min_count)
        else:
            logger.info("No words found with count > %d", min_count)

        return repeated
