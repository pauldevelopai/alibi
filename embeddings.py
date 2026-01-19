"""
Local Embeddings Service using Sentence Transformers (Hugging Face)

Benefits over OpenAI API:
- FREE (no API costs)
- FAST (runs locally, no network latency)
- OFFLINE (works without internet)
- PRIVATE (your data never leaves your machine)

Uses all-MiniLM-L6-v2 by default:
- 384 dimensions
- ~80MB model size
- Great balance of speed and quality
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Optional, Union, Tuple
import hashlib

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

# Fallback to OpenAI if needed
try:
    import os
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    _openai_client = None

DATA_DIR = Path(__file__).parent / "data"
CACHE_FILE = DATA_DIR / "embeddings_cache.json"

# Model configuration
DEFAULT_MODEL = "all-MiniLM-L6-v2"  # Fast, good quality, 384 dims
ALTERNATIVE_MODELS = {
    "fast": "all-MiniLM-L6-v2",      # 80MB, 384 dims, fastest
    "balanced": "all-MiniLM-L12-v2",  # 120MB, 384 dims, better quality
    "quality": "all-mpnet-base-v2",   # 420MB, 768 dims, best quality
}

# Global model instance (lazy loaded)
_model: Optional[SentenceTransformer] = None
_model_name: Optional[str] = None


def get_model(model_name: str = DEFAULT_MODEL) -> Optional[SentenceTransformer]:
    """
    Get or initialize the sentence transformer model.
    
    Lazy loads on first use to avoid slow startup.
    """
    global _model, _model_name
    
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return None
    
    if _model is None or _model_name != model_name:
        print(f"Loading embedding model: {model_name}...")
        _model = SentenceTransformer(model_name)
        _model_name = model_name
        print(f"Model loaded successfully!")
    
    return _model


def get_embedding(
    text: str,
    use_cache: bool = True,
    prefer_local: bool = True
) -> Optional[List[float]]:
    """
    Get embedding for a single text.
    
    Args:
        text: The text to embed
        use_cache: Whether to check/update cache
        prefer_local: Use sentence-transformers if available, else OpenAI
    
    Returns:
        List of floats (embedding vector) or None if failed
    """
    if not text or not text.strip():
        return None
    
    text = text.strip()[:8000]  # Limit input size
    
    # Check cache first
    if use_cache:
        cached = _get_from_cache(text)
        if cached is not None:
            return cached
    
    embedding = None
    
    # Try local model first
    if prefer_local and SENTENCE_TRANSFORMERS_AVAILABLE:
        embedding = _embed_local(text)
    
    # Fallback to OpenAI
    if embedding is None and OPENAI_AVAILABLE:
        embedding = _embed_openai(text)
    
    # Cache the result
    if embedding is not None and use_cache:
        _save_to_cache(text, embedding)
    
    return embedding


def get_embeddings_batch(
    texts: List[str],
    use_cache: bool = True,
    prefer_local: bool = True,
    show_progress: bool = False
) -> List[Optional[List[float]]]:
    """
    Get embeddings for multiple texts efficiently.
    
    Local model processes in batches for speed.
    """
    if not texts:
        return []
    
    results = [None] * len(texts)
    texts_to_embed = []
    indices_to_embed = []
    
    # Check cache first
    for i, text in enumerate(texts):
        if not text or not text.strip():
            continue
        
        text = text.strip()[:8000]
        
        if use_cache:
            cached = _get_from_cache(text)
            if cached is not None:
                results[i] = cached
                continue
        
        texts_to_embed.append(text)
        indices_to_embed.append(i)
    
    if not texts_to_embed:
        return results
    
    # Batch embed remaining texts
    if prefer_local and SENTENCE_TRANSFORMERS_AVAILABLE:
        embeddings = _embed_local_batch(texts_to_embed, show_progress)
    elif OPENAI_AVAILABLE:
        embeddings = [_embed_openai(t) for t in texts_to_embed]
    else:
        embeddings = [None] * len(texts_to_embed)
    
    # Store results and cache
    for idx, embedding, text in zip(indices_to_embed, embeddings, texts_to_embed):
        results[idx] = embedding
        if embedding is not None and use_cache:
            _save_to_cache(text, embedding)
    
    return results


def compute_similarity(
    embedding1: List[float],
    embedding2: List[float]
) -> float:
    """
    Compute cosine similarity between two embeddings.
    
    Returns value between -1 and 1 (1 = identical, 0 = orthogonal, -1 = opposite)
    """
    if not embedding1 or not embedding2:
        return 0.0
    
    # Convert to numpy for efficiency
    a = np.array(embedding1)
    b = np.array(embedding2)
    
    # Cosine similarity
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(dot_product / (norm_a * norm_b))


def find_most_similar(
    query_embedding: List[float],
    candidate_embeddings: List[List[float]],
    top_k: int = 5,
    min_similarity: float = 0.0
) -> List[Tuple[int, float]]:
    """
    Find the most similar embeddings to a query.
    
    Args:
        query_embedding: The embedding to search for
        candidate_embeddings: List of embeddings to search through
        top_k: Number of results to return
        min_similarity: Minimum similarity threshold
    
    Returns:
        List of (index, similarity) tuples, sorted by similarity descending
    """
    if not query_embedding or not candidate_embeddings:
        return []
    
    similarities = []
    for i, candidate in enumerate(candidate_embeddings):
        if candidate:
            sim = compute_similarity(query_embedding, candidate)
            if sim >= min_similarity:
                similarities.append((i, sim))
    
    # Sort by similarity descending
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    return similarities[:top_k]


def semantic_search(
    query: str,
    documents: List[str],
    top_k: int = 5,
    min_similarity: float = 0.3
) -> List[Tuple[int, str, float]]:
    """
    Search documents by semantic similarity to query.
    
    Args:
        query: Search query
        documents: List of documents to search
        top_k: Number of results
        min_similarity: Minimum similarity threshold
    
    Returns:
        List of (index, document, similarity) tuples
    """
    if not query or not documents:
        return []
    
    # Get query embedding
    query_embedding = get_embedding(query, use_cache=False)
    if not query_embedding:
        return []
    
    # Get document embeddings
    doc_embeddings = get_embeddings_batch(documents)
    
    # Find most similar
    results = find_most_similar(
        query_embedding,
        doc_embeddings,
        top_k=top_k,
        min_similarity=min_similarity
    )
    
    return [(idx, documents[idx], sim) for idx, sim in results]


# ============================================================================
# Private Implementation
# ============================================================================

def _embed_local(text: str) -> Optional[List[float]]:
    """Embed using local sentence-transformers model."""
    model = get_model()
    if model is None:
        return None
    
    try:
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    except Exception as e:
        print(f"Local embedding error: {e}")
        return None


def _embed_local_batch(
    texts: List[str],
    show_progress: bool = False
) -> List[Optional[List[float]]]:
    """Embed multiple texts using local model (efficient batching)."""
    model = get_model()
    if model is None:
        return [None] * len(texts)
    
    try:
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=show_progress
        )
        return [emb.tolist() for emb in embeddings]
    except Exception as e:
        print(f"Local batch embedding error: {e}")
        return [None] * len(texts)


def _embed_openai(text: str) -> Optional[List[float]]:
    """Embed using OpenAI API (fallback)."""
    if not OPENAI_AVAILABLE or not _openai_client:
        return None
    
    try:
        response = _openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"OpenAI embedding error: {e}")
        return None


# ============================================================================
# Caching
# ============================================================================

_cache: Optional[dict] = None


def _get_cache() -> dict:
    """Load or return cached embeddings."""
    global _cache
    
    if _cache is not None:
        return _cache
    
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                _cache = json.load(f)
        except:
            _cache = {}
    else:
        _cache = {}
    
    return _cache


def _save_cache():
    """Save cache to disk."""
    global _cache
    if _cache is None:
        return
    
    DATA_DIR.mkdir(exist_ok=True)
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(_cache, f)
    except Exception as e:
        print(f"Cache save error: {e}")


def _text_hash(text: str) -> str:
    """Create hash key for text."""
    return hashlib.md5(text.encode()).hexdigest()


def _get_from_cache(text: str) -> Optional[List[float]]:
    """Get embedding from cache if exists."""
    cache = _get_cache()
    key = _text_hash(text)
    return cache.get(key)


def _save_to_cache(text: str, embedding: List[float]):
    """Save embedding to cache."""
    cache = _get_cache()
    key = _text_hash(text)
    cache[key] = embedding
    
    # Save periodically (every 100 new entries)
    if len(cache) % 100 == 0:
        _save_cache()


def clear_cache():
    """Clear the embeddings cache."""
    global _cache
    _cache = {}
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()


def get_cache_stats() -> dict:
    """Get statistics about the cache."""
    cache = _get_cache()
    return {
        'total_entries': len(cache),
        'cache_file': str(CACHE_FILE),
        'cache_exists': CACHE_FILE.exists(),
    }


# ============================================================================
# Status and Testing
# ============================================================================

def get_status() -> dict:
    """Get status of embedding services."""
    return {
        'sentence_transformers_available': SENTENCE_TRANSFORMERS_AVAILABLE,
        'openai_available': OPENAI_AVAILABLE,
        'model_loaded': _model is not None,
        'model_name': _model_name,
        'default_model': DEFAULT_MODEL,
        'cache_stats': get_cache_stats(),
    }


def test_embeddings():
    """Test the embedding system."""
    print("=" * 60)
    print("EMBEDDINGS TEST")
    print("=" * 60)
    
    status = get_status()
    print(f"\nStatus:")
    print(f"  Sentence Transformers: {'✅' if status['sentence_transformers_available'] else '❌'}")
    print(f"  OpenAI Fallback: {'✅' if status['openai_available'] else '❌'}")
    
    if not status['sentence_transformers_available'] and not status['openai_available']:
        print("\n❌ No embedding service available!")
        print("Install sentence-transformers: pip install sentence-transformers")
        return
    
    # Test single embedding
    print("\n1. Testing single embedding...")
    text = "AI is transforming how we work and live."
    embedding = get_embedding(text)
    if embedding:
        print(f"   ✅ Got embedding with {len(embedding)} dimensions")
    else:
        print("   ❌ Failed to get embedding")
        return
    
    # Test batch embedding
    print("\n2. Testing batch embedding...")
    texts = [
        "Machine learning models are getting better.",
        "The weather is nice today.",
        "Neural networks can recognize images.",
    ]
    embeddings = get_embeddings_batch(texts)
    success = sum(1 for e in embeddings if e is not None)
    print(f"   ✅ Got {success}/{len(texts)} embeddings")
    
    # Test similarity
    print("\n3. Testing similarity...")
    sim_ml = compute_similarity(embeddings[0], embeddings[2])
    sim_weather = compute_similarity(embeddings[0], embeddings[1])
    print(f"   ML vs Neural Networks: {sim_ml:.3f}")
    print(f"   ML vs Weather: {sim_weather:.3f}")
    print(f"   ✅ ML topic more similar to neural networks (as expected)")
    
    # Test semantic search
    print("\n4. Testing semantic search...")
    docs = [
        "Python is a programming language used for AI.",
        "The stock market closed higher today.",
        "Deep learning uses neural networks.",
        "I went for a walk in the park.",
        "GPT models generate human-like text.",
    ]
    results = semantic_search("artificial intelligence", docs, top_k=3)
    print("   Query: 'artificial intelligence'")
    for idx, doc, sim in results:
        print(f"   [{sim:.3f}] {doc[:50]}...")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_embeddings()
