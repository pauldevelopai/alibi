"""
RAG System for Newsletter Generation

This creates a proper Retrieval-Augmented Generation system:
1. Embeds all past newsletters into chunks
2. Stores embeddings for fast retrieval
3. Retrieves relevant passages based on topic
4. Uses retrieved passages as examples in generation

This ensures the AI writes in YOUR voice by seeing actual examples
from your past newsletters that are relevant to the current topic.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Tuple
import re

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATA_DIR = Path(__file__).parent / "data"
EMBEDDINGS_FILE = DATA_DIR / "newsletter_embeddings.json"
RAW_DATA_FILE = DATA_DIR / "newsletters_raw.jsonl"

# Embedding model
EMBEDDING_MODEL = "text-embedding-3-small"


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
# Embeddings
# ============================================================================

def get_embedding(text: str) -> List[float]:
    """Get embedding for a piece of text."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text[:8000]  # Limit input size
    )
    return response.data[0].embedding


def compute_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """Compute cosine similarity between two embeddings."""
    dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
    norm1 = sum(a * a for a in embedding1) ** 0.5
    norm2 = sum(b * b for b in embedding2) ** 0.5
    return dot_product / (norm1 * norm2) if norm1 and norm2 else 0


def load_embeddings() -> dict:
    """Load cached embeddings."""
    if not EMBEDDINGS_FILE.exists():
        return {'chunks': [], 'version': 1}
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

def build_embeddings_database(force_rebuild: bool = False) -> dict:
    """
    Build embeddings for all newsletters.
    
    This:
    1. Loads all past newsletters
    2. Chunks them into ~500 word passages
    3. Creates embeddings for each chunk
    4. Saves to disk for fast retrieval
    """
    print("Building newsletter embeddings database...")
    
    # Check if we need to rebuild
    existing = load_embeddings()
    if existing.get('chunks') and not force_rebuild:
        print(f"Using existing database with {len(existing['chunks'])} chunks")
        return existing
    
    if not RAW_DATA_FILE.exists():
        print(f"No newsletters found at {RAW_DATA_FILE}")
        return {'chunks': [], 'version': 1}
    
    # Load all newsletters
    newsletters = []
    with open(RAW_DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                newsletters.append(json.loads(line))
    
    print(f"Processing {len(newsletters)} newsletters...")
    
    all_chunks = []
    
    for i, nl in enumerate(newsletters):
        title = nl.get('title', 'Untitled')
        content = nl.get('content_html', '')
        
        if not content:
            continue
        
        # Chunk the newsletter
        chunks = chunk_newsletter(title, content)
        
        print(f"  [{i+1}/{len(newsletters)}] {title[:50]}... ({len(chunks)} chunks)")
        
        for j, chunk in enumerate(chunks):
            # Create embedding
            try:
                embedding = get_embedding(f"Newsletter: {title}\n\n{chunk['text']}")
                
                all_chunks.append({
                    'id': f"{i}_{j}",
                    'newsletter_title': title,
                    'text': chunk['text'],
                    'word_count': chunk['word_count'],
                    'embedding': embedding,
                })
            except Exception as e:
                print(f"    Error embedding chunk {j}: {e}")
    
    print(f"\nCreated {len(all_chunks)} total chunks")
    
    # Save
    data = {
        'chunks': all_chunks,
        'version': 1,
        'total_newsletters': len(newsletters),
    }
    save_embeddings(data)
    
    print(f"Saved to {EMBEDDINGS_FILE}")
    
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
    
    # Calculate similarities
    results = []
    for chunk in data['chunks']:
        similarity = compute_similarity(query_embedding, chunk['embedding'])
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


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("RAG SYSTEM FOR NEWSLETTERS")
    print("=" * 60)
    
    # Build database
    data = build_embeddings_database()
    
    print(f"\nDatabase has {len(data.get('chunks', []))} chunks")
    
    # Test retrieval
    test_query = "AI tools for African journalists"
    print(f"\nTest query: '{test_query}'")
    print("-" * 40)
    
    passages = retrieve_relevant_passages(test_query, top_k=3)
    
    for i, p in enumerate(passages, 1):
        print(f"\n{i}. From: {p['title']}")
        print(f"   Similarity: {p['similarity']:.2%}")
        print(f"   Preview: {p['text'][:200]}...")
    
    print("\n" + "=" * 60)









