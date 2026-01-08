"""
RAG System for Newsletter Generation

This creates a proper Retrieval-Augmented Generation system:
1. Embeds all past newsletters into chunks
2. Stores embeddings for fast retrieval
3. Retrieves relevant passages based on topic
4. Uses retrieved passages as examples in generation

This ensures the AI writes in YOUR voice by seeing actual examples
from your past newsletters that are relevant to the current topic.

NOW USING LOCAL EMBEDDINGS (sentence-transformers):
- FREE (no API costs for embeddings)
- FAST (runs locally, no network latency)
- OFFLINE (works without internet)
- Falls back to OpenAI if sentence-transformers not installed
"""

import json
from pathlib import Path
from typing import List, Tuple, Optional

# Use our new local embeddings module
try:
    from embeddings import (
        get_embedding,
        get_embeddings_batch,
        compute_similarity,
        find_most_similar,
        get_status as get_embeddings_status,
        SENTENCE_TRANSFORMERS_AVAILABLE,
        OPENAI_AVAILABLE,
    )
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    OPENAI_AVAILABLE = False

# Fallback to old OpenAI-only method if embeddings module not available
if not EMBEDDINGS_AVAILABLE:
    import os
    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv()
    _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def get_embedding(text: str) -> List[float]:
        """Fallback: Get embedding using OpenAI API."""
        response = _client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000]
        )
        return response.data[0].embedding
    
    def compute_similarity(embedding1: List[float], embedding2: List[float]) -> float:
        """Fallback: Compute cosine similarity."""
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5
        return dot_product / (norm1 * norm2) if norm1 and norm2 else 0


DATA_DIR = Path(__file__).parent / "data"
EMBEDDINGS_FILE = DATA_DIR / "newsletter_embeddings.json"
RAW_DATA_FILE = DATA_DIR / "newsletters_raw.jsonl"


# ============================================================================
# Text Processing
# ============================================================================

def clean_html(html: str) -> str:
    """Remove HTML tags and clean text."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'lxml')
    
    # Remove script and style elements
    for element in soup(['script', 'style', 'nav', 'footer']):
        element.decompose()
    
    text = soup.get_text(separator='\n', strip=True)
    
    # Clean up whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)


def chunk_newsletter(title: str, content: str, chunk_size: int = 500) -> List[dict]:
    """
    Split a newsletter into meaningful chunks for embedding.
    
    Each chunk includes:
    - The newsletter title for context
    - A passage of ~500 words
    - Overlap with adjacent chunks
    """
    chunks = []
    
    # Clean the content
    text = clean_html(content) if '<' in content else content
    
    # Split into paragraphs
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    
    current_chunk = []
    current_words = 0
    
    for para in paragraphs:
        para_words = len(para.split())
        
        if current_words + para_words > chunk_size and current_chunk:
            # Save current chunk
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append({
                'title': title,
                'text': chunk_text,
                'word_count': current_words,
            })
            
            # Start new chunk with overlap (keep last paragraph)
            current_chunk = [current_chunk[-1]] if current_chunk else []
            current_words = len(current_chunk[0].split()) if current_chunk else 0
        
        current_chunk.append(para)
        current_words += para_words
    
    # Don't forget the last chunk
    if current_chunk:
        chunk_text = '\n\n'.join(current_chunk)
        chunks.append({
            'title': title,
            'text': chunk_text,
            'word_count': current_words,
        })
    
    return chunks


# ============================================================================
# Embeddings Storage
# ============================================================================

def load_embeddings() -> dict:
    """Load cached embeddings."""
    if not EMBEDDINGS_FILE.exists():
        return {'chunks': [], 'version': 2, 'embedding_source': 'none'}
    with open(EMBEDDINGS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_embeddings(data: dict):
    """Save embeddings to cache."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(EMBEDDINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


# ============================================================================
# Build Embeddings Database
# ============================================================================

