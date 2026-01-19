"""
Deep Style Analyzer - Extract comprehensive stylistic fingerprint from writing

Uses multiple NLP libraries to create a detailed writing style profile:
- Vocabulary patterns
- Sentence structure
- Paragraph flow
- Punctuation habits
- Semantic patterns
- Readability metrics

This creates a much deeper Newsletter Bible that can better guide AI generation.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import Counter
from datetime import datetime

# Try to import NLP libraries
try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False
    print("textstat not available - install with: pip install textstat")

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
    except OSError:
        SPACY_AVAILABLE = False
        print("spaCy model not available - install with: python -m spacy download en_core_web_sm")
except ImportError:
    SPACY_AVAILABLE = False
    print("spaCy not available - install with: pip install spacy")

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    print("TextBlob not available - install with: pip install textblob")

# Use shared embeddings module for sentence-transformers
try:
    from embeddings import (
        get_embedding,
        get_embeddings_batch,
        compute_similarity,
        semantic_search,
        SENTENCE_TRANSFORMERS_AVAILABLE,
    )
except ImportError:
    # Fallback: try direct import
    try:
        from sentence_transformers import SentenceTransformer
        SENTENCE_TRANSFORMERS_AVAILABLE = True
    except ImportError:
        SENTENCE_TRANSFORMERS_AVAILABLE = False
        print("sentence-transformers not available - install with: pip install sentence-transformers")


DATA_DIR = Path(__file__).parent / "data"
DEEP_BIBLE_FILE = DATA_DIR / "newsletter_bible_deep.json"
CUSTOM_WRITING_FILE = DATA_DIR / "custom_writing_samples.json"


# ============================================================================
# Semantic Analysis (using sentence-transformers)
# ============================================================================

def analyze_semantic_patterns(texts: List[str]) -> Dict:
    """
    Analyze semantic patterns using sentence-transformers embeddings.
    
    This provides:
    - Topic consistency analysis
    - Semantic diversity measurement
    - Writing style clustering
    - Similar passage detection
    """
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return {'error': 'sentence-transformers not available'}
    
    try:
        from embeddings import get_embeddings_batch, compute_similarity
    except ImportError:
        return {'error': 'embeddings module not available'}
    
    import numpy as np
    
    # Extract representative sentences from each text
    all_sentences = []
    sentence_sources = []
    
    for text_idx, text in enumerate(texts):
        # Split into sentences and take key ones
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30 and len(s.strip()) < 500]
        
        # Take first 5 sentences (often most representative)
        for sent in sentences[:5]:
            all_sentences.append(sent)
            sentence_sources.append(text_idx)
    
    if len(all_sentences) < 10:
        return {'error': 'Not enough sentences for semantic analysis'}
    
    print(f"   Embedding {len(all_sentences)} representative sentences...")
    
    # Get embeddings for all sentences
    embeddings = get_embeddings_batch(all_sentences, use_cache=True, prefer_local=True)
    
    # Filter out None embeddings
    valid_pairs = [(sent, emb, src) for sent, emb, src in zip(all_sentences, embeddings, sentence_sources) if emb is not None]
    
    if len(valid_pairs) < 10:
        return {'error': 'Failed to embed enough sentences'}
    
    sentences, embeddings, sources = zip(*valid_pairs)
    embeddings = list(embeddings)
    
    # Calculate average embedding (centroid) - represents "typical" writing
    centroid = np.mean([np.array(e) for e in embeddings], axis=0).tolist()
    
    # Calculate semantic consistency (how similar sentences are to the centroid)
    similarities_to_centroid = [compute_similarity(e, centroid) for e in embeddings]
    avg_consistency = np.mean(similarities_to_centroid)
    std_consistency = np.std(similarities_to_centroid)
    
    # Calculate semantic diversity (average pairwise distance)
    # Sample to avoid O(n^2) for large datasets
    sample_size = min(100, len(embeddings))
    sample_indices = np.random.choice(len(embeddings), sample_size, replace=False) if len(embeddings) > sample_size else range(len(embeddings))
    
    pairwise_similarities = []
    for i in sample_indices:
        for j in sample_indices:
            if i < j:
                sim = compute_similarity(embeddings[i], embeddings[j])
                pairwise_similarities.append(sim)
    
    avg_pairwise_similarity = np.mean(pairwise_similarities) if pairwise_similarities else 0
    semantic_diversity = 1 - avg_pairwise_similarity  # Higher = more diverse topics
    
    # Find most "on-brand" sentences (closest to centroid)
    sentence_scores = list(zip(sentences, similarities_to_centroid))
    sentence_scores.sort(key=lambda x: x[1], reverse=True)
    most_representative = [s for s, _ in sentence_scores[:5]]
    
    # Find outlier sentences (furthest from centroid)
    outliers = [s for s, _ in sentence_scores[-3:]]
    
    # Topic cluster analysis (simplified)
    # Group similar sentences together
    clusters = []
    used = set()
    
    for i, emb in enumerate(embeddings):
        if i in used:
            continue
        
        cluster = [sentences[i]]
        used.add(i)
        
        for j, emb2 in enumerate(embeddings):
            if j not in used and compute_similarity(emb, emb2) > 0.7:
                cluster.append(sentences[j])
                used.add(j)
                if len(cluster) >= 5:
                    break
        
        if len(cluster) >= 2:
            clusters.append(cluster[:3])  # Keep top 3 from each cluster
        
        if len(clusters) >= 5:
            break
    
    return {
        'total_sentences_analyzed': len(sentences),
        'semantic_consistency': round(float(avg_consistency), 4),
        'consistency_interpretation': (
            'Very consistent voice' if avg_consistency > 0.7 else
            'Consistent voice' if avg_consistency > 0.5 else
            'Varied voice' if avg_consistency > 0.3 else
            'Highly varied voice'
        ),
        'semantic_diversity': round(float(semantic_diversity), 4),
        'diversity_interpretation': (
            'Very focused (few topics)' if semantic_diversity < 0.3 else
            'Focused' if semantic_diversity < 0.5 else
            'Diverse topics' if semantic_diversity < 0.7 else
            'Highly diverse topics'
        ),
        'most_representative_sentences': most_representative,
        'outlier_sentences': outliers,
        'topic_clusters': clusters,
        'embedding_dimension': len(embeddings[0]) if embeddings else 0,
    }


def load_custom_writing_samples() -> List[str]:
    """Load custom writing samples added by the user."""
    if not CUSTOM_WRITING_FILE.exists():
        return []
    try:
        with open(CUSTOM_WRITING_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('samples', [])
    except:
        return []


def save_custom_writing_sample(text: str, source: str = "manual") -> bool:
    """Save a custom writing sample for analysis."""
    if not text or len(text.strip()) < 100:
        return False
    
    DATA_DIR.mkdir(exist_ok=True)
    
    # Load existing samples
    samples_data = {'samples': [], 'meta': {'count': 0}}
    if CUSTOM_WRITING_FILE.exists():
        try:
            with open(CUSTOM_WRITING_FILE, 'r', encoding='utf-8') as f:
                samples_data = json.load(f)
        except:
            pass
    
    # Add new sample
    samples_data['samples'].append({
        'text': text.strip(),
        'source': source,
        'added_at': datetime.now().isoformat(),
        'char_count': len(text.strip())
    })
    samples_data['meta'] = {
        'count': len(samples_data['samples']),
        'last_updated': datetime.now().isoformat()
    }
    
    with open(CUSTOM_WRITING_FILE, 'w', encoding='utf-8') as f:
        json.dump(samples_data, f, indent=2, ensure_ascii=False)
    
    return True


def clear_custom_writing_samples() -> bool:
    """Clear all custom writing samples."""
    if CUSTOM_WRITING_FILE.exists():
        CUSTOM_WRITING_FILE.unlink()
    return True


def merge_deep_into_bible() -> Dict:
    """Merge deep style analysis insights into the main Newsletter Bible."""
    from style_analyzer import load_bible
    
    deep = load_deep_bible()
    bible = load_bible()
    
    if not deep or not bible:
        return {'error': 'Missing deep analysis or Bible'}
    
    # Add deep analysis section to Bible
    bible['deep_analysis'] = {
        'vocabulary': deep.get('vocabulary', {}),
        'sentences': deep.get('sentences', {}),
        'paragraphs': deep.get('paragraphs', {}),
        'punctuation': deep.get('punctuation', {}),
        'personal_voice': deep.get('personal_voice', {}),
        'signature_patterns': deep.get('signature_patterns', {}),
        'readability': deep.get('readability', {}),
        'sentiment': deep.get('sentiment', {}),
        'linguistics': deep.get('linguistics', {}),
        'meta': deep.get('meta', {})
    }
    
    # Also update the writing_voice section with key insights
    if 'writing_voice' not in bible:
        bible['writing_voice'] = {}
    
    # Add signature words to writing voice
    vocab = deep.get('vocabulary', {})
    if vocab.get('signature_words'):
        bible['writing_voice']['signature_words'] = vocab['signature_words']
    
    # Add sentence style info
    sent = deep.get('sentences', {})
    if sent:
        bible['writing_voice']['sentence_style'] = {
            'avg_length': sent.get('average_sentence_length', 0),
            'short_sentence_pct': sent.get('short_sentence_frequency', 0),
            'long_sentence_pct': sent.get('long_sentence_frequency', 0),
        }
    
    # Add personal voice stats
    voice = deep.get('personal_voice', {})
    if voice:
        bible['writing_voice']['personal_voice_stats'] = {
            'first_person_pct': voice.get('first_person_singular_frequency', 0),
            'second_person_pct': voice.get('second_person_frequency', 0),
            'common_i_patterns': list(voice.get('common_i_statements', {}).keys())[:10]
        }
    
    # Save updated Bible
    bible_path = DATA_DIR / "newsletter_bible.json"
    with open(bible_path, 'w', encoding='utf-8') as f:
        json.dump(bible, f, indent=2, ensure_ascii=False)
    
    return {'success': True, 'sections_added': list(bible.get('deep_analysis', {}).keys())}


def analyze_vocabulary(texts: List[str]) -> Dict:
    """Analyze vocabulary patterns across all texts."""
    
    all_words = []
    all_unique_words = set()
    word_lengths = []
    
    for text in texts:
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        all_words.extend(words)
        all_unique_words.update(words)
        word_lengths.extend([len(w) for w in words])
    
    # Calculate metrics
    total_words = len(all_words)
    unique_words = len(all_unique_words)
    
    # Type-Token Ratio (vocabulary richness)
    ttr = unique_words / total_words if total_words > 0 else 0
    
    # Hapax Legomena (words used only once)
    word_counts = Counter(all_words)
    hapax = [w for w, c in word_counts.items() if c == 1]
    hapax_ratio = len(hapax) / total_words if total_words > 0 else 0
    
    # Most frequent words (excluding common stop words)
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                  'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
                  'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
                  'into', 'through', 'during', 'before', 'after', 'above', 'below',
                  'between', 'under', 'again', 'further', 'then', 'once', 'here',
                  'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
                  'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
                  'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
                  'and', 'but', 'if', 'or', 'because', 'until', 'while', 'although',
                  'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them',
                  'their', 'what', 'which', 'who', 'whom', 'i', 'you', 'he', 'she',
                  'we', 'my', 'your', 'his', 'her', 'our', 'about'}
    
    content_words = [w for w in all_words if w not in stop_words and len(w) > 2]
    frequent_words = Counter(content_words).most_common(50)
    
    # Signature words (unique to this author - high frequency relative to typical usage)
    signature_words = [w for w, c in frequent_words if c >= 5][:20]
    
    return {
        'total_words_analyzed': total_words,
        'unique_words': unique_words,
        'type_token_ratio': round(ttr, 4),
        'hapax_legomena_count': len(hapax),
        'hapax_ratio': round(hapax_ratio, 4),
        'average_word_length': round(sum(word_lengths) / len(word_lengths), 2) if word_lengths else 0,
        'signature_words': signature_words,
        'most_frequent_content_words': dict(frequent_words[:30]),
    }


def analyze_sentences(texts: List[str]) -> Dict:
    """Analyze sentence structure patterns."""
    
    all_sentences = []
    sentence_lengths = []
    questions = []
    exclamations = []
    short_sentences = []  # ≤ 10 words
    long_sentences = []   # > 25 words
    
    for text in texts:
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        for sent in sentences:
            words = sent.split()
            word_count = len(words)
            
            all_sentences.append(sent)
            sentence_lengths.append(word_count)
            
            if '?' in sent or sent.endswith('?'):
                questions.append(sent)
            if '!' in sent or sent.endswith('!'):
                exclamations.append(sent)
            if word_count <= 10:
                short_sentences.append(sent)
            if word_count > 25:
                long_sentences.append(sent)
    
    total_sentences = len(all_sentences)
    
    return {
        'total_sentences_analyzed': total_sentences,
        'average_sentence_length': round(sum(sentence_lengths) / total_sentences, 1) if total_sentences else 0,
        'sentence_length_std_dev': round(
            (sum((x - sum(sentence_lengths)/total_sentences)**2 for x in sentence_lengths) / total_sentences)**0.5, 1
        ) if total_sentences > 1 else 0,
        'shortest_sentence_length': min(sentence_lengths) if sentence_lengths else 0,
        'longest_sentence_length': max(sentence_lengths) if sentence_lengths else 0,
        'question_frequency': round(len(questions) / total_sentences * 100, 1) if total_sentences else 0,
        'exclamation_frequency': round(len(exclamations) / total_sentences * 100, 1) if total_sentences else 0,
        'short_sentence_frequency': round(len(short_sentences) / total_sentences * 100, 1) if total_sentences else 0,
        'long_sentence_frequency': round(len(long_sentences) / total_sentences * 100, 1) if total_sentences else 0,
        'sample_questions': questions[:10],
        'sample_short_sentences': short_sentences[:10],
        'sample_long_sentences': [s[:150] + '...' for s in long_sentences[:5]],
    }


def analyze_paragraphs(texts: List[str]) -> Dict:
    """Analyze paragraph structure patterns."""
    
    all_paragraphs = []
    paragraph_lengths = []
    first_sentences = []
    last_sentences = []
    
    for text in texts:
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 50]
        
        for para in paragraphs:
            all_paragraphs.append(para)
            words = para.split()
            paragraph_lengths.append(len(words))
            
            # Get first and last sentences
            sentences = re.split(r'[.!?]+', para)
            sentences = [s.strip() for s in sentences if s.strip()]
            if sentences:
                first_sentences.append(sentences[0])
                if len(sentences) > 1:
                    last_sentences.append(sentences[-1])
    
    total_paragraphs = len(all_paragraphs)
    
    # Analyze first sentence patterns
    first_sentence_starters = Counter()
    for sent in first_sentences:
        words = sent.split()[:3]
        if words:
            starter = ' '.join(words[:2]) if len(words) > 1 else words[0]
            first_sentence_starters[starter.lower()] += 1
    
    return {
        'total_paragraphs_analyzed': total_paragraphs,
        'average_paragraph_length': round(sum(paragraph_lengths) / total_paragraphs, 1) if total_paragraphs else 0,
        'paragraph_length_range': {
            'min': min(paragraph_lengths) if paragraph_lengths else 0,
            'max': max(paragraph_lengths) if paragraph_lengths else 0,
        },
        'common_paragraph_starters': dict(first_sentence_starters.most_common(15)),
        'sample_first_sentences': first_sentences[:15],
        'sample_last_sentences': last_sentences[:10],
    }


def analyze_punctuation(texts: List[str]) -> Dict:
    """Analyze punctuation patterns."""
    
    full_text = ' '.join(texts)
    
    # Count punctuation
    dash_count = full_text.count('—') + full_text.count('–') + full_text.count(' - ')
    ellipsis_count = full_text.count('...')
    colon_count = full_text.count(':')
    semicolon_count = full_text.count(';')
    parentheses_count = full_text.count('(')
    quote_count = full_text.count('"') // 2
    
    # Contractions
    contractions = re.findall(r"\b\w+'[a-z]+\b", full_text.lower())
    contraction_count = len(contractions)
    common_contractions = Counter(contractions).most_common(10)
    
    total_words = len(full_text.split())
    
    return {
        'dash_frequency': round(dash_count / total_words * 1000, 2) if total_words else 0,  # per 1000 words
        'ellipsis_frequency': round(ellipsis_count / total_words * 1000, 2) if total_words else 0,
        'colon_frequency': round(colon_count / total_words * 1000, 2) if total_words else 0,
        'semicolon_frequency': round(semicolon_count / total_words * 1000, 2) if total_words else 0,
        'parentheses_frequency': round(parentheses_count / total_words * 1000, 2) if total_words else 0,
        'quote_frequency': round(quote_count / total_words * 1000, 2) if total_words else 0,
        'contraction_frequency': round(contraction_count / total_words * 100, 2) if total_words else 0,  # percentage
        'common_contractions': dict(common_contractions),
    }


def analyze_personal_voice(texts: List[str]) -> Dict:
    """Analyze personal voice and perspective patterns."""
    
    full_text = ' '.join(texts)
    words = full_text.lower().split()
    total_words = len(words)
    
    # First person pronouns
    first_person_singular = sum(1 for w in words if w in ['i', "i'm", "i've", "i'll", "i'd", 'me', 'my', 'mine', 'myself'])
    first_person_plural = sum(1 for w in words if w in ['we', "we're", "we've", "we'll", "we'd", 'us', 'our', 'ours', 'ourselves'])
    
    # Second person pronouns
    second_person = sum(1 for w in words if w in ['you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself'])
    
    # Extract "I" statements
    i_statements = re.findall(r'\bI\s+\w+\s+\w+\s+\w+', full_text)
    i_statement_patterns = Counter([' '.join(s.split()[:3]) for s in i_statements])
    
    # Questions directed at reader
    reader_questions = re.findall(r'[.!?]\s*([^.!?]*\byou\b[^.!?]*\?)', full_text)
    
    return {
        'first_person_singular_frequency': round(first_person_singular / total_words * 100, 2) if total_words else 0,
        'first_person_plural_frequency': round(first_person_plural / total_words * 100, 2) if total_words else 0,
        'second_person_frequency': round(second_person / total_words * 100, 2) if total_words else 0,
        'common_i_statements': dict(i_statement_patterns.most_common(15)),
        'sample_reader_questions': reader_questions[:10],
    }


def analyze_readability(texts: List[str]) -> Dict:
    """Analyze readability metrics using textstat."""
    
    if not TEXTSTAT_AVAILABLE:
        return {'error': 'textstat not installed'}
    
    full_text = ' '.join(texts)
    
    return {
        'flesch_reading_ease': textstat.flesch_reading_ease(full_text),
        'flesch_kincaid_grade': textstat.flesch_kincaid_grade(full_text),
        'gunning_fog_index': textstat.gunning_fog(full_text),
        'smog_index': textstat.smog_index(full_text),
        'coleman_liau_index': textstat.coleman_liau_index(full_text),
        'automated_readability_index': textstat.automated_readability_index(full_text),
        'dale_chall_readability': textstat.dale_chall_readability_score(full_text),
        'difficult_words_count': textstat.difficult_words(full_text),
        'linsear_write_formula': textstat.linsear_write_formula(full_text),
        'text_standard': textstat.text_standard(full_text),
        'reading_time_minutes': textstat.reading_time(full_text, ms_per_char=14.69) / 60,
    }


def analyze_sentiment(texts: List[str]) -> Dict:
    """Analyze sentiment and subjectivity patterns using TextBlob."""
    
    if not TEXTBLOB_AVAILABLE:
        return {'error': 'textblob not installed'}
    
    polarities = []
    subjectivities = []
    
    for text in texts:
        blob = TextBlob(text)
        for sentence in blob.sentences:
            polarities.append(sentence.sentiment.polarity)
            subjectivities.append(sentence.sentiment.subjectivity)
    
    return {
        'average_polarity': round(sum(polarities) / len(polarities), 3) if polarities else 0,
        'average_subjectivity': round(sum(subjectivities) / len(subjectivities), 3) if subjectivities else 0,
        'polarity_range': {
            'min': round(min(polarities), 3) if polarities else 0,
            'max': round(max(polarities), 3) if polarities else 0,
        },
        'subjectivity_range': {
            'min': round(min(subjectivities), 3) if subjectivities else 0,
            'max': round(max(subjectivities), 3) if subjectivities else 0,
        },
        'sentiment_interpretation': 'mostly positive' if sum(polarities)/len(polarities) > 0.1 else 'mostly negative' if sum(polarities)/len(polarities) < -0.1 else 'neutral/balanced' if polarities else 'unknown',
        'subjectivity_interpretation': 'highly opinionated' if sum(subjectivities)/len(subjectivities) > 0.5 else 'mostly factual' if sum(subjectivities)/len(subjectivities) < 0.3 else 'balanced' if subjectivities else 'unknown',
    }


def analyze_linguistic_features(texts: List[str]) -> Dict:
    """Analyze linguistic features using spaCy."""
    
    if not SPACY_AVAILABLE:
        return {'error': 'spaCy not installed or model not available'}
    
    pos_counts = Counter()
    entity_types = Counter()
    dependencies = Counter()
    
    for text in texts[:20]:  # Limit to first 20 texts for performance
        doc = nlp(text[:5000])  # Limit text length
        
        for token in doc:
            pos_counts[token.pos_] += 1
            dependencies[token.dep_] += 1
        
        for ent in doc.ents:
            entity_types[ent.label_] += 1
    
    total_tokens = sum(pos_counts.values())
    
    return {
        'pos_distribution': {k: round(v/total_tokens*100, 2) for k, v in pos_counts.most_common(15)},
        'noun_frequency': round(pos_counts.get('NOUN', 0) / total_tokens * 100, 2) if total_tokens else 0,
        'verb_frequency': round(pos_counts.get('VERB', 0) / total_tokens * 100, 2) if total_tokens else 0,
        'adjective_frequency': round(pos_counts.get('ADJ', 0) / total_tokens * 100, 2) if total_tokens else 0,
        'adverb_frequency': round(pos_counts.get('ADV', 0) / total_tokens * 100, 2) if total_tokens else 0,
        'named_entity_types': dict(entity_types.most_common(10)),
        'common_dependencies': dict(dependencies.most_common(10)),
    }


def extract_signature_patterns(texts: List[str]) -> Dict:
    """Extract signature phrases and patterns unique to this author."""
    
    # Bigrams and trigrams
    all_bigrams = []
    all_trigrams = []
    
    for text in texts:
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # Bigrams
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            all_bigrams.append(bigram)
        
        # Trigrams
        for i in range(len(words) - 2):
            trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
            all_trigrams.append(trigram)
    
    # Find frequent patterns
    bigram_counts = Counter(all_bigrams)
    trigram_counts = Counter(all_trigrams)
    
    # Filter for meaningful patterns (not just common phrases)
    stop_bigrams = {'of the', 'in the', 'to the', 'on the', 'for the', 'and the', 'is a', 'is the', 'to be', 'it is'}
    signature_bigrams = [(b, c) for b, c in bigram_counts.most_common(50) if b not in stop_bigrams and c >= 3]
    
    stop_trigrams = {'one of the', 'as well as', 'in order to', 'there is a', 'it is a'}
    signature_trigrams = [(t, c) for t, c in trigram_counts.most_common(50) if t not in stop_trigrams and c >= 2]
    
    return {
        'signature_bigrams': dict(signature_bigrams[:20]),
        'signature_trigrams': dict(signature_trigrams[:15]),
    }


def run_deep_analysis(newsletters: List[Dict], include_custom: bool = True) -> Dict:
    """Run comprehensive deep analysis on newsletters and custom writing samples."""
    
    # Import html_to_text to convert HTML to plain text
    try:
        from style_analyzer import html_to_text
    except ImportError:
        # Fallback: simple HTML stripping
        import re
        def html_to_text(html):
            text = re.sub(r'<[^>]+>', '', html)
            return text.strip()
    
    print("=" * 60)
    print("DEEP STYLE ANALYZER")
    print("=" * 60)
    
    # Extract text content - check both 'content' and 'content_html'
    texts = []
    newsletter_count = 0
    custom_count = 0
    
    for nl in newsletters:
        # Try 'content' first, then 'content_html'
        content = nl.get('content', '')
        if not content:
            content_html = nl.get('content_html', '')
            if content_html:
                content = html_to_text(content_html)
        
        if content and len(content) > 100:
            texts.append(content)
            newsletter_count += 1
    
    # Also include custom writing samples
    if include_custom:
        custom_samples = load_custom_writing_samples()
        for sample in custom_samples:
            text = sample.get('text', '') if isinstance(sample, dict) else sample
            if text and len(text) > 100:
                texts.append(text)
                custom_count += 1
        
        if custom_count > 0:
            print(f"Including {custom_count} custom writing samples")
    
    if not texts:
        return {'error': 'No newsletter content found'}
    
    print(f"\nAnalyzing {len(texts)} newsletters...")
    
    # Run all analyses
    results = {
        'meta': {
            'total_texts_analyzed': len(texts),
            'newsletters_analyzed': newsletter_count,
            'custom_samples_analyzed': custom_count,
            'total_characters': sum(len(t) for t in texts),
            'analysis_date': datetime.now().isoformat(),
            'libraries_available': {
                'textstat': TEXTSTAT_AVAILABLE,
                'spacy': SPACY_AVAILABLE,
                'textblob': TEXTBLOB_AVAILABLE,
                'sentence_transformers': SENTENCE_TRANSFORMERS_AVAILABLE,
            }
        }
    }
    
    print("\n1. Analyzing vocabulary patterns...")
    results['vocabulary'] = analyze_vocabulary(texts)
    
    print("2. Analyzing sentence structure...")
    results['sentences'] = analyze_sentences(texts)
    
    print("3. Analyzing paragraph patterns...")
    results['paragraphs'] = analyze_paragraphs(texts)
    
    print("4. Analyzing punctuation habits...")
    results['punctuation'] = analyze_punctuation(texts)
    
    print("5. Analyzing personal voice...")
    results['personal_voice'] = analyze_personal_voice(texts)
    
    print("6. Extracting signature patterns...")
    results['signature_patterns'] = extract_signature_patterns(texts)
    
    if TEXTSTAT_AVAILABLE:
        print("7. Calculating readability metrics...")
        results['readability'] = analyze_readability(texts)
    
    if TEXTBLOB_AVAILABLE:
        print("8. Analyzing sentiment patterns...")
        results['sentiment'] = analyze_sentiment(texts)
    
    if SPACY_AVAILABLE:
        print("9. Analyzing linguistic features...")
        results['linguistics'] = analyze_linguistic_features(texts)
    
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        print("10. Analyzing semantic patterns (using sentence-transformers)...")
        results['semantic'] = analyze_semantic_patterns(texts)
    
    # Save results
    DATA_DIR.mkdir(exist_ok=True)
    with open(DEEP_BIBLE_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Deep analysis saved to: {DEEP_BIBLE_FILE}")
    print("=" * 60)
    
    return results


def load_deep_bible() -> Dict:
    """Load the deep style analysis."""
    if not DEEP_BIBLE_FILE.exists():
        return {}
    with open(DEEP_BIBLE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_deep_style_context(topic: str = "") -> str:
    """Get deep style context for generation prompts."""
    
    deep = load_deep_bible()
    if not deep:
        return ""
    
    context = "\n## DEEP STYLE ANALYSIS (from advanced linguistic analysis)\n\n"
    
    # Vocabulary
    vocab = deep.get('vocabulary', {})
    if vocab:
        context += f"**Vocabulary:** Type-token ratio {vocab.get('type_token_ratio', 0)} | "
        context += f"Avg word length {vocab.get('average_word_length', 0)} characters\n"
        sig_words = vocab.get('signature_words', [])
        if sig_words:
            context += f"**Your signature words:** {', '.join(sig_words[:10])}\n\n"
    
    # Sentences
    sent = deep.get('sentences', {})
    if sent:
        context += f"**Sentence style:** Avg {sent.get('average_sentence_length', 0)} words | "
        context += f"{sent.get('short_sentence_frequency', 0)}% short (≤10 words) | "
        context += f"{sent.get('question_frequency', 0)}% questions\n\n"
    
    # Personal voice
    voice = deep.get('personal_voice', {})
    if voice:
        context += f"**Personal voice:** {voice.get('first_person_singular_frequency', 0)}% first person | "
        context += f"{voice.get('second_person_frequency', 0)}% addressing reader\n"
        i_statements = voice.get('common_i_statements', {})
        if i_statements:
            context += f"**Common 'I' patterns:** {', '.join(list(i_statements.keys())[:5])}\n\n"
    
    # Readability
    read = deep.get('readability', {})
    if read and 'error' not in read:
        context += f"**Readability:** {read.get('text_standard', 'N/A')} | "
        context += f"Flesch-Kincaid grade {read.get('flesch_kincaid_grade', 0)}\n\n"
    
    # Sentiment
    sentiment = deep.get('sentiment', {})
    if sentiment and 'error' not in sentiment:
        context += f"**Tone:** {sentiment.get('sentiment_interpretation', 'unknown')} | "
        context += f"{sentiment.get('subjectivity_interpretation', 'unknown')}\n\n"
    
    # Signature patterns
    patterns = deep.get('signature_patterns', {})
    if patterns:
        bigrams = patterns.get('signature_bigrams', {})
        if bigrams:
            context += f"**Your signature phrases:** {', '.join(list(bigrams.keys())[:8])}\n"
    
    # Semantic patterns (from sentence-transformers analysis)
    semantic = deep.get('semantic', {})
    if semantic and 'error' not in semantic:
        context += f"\n**Semantic profile:** {semantic.get('consistency_interpretation', 'unknown')} | "
        context += f"{semantic.get('diversity_interpretation', 'unknown')}\n"
        rep_sentences = semantic.get('most_representative_sentences', [])
        if rep_sentences:
            context += f"**Most 'you' sentences:**\n"
            for sent in rep_sentences[:3]:
                context += f"  - \"{sent[:100]}...\"\n"
    
    return context


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    from style_analyzer import load_all_newsletters
    
    newsletters = load_all_newsletters()
    if newsletters:
        result = run_deep_analysis(newsletters)
        print(f"\nAnalysis complete! Found {len(result)} analysis categories.")
    else:
        print("No newsletters found. Run the Substack scraper first.")

