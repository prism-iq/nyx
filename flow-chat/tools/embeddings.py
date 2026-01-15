"""
CIPHER Semantic Embeddings Module

Generates vector embeddings for claims to enable:
- Semantic similarity search
- Clustering of related claims
- Cross-domain concept matching
- Near-duplicate detection

Supports multiple backends:
- sentence-transformers (local, default)
- OpenAI API (optional, higher quality)
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result of embedding computation"""
    text: str
    vector: List[float]
    model: str
    dimensions: int


class EmbeddingBackend(ABC):
    """Abstract base class for embedding backends"""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the embedding dimensions"""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name"""
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Embed a single text"""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts efficiently"""
        pass


class SentenceTransformerBackend(EmbeddingBackend):
    """
    Local embedding using sentence-transformers.

    Default model: all-MiniLM-L6-v2 (384 dimensions, fast)
    Alternative: all-mpnet-base-v2 (768 dimensions, better quality)
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None
        self._dimensions = None

    def _load_model(self):
        """Lazy load the model"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading sentence-transformer model: {self._model_name}")
                self._model = SentenceTransformer(self._model_name)
                # Get dimensions from a test embedding
                test_emb = self._model.encode("test", convert_to_numpy=True)
                self._dimensions = len(test_emb)
                logger.info(f"Model loaded. Dimensions: {self._dimensions}")
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )

    @property
    def dimensions(self) -> int:
        self._load_model()
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model_name

    async def embed(self, text: str) -> List[float]:
        """Embed a single text"""
        self._load_model()
        # Run in executor to not block event loop
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self._model.encode(text, convert_to_numpy=True)
        )
        return embedding.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts efficiently"""
        if not texts:
            return []

        self._load_model()
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        )
        return [emb.tolist() for emb in embeddings]


class EmbeddingService:
    """
    Main embedding service for CIPHER.

    Handles:
    - Embedding computation with configurable backend
    - Caching (optional)
    - Similarity computation
    - Batch processing
    """

    def __init__(
        self,
        backend: Optional[EmbeddingBackend] = None,
        cache_enabled: bool = True
    ):
        """
        Initialize the embedding service.

        Args:
            backend: Embedding backend to use (default: SentenceTransformer)
            cache_enabled: Whether to cache embeddings in memory
        """
        self.backend = backend or SentenceTransformerBackend()
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, List[float]] = {}

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions"""
        return self.backend.dimensions

    @property
    def model_name(self) -> str:
        """Get model name"""
        return self.backend.model_name

    def _cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        # Use first 100 chars + length as simple key
        return f"{text[:100]}_{len(text)}"

    async def embed(self, text: str) -> EmbeddingResult:
        """
        Embed a single text.

        Args:
            text: Text to embed

        Returns:
            EmbeddingResult with vector
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return EmbeddingResult(
                text=text,
                vector=[0.0] * self.dimensions,
                model=self.model_name,
                dimensions=self.dimensions
            )

        # Check cache
        if self.cache_enabled:
            cache_key = self._cache_key(text)
            if cache_key in self._cache:
                return EmbeddingResult(
                    text=text,
                    vector=self._cache[cache_key],
                    model=self.model_name,
                    dimensions=self.dimensions
                )

        # Compute embedding
        vector = await self.backend.embed(text)

        # Cache result
        if self.cache_enabled:
            self._cache[cache_key] = vector

        return EmbeddingResult(
            text=text,
            vector=vector,
            model=self.model_name,
            dimensions=self.dimensions
        )

    async def embed_batch(
        self,
        texts: List[str],
        show_progress: bool = False
    ) -> List[EmbeddingResult]:
        """
        Embed multiple texts efficiently.

        Args:
            texts: List of texts to embed
            show_progress: Whether to log progress

        Returns:
            List of EmbeddingResults
        """
        if not texts:
            return []

        # Separate cached and uncached
        results = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            if not text or not text.strip():
                results[i] = EmbeddingResult(
                    text=text,
                    vector=[0.0] * self.dimensions,
                    model=self.model_name,
                    dimensions=self.dimensions
                )
            elif self.cache_enabled:
                cache_key = self._cache_key(text)
                if cache_key in self._cache:
                    results[i] = EmbeddingResult(
                        text=text,
                        vector=self._cache[cache_key],
                        model=self.model_name,
                        dimensions=self.dimensions
                    )
                else:
                    uncached_indices.append(i)
                    uncached_texts.append(text)
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Batch embed uncached texts
        if uncached_texts:
            if show_progress:
                logger.info(f"Embedding {len(uncached_texts)} texts...")

            vectors = await self.backend.embed_batch(uncached_texts)

            for idx, text, vector in zip(uncached_indices, uncached_texts, vectors):
                # Cache
                if self.cache_enabled:
                    self._cache[self._cache_key(text)] = vector

                results[idx] = EmbeddingResult(
                    text=text,
                    vector=vector,
                    model=self.model_name,
                    dimensions=self.dimensions
                )

        return results

    def cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score between -1 and 1
        """
        a = np.array(vec1)
        b = np.array(vec2)

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.dot(a, b) / (norm_a * norm_b))

    def find_similar(
        self,
        query_vector: List[float],
        candidates: List[Tuple[Any, List[float]]],
        top_k: int = 10,
        threshold: float = 0.0
    ) -> List[Tuple[Any, float]]:
        """
        Find most similar vectors to query.

        Args:
            query_vector: Query embedding
            candidates: List of (id, vector) tuples
            top_k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of (id, similarity) tuples, sorted by similarity
        """
        similarities = []

        for item_id, vector in candidates:
            sim = self.cosine_similarity(query_vector, vector)
            if sim >= threshold:
                similarities.append((item_id, sim))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    async def semantic_search(
        self,
        query: str,
        candidates: List[Tuple[Any, str]],
        top_k: int = 10,
        threshold: float = 0.5
    ) -> List[Tuple[Any, float]]:
        """
        Search for semantically similar texts.

        Args:
            query: Query text
            candidates: List of (id, text) tuples
            top_k: Number of results
            threshold: Minimum similarity

        Returns:
            List of (id, similarity) tuples
        """
        # Embed query
        query_result = await self.embed(query)

        # Embed all candidates
        texts = [text for _, text in candidates]
        candidate_results = await self.embed_batch(texts)

        # Build vector list
        candidate_vectors = [
            (candidates[i][0], result.vector)
            for i, result in enumerate(candidate_results)
        ]

        return self.find_similar(
            query_result.vector,
            candidate_vectors,
            top_k=top_k,
            threshold=threshold
        )

    def clear_cache(self):
        """Clear the embedding cache"""
        self._cache.clear()
        logger.info("Embedding cache cleared")


# Singleton instance for global use
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(
    model_name: str = "all-MiniLM-L6-v2"
) -> EmbeddingService:
    """
    Get or create the global embedding service.

    Args:
        model_name: Model to use (only used on first call)

    Returns:
        EmbeddingService instance
    """
    global _embedding_service

    if _embedding_service is None:
        backend = SentenceTransformerBackend(model_name)
        _embedding_service = EmbeddingService(backend)

    return _embedding_service


# Convenience functions
async def embed_text(text: str) -> List[float]:
    """Embed a single text using default service"""
    service = get_embedding_service()
    result = await service.embed(text)
    return result.vector


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed multiple texts using default service"""
    service = get_embedding_service()
    results = await service.embed_batch(texts)
    return [r.vector for r in results]


def compute_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between vectors"""
    service = get_embedding_service()
    return service.cosine_similarity(vec1, vec2)