def build_embeddings_database(
    force_rebuild: bool = False,
    prefer_local: bool = True,
    show_progress: bool = True
) -> dict:
    """
    Build embeddings for all newsletters.
    
    This:
    1. Loads all past newsletters
    2. Chunks them into ~500 word passages
    3. Creates embeddings for each chunk (LOCAL by default!)
    4. Saves to disk for fast retrieval
    
    Args:
        force_rebuild: Rebuild even if database exists
        prefer_local: Use sentence-transformers (free) over OpenAI
        show_progress: Show progress bar during embedding
    """
    print("=" * 60)
    print("BUILDING NEWSLETTER EMBEDDINGS DATABASE")
    print("=" * 60)
    
    # Show which embedding service we're using
    if EMBEDDINGS_AVAILABLE:
        status = get_embeddings_status()
        if prefer_local and status['sentence_transformers_available']:
            print(f"✅ Using LOCAL embeddings (sentence-transformers)")
            print(f"   Model: {status.get('default_model', 'all-MiniLM-L6-v2')}")
            print(f"   Cost: FREE")
        elif status['openai_available']:
            print(f"⚠️  Using OpenAI embeddings (API costs apply)")
        else:
            print("❌ No embedding service available!")
            return {'chunks': [], 'version': 2, 'error': 'No embedding service'}
    else:
        print("⚠️  Using OpenAI embeddings (fallback mode)")
    
    print()
    
    # Check if we need to rebuild
    existing = load_embeddings()
    if existing.get('chunks') and not force_rebuild:
        print(f"📦 Using existing database with {len(existing['chunks'])} chunks")
        print(f"   (use force_rebuild=True to regenerate)")
        return existing
    
    if not RAW_DATA_FILE.exists():
        print(f"❌ No newsletters found at {RAW_DATA_FILE}")
        return {'chunks': [], 'version': 2}
    
    # Load all newsletters
    newsletters = []
    with open(RAW_DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                newsletters.append(json.loads(line))
    
    print(f"📰 Processing {len(newsletters)} newsletters...")
    print()
    
    # Collect all chunks first
    all_chunk_data = []
    
    for i, nl in enumerate(newsletters):
        title = nl.get('title', 'Untitled')
        content = nl.get('content_html', '')
        
        if not content:
            continue
        
        # Chunk the newsletter
        chunks = chunk_newsletter(title, content)
        
        for j, chunk in enumerate(chunks):
            all_chunk_data.append({
                'id': f"{i}_{j}",
                'newsletter_idx': i,
                'newsletter_title': title,
                'text': chunk['text'],
                'word_count': chunk['word_count'],
                'embed_text': f"Newsletter: {title}\n\n{chunk['text']}"
            })
    
    print(f"📝 Created {len(all_chunk_data)} chunks from {len(newsletters)} newsletters")
    print()
    
    # Batch embed all chunks (much faster with local model!)
    if EMBEDDINGS_AVAILABLE:
        print("🔄 Embedding chunks...")
        texts_to_embed = [c['embed_text'] for c in all_chunk_data]
        embeddings = get_embeddings_batch(
            texts_to_embed,
            use_cache=True,
            prefer_local=prefer_local
        )
        
        # Add embeddings to chunks
        all_chunks = []
        success_count = 0
        for chunk_data, embedding in zip(all_chunk_data, embeddings):
            if embedding is not None:
                all_chunks.append({
                    'id': chunk_data['id'],
                    'newsletter_title': chunk_data['newsletter_title'],
                    'text': chunk_data['text'],
                    'word_count': chunk_data['word_count'],
                    'embedding': embedding,
                })
                success_count += 1
        
        print(f"✅ Successfully embedded {success_count}/{len(all_chunk_data)} chunks")
    else:
        # Fallback: embed one at a time with OpenAI
        all_chunks = []
        for i, chunk_data in enumerate(all_chunk_data):
            if i % 10 == 0:
                print(f"   Embedding chunk {i+1}/{len(all_chunk_data)}...")
            try:
                embedding = get_embedding(chunk_data['embed_text'])
                all_chunks.append({
                    'id': chunk_data['id'],
                    'newsletter_title': chunk_data['newsletter_title'],
                    'text': chunk_data['text'],
                    'word_count': chunk_data['word_count'],
                    'embedding': embedding,
                })
            except Exception as e:
                print(f"   Error embedding chunk {i}: {e}")
    
    print()
    
    # Determine embedding source
    embedding_source = 'unknown'
    if EMBEDDINGS_AVAILABLE:
        status = get_embeddings_status()
        if prefer_local and status['sentence_transformers_available']:
            embedding_source = 'sentence-transformers'
        elif status['openai_available']:
            embedding_source = 'openai'
    else:
        embedding_source = 'openai-fallback'
    
    # Save
    data = {
        'chunks': all_chunks,
        'version': 2,
        'total_newsletters': len(newsletters),
        'total_chunks': len(all_chunks),
        'embedding_source': embedding_source,
    }
    save_embeddings(data)
    
    print(f"💾 Saved {len(all_chunks)} chunks to {EMBEDDINGS_FILE}")
    print("=" * 60)
    
    return data


# ============================================================================
# Retrieval
# ============================================================================

def retrieve_relevant_passages(
    query: str,
    top_k: int = 5,
    min_similarity: float = 0.3
) -> List[dict]:
    """
    Retrieve the most relevant passages from past newsletters.
    
    Args:
        query: The topic/idea to find relevant passages for
        top_k: Number of passages to retrieve
        min_similarity: Minimum similarity threshold
    
    Returns:
        List of relevant passages with similarity scores
    """
    data = load_embeddings()
    
    if not data.get('chunks'):
        print("No embeddings found. Run build_embeddings_database() first.")
        return []
    
    # Get query embedding
    query_embedding = get_embedding(query)
    if query_embedding is None:
        print("Failed to get query embedding")
        return []
    
    # Calculate similarities
    results = []
    for chunk in data['chunks']:
        chunk_embedding = chunk.get('embedding')
        if chunk_embedding:
            similarity = compute_similarity(query_embedding, chunk_embedding)
            if similarity >= min_similarity:
                results.append({
                    'title': chunk['newsletter_title'],
                    'text': chunk['text'],
                    'similarity': similarity,
                })
    
    # Sort by similarity
    results.sort(key=lambda x: x['similarity'], reverse=True)
    
    return results[:top_k]


def get_writing_examples(topic: str, num_examples: int = 5) -> str:
    """
    Get relevant writing examples from past newsletters.
    
    Returns formatted text to include in the generation prompt.
    """
    passages = retrieve_relevant_passages(topic, top_k=num_examples)
    
    if not passages:
        return ""
    
    examples = "# RELEVANT PASSAGES FROM YOUR PAST NEWSLETTERS\n\n"
    examples += "These are REAL examples of how you've written about similar topics.\n"
    examples += "Match this style, tone, and approach EXACTLY.\n\n"
    
    for i, passage in enumerate(passages, 1):
        examples += f"---\n"
        examples += f"## From: \"{passage['title']}\"\n"
        examples += f"(Relevance: {passage['similarity']:.0%})\n\n"
        examples += f"{passage['text']}\n\n"
    
    examples += "---\n\n"
    examples += "WRITE LIKE THESE EXAMPLES. Same voice. Same style. Same approach.\n"
    
    return examples


def get_rag_status() -> dict:
    """Get status of the RAG system."""
    data = load_embeddings()
    
    status = {
        'embeddings_available': EMBEDDINGS_AVAILABLE,
        'sentence_transformers': SENTENCE_TRANSFORMERS_AVAILABLE if EMBEDDINGS_AVAILABLE else False,
        'openai_available': OPENAI_AVAILABLE if EMBEDDINGS_AVAILABLE else True,
        'total_chunks': len(data.get('chunks', [])),
        'total_newsletters': data.get('total_newsletters', 0),
        'embedding_source': data.get('embedding_source', 'unknown'),
        'version': data.get('version', 1),
    }
    
    if EMBEDDINGS_AVAILABLE:
        emb_status = get_embeddings_status()
        status['model_loaded'] = emb_status.get('model_loaded', False)
        status['model_name'] = emb_status.get('model_name')
    
    return status


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("RAG SYSTEM FOR NEWSLETTERS")
    print("=" * 60)
    
    # Show status
    status = get_rag_status()
    print("\n📊 Status:")
    print(f"   Sentence Transformers: {'✅' if status.get('sentence_transformers') else '❌'}")
    print(f"   OpenAI Fallback: {'✅' if status.get('openai_available') else '❌'}")
    print(f"   Current DB: {status['total_chunks']} chunks from {status['total_newsletters']} newsletters")
    print(f"   Embedding Source: {status['embedding_source']}")
    
    # Build database
    print("\n")
    data = build_embeddings_database()
    
    print(f"\n📦 Database has {len(data.get('chunks', []))} chunks")
    
    # Test retrieval
    test_query = "AI tools for African journalists"
    print(f"\n🔍 Test query: '{test_query}'")
    print("-" * 40)
    
    passages = retrieve_relevant_passages(test_query, top_k=3)
    
    for i, p in enumerate(passages, 1):
        print(f"\n{i}. From: {p['title']}")
        print(f"   Similarity: {p['similarity']:.2%}")
        print(f"   Preview: {p['text'][:200]}...")
    
    print("\n" + "=" * 60)
