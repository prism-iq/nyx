"""
CIPHER Hash Learning Module
SHAKE256-based entropy scoring for quality assessment and novelty detection

The idea: novel/high-quality content has higher information entropy.
We use SHAKE256 (variable-length hash) to:
1. Detect duplicate/near-duplicate content
2. Score information density/novelty
3. Track concept evolution over time
"""

import hashlib
import math
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from collections import Counter
import re


@dataclass
class EntropyScore:
    """Result of entropy analysis"""
    hash: str                    # SHAKE256 hash
    byte_entropy: float          # Shannon entropy of hash bytes (0-8)
    text_entropy: float          # Shannon entropy of source text (0-log2(vocab))
    compression_ratio: float     # Estimated compressibility
    novelty_score: float         # Combined novelty metric (0-1)
    information_density: float   # Information per character


class HashLearning:
    """
    SHAKE256-based learning and quality scoring.

    Core insight: The entropy characteristics of text reveal its information content.
    High-quality academic text has:
    - High lexical diversity (many unique terms)
    - Moderate repetition (key concepts repeated, but not excessively)
    - Technical vocabulary (domain-specific terms)

    We combine multiple entropy measures for a robust quality signal.
    """

    def __init__(self, hash_length: int = 64):
        """
        Initialize with configurable hash length.

        Args:
            hash_length: SHAKE256 output length in bytes (default 64 = 512 bits)
        """
        self.hash_length = hash_length
        self._seen_hashes: Dict[str, int] = {}  # hash -> count for dedup

    def compute_shake256(self, text: str) -> str:
        """
        Compute SHAKE256 hash of text.

        SHAKE256 is an extendable-output function (XOF) from SHA-3 family.
        Unlike fixed-output hashes, we can request any length output.
        """
        shake = hashlib.shake_256(text.encode('utf-8'))
        return shake.hexdigest(self.hash_length)

    def shannon_entropy(self, data: bytes) -> float:
        """
        Calculate Shannon entropy of byte sequence.

        H = -sum(p(x) * log2(p(x))) for all x in alphabet

        Max entropy for bytes = 8 bits (uniform distribution)
        """
        if not data:
            return 0.0

        counts = Counter(data)
        total = len(data)
        entropy = 0.0

        for count in counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)

        return entropy

    def text_entropy(self, text: str) -> Tuple[float, float]:
        """
        Calculate character-level and word-level entropy.

        Returns:
            (char_entropy, word_entropy)
        """
        if not text:
            return 0.0, 0.0

        # Character-level entropy
        char_counts = Counter(text.lower())
        char_total = len(text)
        char_entropy = 0.0
        for count in char_counts.values():
            if count > 0:
                p = count / char_total
                char_entropy -= p * math.log2(p)

        # Word-level entropy
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return char_entropy, 0.0

        word_counts = Counter(words)
        word_total = len(words)
        word_entropy = 0.0
        for count in word_counts.values():
            if count > 0:
                p = count / word_total
                word_entropy -= p * math.log2(p)

        return char_entropy, word_entropy

    def estimate_compression_ratio(self, text: str) -> float:
        """
        Estimate how compressible the text is (proxy for redundancy).

        Lower ratio = more compressible = more redundant = less novel

        Uses a simple LZ77-style approximation without actual compression.
        """
        if len(text) < 10:
            return 1.0

        # Count unique n-grams as compression proxy
        text_bytes = text.encode('utf-8')
        original_size = len(text_bytes)

        # Simulate compression by counting unique 3-grams
        trigrams = set()
        for i in range(len(text) - 2):
            trigrams.add(text[i:i+3])

        # Ratio of unique trigrams to possible trigrams
        possible_trigrams = len(text) - 2
        if possible_trigrams <= 0:
            return 1.0

        uniqueness = len(trigrams) / possible_trigrams

        # Map to 0-1 range where 1 = highly unique/incompressible
        return min(1.0, uniqueness)

    def vocabulary_richness(self, text: str) -> float:
        """
        Calculate vocabulary richness (type-token ratio with correction).

        Uses Guiraud's index: R = V / sqrt(N)
        where V = vocabulary size, N = total tokens
        """
        words = re.findall(r'\b\w+\b', text.lower())
        if len(words) < 2:
            return 0.0

        vocab_size = len(set(words))
        total_words = len(words)

        # Guiraud's index, normalized to 0-1 range
        guiraud = vocab_size / math.sqrt(total_words)

        # Typical values: 5-15 for academic text
        # Normalize: divide by expected max (~20)
        return min(1.0, guiraud / 20.0)

    def analyze(self, text: str, domain: Optional[str] = None) -> EntropyScore:
        """
        Full entropy analysis of text.

        Args:
            text: The text to analyze
            domain: Optional domain for domain-specific scoring

        Returns:
            EntropyScore with all metrics
        """
        # Compute hash
        text_hash = self.compute_shake256(text)
        hash_bytes = bytes.fromhex(text_hash)

        # Entropy of the hash itself (should be near-maximal ~8 bits for good hash)
        byte_entropy = self.shannon_entropy(hash_bytes)

        # Text entropy
        char_entropy, word_entropy = self.text_entropy(text)

        # Compression ratio
        compression_ratio = self.estimate_compression_ratio(text)

        # Vocabulary richness
        vocab_richness = self.vocabulary_richness(text)

        # Information density (bits per character)
        info_density = char_entropy

        # Combined novelty score
        # Weight different signals
        novelty_score = self._compute_novelty(
            byte_entropy=byte_entropy,
            word_entropy=word_entropy,
            compression_ratio=compression_ratio,
            vocab_richness=vocab_richness,
            text_length=len(text)
        )

        return EntropyScore(
            hash=text_hash,
            byte_entropy=byte_entropy,
            text_entropy=word_entropy,
            compression_ratio=compression_ratio,
            novelty_score=novelty_score,
            information_density=info_density
        )

    def _compute_novelty(
        self,
        byte_entropy: float,
        word_entropy: float,
        compression_ratio: float,
        vocab_richness: float,
        text_length: int
    ) -> float:
        """
        Combine multiple signals into a single novelty score.

        High novelty = unique, information-rich content
        Low novelty = repetitive, common content
        """
        # Length penalty for very short texts
        length_factor = min(1.0, text_length / 500)

        # Normalize word entropy (typical range 5-12 for academic text)
        norm_word_entropy = min(1.0, word_entropy / 12.0)

        # Hash entropy should be near 8 for random-looking output
        hash_quality = byte_entropy / 8.0

        # Weighted combination
        novelty = (
            0.30 * norm_word_entropy +
            0.25 * compression_ratio +
            0.25 * vocab_richness +
            0.10 * hash_quality +
            0.10 * length_factor
        )

        return min(1.0, max(0.0, novelty))

    def is_duplicate(self, text: str, threshold: float = 0.95) -> Tuple[bool, Optional[str]]:
        """
        Check if text is a duplicate of something we've seen.

        Args:
            text: Text to check
            threshold: Similarity threshold (not used for exact match)

        Returns:
            (is_duplicate, matching_hash)
        """
        text_hash = self.compute_shake256(text)

        if text_hash in self._seen_hashes:
            self._seen_hashes[text_hash] += 1
            return True, text_hash

        self._seen_hashes[text_hash] = 1
        return False, None

    def similarity_hash(self, text: str, shingle_size: int = 3) -> str:
        """
        Create a locality-sensitive hash for near-duplicate detection.

        Uses MinHash-style approach with character shingles.
        Similar texts will have similar hashes.
        """
        # Create shingles
        text_lower = text.lower()
        shingles = set()
        for i in range(len(text_lower) - shingle_size + 1):
            shingles.add(text_lower[i:i + shingle_size])

        if not shingles:
            return self.compute_shake256(text)

        # Hash each shingle and take min (MinHash approximation)
        shingle_hashes = []
        for shingle in shingles:
            h = hashlib.shake_256(shingle.encode()).hexdigest(8)
            shingle_hashes.append(h)

        # Sort and take first N for signature
        shingle_hashes.sort()
        signature = ''.join(shingle_hashes[:16])

        return hashlib.shake_256(signature.encode()).hexdigest(self.hash_length)

    def concept_hash(self, concepts: List[str]) -> str:
        """
        Create a hash representing a set of concepts (order-independent).

        Useful for detecting papers about similar concept combinations
        across different phrasings.
        """
        # Normalize and sort concepts
        normalized = sorted(set(c.lower().strip() for c in concepts if c.strip()))

        # Join and hash
        concept_string = '|'.join(normalized)
        return self.compute_shake256(concept_string)

    def quality_score(self, text: str, citations: int = 0, age_years: float = 0) -> float:
        """
        Compute overall quality score combining entropy and metadata.

        Args:
            text: The text content (abstract, claims)
            citations: Number of citations
            age_years: Age of the paper in years

        Returns:
            Quality score 0-1
        """
        # Get entropy analysis
        entropy = self.analyze(text)

        # Citation impact (logarithmic scale)
        citation_score = min(1.0, math.log10(citations + 1) / 4)  # 10000 citations = 1.0

        # Age-adjusted citations (newer papers haven't had time)
        if age_years > 0:
            citations_per_year = citations / age_years
            age_adjusted = min(1.0, math.log10(citations_per_year + 1) / 2)
        else:
            age_adjusted = 0.5  # Neutral for brand new papers

        # Combine entropy novelty with citation impact
        quality = (
            0.50 * entropy.novelty_score +
            0.25 * citation_score +
            0.25 * age_adjusted
        )

        return min(1.0, max(0.0, quality))


# Singleton instance for global use
hash_learner = HashLearning()


# Convenience functions
def compute_entropy(text: str) -> EntropyScore:
    """Compute entropy score for text."""
    return hash_learner.analyze(text)


def compute_hash(text: str) -> str:
    """Compute SHAKE256 hash of text."""
    return hash_learner.compute_shake256(text)


def compute_quality(text: str, citations: int = 0, age_years: float = 0) -> float:
    """Compute quality score."""
    return hash_learner.quality_score(text, citations, age_years)


def is_novel(text: str, threshold: float = 0.7) -> bool:
    """Check if text meets novelty threshold."""
    score = hash_learner.analyze(text)
    return score.novelty_score >= threshold
