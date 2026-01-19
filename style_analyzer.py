"""
Style Analyzer - Deep Analysis of Paul McNally's Newsletter Writing

Analyzes all scraped newsletters to extract:
- Writing patterns and style fingerprint
- Headline formulas that work
- Structural patterns
- Topic/angle preferences
- Voice characteristics
- Generates a "Newsletter Bible" for future writing
"""

import json
import re
from pathlib import Path
from collections import Counter
from typing import Optional
from html import unescape

import pandas as pd
from bs4 import BeautifulSoup


DATA_DIR = Path(__file__).parent / "data"
RAW_DATA_FILE = DATA_DIR / "newsletters_raw.jsonl"
STATS_FILE = DATA_DIR / "newsletters_with_stats.csv"
BIBLE_FILE = DATA_DIR / "newsletter_bible.json"


# ============================================================================
# Text Extraction Utilities
# ============================================================================

def html_to_text(html: str) -> str:
    """Convert HTML to clean text."""
    if not html:
        return ""
    soup = BeautifulSoup(html, 'lxml')
    for elem in soup(['script', 'style', 'nav', 'header', 'footer']):
        elem.decompose()
    text = soup.get_text(separator='\n', strip=True)
    return unescape(text)


def extract_paragraphs(html: str) -> list[str]:
    """Extract individual paragraphs from HTML."""
    if not html:
        return []
    soup = BeautifulSoup(html, 'lxml')
    paragraphs = []
    for p in soup.find_all(['p', 'li', 'h2', 'h3', 'blockquote']):
        text = p.get_text(strip=True)
        if text and len(text) > 20:
            paragraphs.append(text)
    return paragraphs


def extract_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    # Simple sentence splitter
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip() and len(s) > 10]


# ============================================================================
# Load All Newsletter Data
# ============================================================================

def load_all_newsletters() -> list[dict]:
    """Load all scraped newsletters."""
    if not RAW_DATA_FILE.exists():
        return []
    
    newsletters = []
    with open(RAW_DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                newsletters.append(json.loads(line))
    return newsletters


def load_stats() -> dict:
    """Load stats as a dict keyed by title."""
    if not STATS_FILE.exists():
        return {}
    
    df = pd.read_csv(STATS_FILE)
    stats = {}
    for _, row in df.iterrows():
        title = str(row.get('title', '')).strip().lower()
        stats[title] = {
            'views': row.get('views'),
            'open_rate': row.get('open_rate'),
        }
    return stats


# ============================================================================
# Headline Analysis
# ============================================================================

def analyze_headlines(newsletters: list[dict]) -> dict:
    """Deep analysis of headline patterns."""
    titles = [n['title'] for n in newsletters if n.get('title')]
    
    analysis = {
        'total_headlines': len(titles),
        'avg_word_count': 0,
        'avg_char_count': 0,
        'patterns': {},
        'common_structures': [],
        'opening_words': Counter(),
        'power_words_used': [],
        'punctuation_usage': {},
        'examples_by_type': {},
    }
    
    word_counts = []
    char_counts = []
    
    # Pattern counters
    has_question = []
    has_colon = []
    has_ellipsis = []
    has_number = []
    has_em_dash = []
    
    for title in titles:
        words = title.split()
        word_counts.append(len(words))
        char_counts.append(len(title))
        
        # First word
        if words:
            first_word = words[0].lower().strip('0123456789')
            analysis['opening_words'][first_word] += 1
        
        # Pattern detection
        has_question.append('?' in title)
        has_colon.append(':' in title)
        has_ellipsis.append('...' in title)
        has_number.append(bool(re.match(r'^\d+', title)))
        has_em_dash.append('—' in title or ' - ' in title)
    
    analysis['avg_word_count'] = sum(word_counts) / len(word_counts) if word_counts else 0
    analysis['avg_char_count'] = sum(char_counts) / len(char_counts) if char_counts else 0
    
    analysis['patterns'] = {
        'question_headlines': {
            'count': sum(has_question),
            'percentage': sum(has_question) / len(titles) * 100 if titles else 0,
            'examples': [t for t, q in zip(titles, has_question) if q][:5]
        },
        'colon_headlines': {
            'count': sum(has_colon),
            'percentage': sum(has_colon) / len(titles) * 100 if titles else 0,
            'examples': [t for t, c in zip(titles, has_colon) if c][:5]
        },
        'number_headlines': {
            'count': sum(has_number),
            'percentage': sum(has_number) / len(titles) * 100 if titles else 0,
            'examples': [t for t, n in zip(titles, has_number) if n][:5]
        },
        'ellipsis_headlines': {
            'count': sum(has_ellipsis),
            'percentage': sum(has_ellipsis) / len(titles) * 100 if titles else 0,
            'examples': [t for t, e in zip(titles, has_ellipsis) if e][:5]
        },
    }
    
    # Categorize headline types
    analysis['examples_by_type'] = {
        'provocative_questions': [t for t in titles if '?' in t and any(w in t.lower() for w in ['will', 'could', 'is', 'are', 'can'])],
        'how_to': [t for t in titles if t.lower().startswith('how to') or 'how to' in t.lower()],
        'listicles': [t for t in titles if re.match(r'^\d+\s', t)],
        'vs_confrontation': [t for t in titles if ' vs ' in t.lower() or ' vs. ' in t.lower()],
        'future_predictions': [t for t in titles if any(w in t.lower() for w in ['will', 'future', 'coming', 'next'])],
    }
    
    return analysis


# ============================================================================
# Writing Style Analysis
# ============================================================================

def analyze_writing_style(newsletters: list[dict]) -> dict:
    """Analyze Paul's writing style and voice."""
    
    all_text = ""
    all_paragraphs = []
    all_sentences = []
    opening_lines = []
    closing_lines = []
    
    for n in newsletters:
        content = n.get('content_html', '')
        if not content:
            continue
        
        text = html_to_text(content)
        all_text += text + "\n\n"
        
        paragraphs = extract_paragraphs(content)
        all_paragraphs.extend(paragraphs)
        
        sentences = extract_sentences(text)
        all_sentences.extend(sentences)
        
        if paragraphs:
            opening_lines.append(paragraphs[0])
            if len(paragraphs) > 1:
                closing_lines.append(paragraphs[-1])
    
    # Word frequency analysis
    words = re.findall(r'\b[a-zA-Z]{4,}\b', all_text.lower())
    word_freq = Counter(words)
    
    # Remove common stop words
    stop_words = {'this', 'that', 'with', 'from', 'have', 'been', 'will', 'would', 
                  'could', 'should', 'about', 'their', 'there', 'which', 'what',
                  'when', 'where', 'they', 'them', 'than', 'then', 'also', 'just',
                  'more', 'some', 'into', 'your', 'only', 'other', 'very', 'even',
                  'most', 'much', 'such', 'like', 'over', 'make', 'made', 'being'}
    
    signature_words = {w: c for w, c in word_freq.most_common(200) if w not in stop_words}
    
    # Sentence length analysis
    sentence_lengths = [len(s.split()) for s in all_sentences]
    
    # Paragraph length analysis
    para_lengths = [len(p.split()) for p in all_paragraphs]
    
    # Find signature phrases (2-4 word combinations)
    bigrams = []
    trigrams = []
    for sentence in all_sentences:
        words = sentence.lower().split()
        for i in range(len(words) - 1):
            bigrams.append(' '.join(words[i:i+2]))
        for i in range(len(words) - 2):
            trigrams.append(' '.join(words[i:i+3]))
    
    common_bigrams = Counter(bigrams).most_common(30)
    common_trigrams = Counter(trigrams).most_common(30)
    
    # Filter to meaningful phrases
    meaningful_phrases = [
        phrase for phrase, count in common_trigrams 
        if count >= 3 and not all(w in stop_words for w in phrase.split())
    ]
    
    analysis = {
        'total_words_analyzed': len(words),
        'total_paragraphs': len(all_paragraphs),
        'total_sentences': len(all_sentences),
        
        'sentence_stats': {
            'avg_length': sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0,
            'min_length': min(sentence_lengths) if sentence_lengths else 0,
            'max_length': max(sentence_lengths) if sentence_lengths else 0,
            'short_punchy_pct': len([s for s in sentence_lengths if s <= 10]) / len(sentence_lengths) * 100 if sentence_lengths else 0,
        },
        
        'paragraph_stats': {
            'avg_length': sum(para_lengths) / len(para_lengths) if para_lengths else 0,
            'short_para_pct': len([p for p in para_lengths if p <= 30]) / len(para_lengths) * 100 if para_lengths else 0,
        },
        
        'signature_vocabulary': dict(list(signature_words.items())[:50]),
        'signature_phrases': meaningful_phrases[:20],
        
        'opening_patterns': {
            'sample_openings': opening_lines[:10],
            'common_opening_words': Counter([o.split()[0].lower() if o.split() else '' for o in opening_lines]).most_common(10),
        },
        
        'closing_patterns': {
            'sample_closings': closing_lines[:10],
        },
        
        'voice_characteristics': [],  # Will be filled by analysis
    }
    
    # Detect voice characteristics
    voice_traits = []
    
    # Check for direct address
    if word_freq.get('you', 0) > 50:
        voice_traits.append("Direct address to reader (uses 'you' frequently)")
    
    # Check for first person
    if word_freq.get('i', 0) > 30 or word_freq.get('we', 0) > 30:
        voice_traits.append("Personal voice (uses first person)")
    
    # Check for questions in body
    question_count = all_text.count('?')
    if question_count > len(newsletters) * 3:
        voice_traits.append("Rhetorical questioning (asks readers to think)")
    
    # Check for contractions (informal)
    contractions = len(re.findall(r"\b\w+'t\b|\b\w+'s\b|\b\w+'re\b|\b\w+'ll\b", all_text))
    if contractions > 50:
        voice_traits.append("Conversational tone (uses contractions)")
    
    # Check for emphatic punctuation
    if all_text.count('...') > 20:
        voice_traits.append("Uses ellipsis for dramatic pause/trailing thoughts")
    
    analysis['voice_characteristics'] = voice_traits
    
    return analysis


# ============================================================================
# Structure Analysis
# ============================================================================

def analyze_structure(newsletters: list[dict]) -> dict:
    """Analyze newsletter structure patterns."""
    
    structures = []
    
    for n in newsletters:
        content = n.get('content_html', '')
        if not content:
            continue
        
        soup = BeautifulSoup(content, 'lxml')
        
        structure = {
            'title': n.get('title', ''),
            'h2_count': len(soup.find_all('h2')),
            'h3_count': len(soup.find_all('h3')),
            'paragraph_count': len(soup.find_all('p')),
            'list_count': len(soup.find_all(['ul', 'ol'])),
            'blockquote_count': len(soup.find_all('blockquote')),
            'link_count': len(soup.find_all('a')),
            'image_count': len(soup.find_all('img')),
            'has_numbered_sections': bool(re.search(r'<h[23]>\s*\d+[\.\)]', content)),
        }
        
        # Extract section headings
        headings = [h.get_text(strip=True) for h in soup.find_all(['h2', 'h3'])]
        structure['section_headings'] = headings
        
        # Word count
        text = html_to_text(content)
        structure['word_count'] = len(text.split())
        
        structures.append(structure)
    
    # Aggregate statistics
    if not structures:
        return {}
    
    analysis = {
        'newsletter_count': len(structures),
        
        'length_stats': {
            'avg_word_count': sum(s['word_count'] for s in structures) / len(structures),
            'min_word_count': min(s['word_count'] for s in structures),
            'max_word_count': max(s['word_count'] for s in structures),
            'typical_range': f"{int(sum(s['word_count'] for s in structures) / len(structures) * 0.7)} - {int(sum(s['word_count'] for s in structures) / len(structures) * 1.3)} words",
        },
        
        'section_stats': {
            'avg_h2_sections': sum(s['h2_count'] for s in structures) / len(structures),
            'avg_h3_sections': sum(s['h3_count'] for s in structures) / len(structures),
            'uses_numbered_sections_pct': len([s for s in structures if s['has_numbered_sections']]) / len(structures) * 100,
        },
        
        'element_usage': {
            'avg_paragraphs': sum(s['paragraph_count'] for s in structures) / len(structures),
            'avg_lists': sum(s['list_count'] for s in structures) / len(structures),
            'avg_blockquotes': sum(s['blockquote_count'] for s in structures) / len(structures),
            'avg_links': sum(s['link_count'] for s in structures) / len(structures),
            'avg_images': sum(s['image_count'] for s in structures) / len(structures),
        },
        
        'common_section_headings': [],
        'structure_templates': [],
    }
    
    # Find common section heading patterns
    all_headings = []
    for s in structures:
        all_headings.extend(s.get('section_headings', []))
    
    heading_patterns = Counter()
    for h in all_headings:
        # Normalize to pattern
        h_lower = h.lower()
        if h_lower.startswith('what'):
            heading_patterns['What... questions'] += 1
        elif h_lower.startswith('how'):
            heading_patterns['How... questions'] += 1
        elif h_lower.startswith('why'):
            heading_patterns['Why... questions'] += 1
        elif re.match(r'^\d+[\.\)]', h):
            heading_patterns['Numbered sections'] += 1
        elif 'the' in h_lower and len(h.split()) <= 5:
            heading_patterns['Short declarative'] += 1
    
    analysis['common_section_headings'] = dict(heading_patterns.most_common(10))
    
    return analysis


# ============================================================================
# Topic & Theme Analysis
# ============================================================================

def analyze_topics(newsletters: list[dict]) -> dict:
    """Analyze topic patterns and themes."""
    
    # Topic keywords
    topic_keywords = {
        'ai_regulation': ['eu ai act', 'regulation', 'law', 'legal', 'lawsuit', 'court', 'ban', 'compliance'],
        'media_industry': ['newsroom', 'journalism', 'journalist', 'media', 'publisher', 'news', 'editorial'],
        'ai_tools': ['chatgpt', 'openai', 'claude', 'gemini', 'gpt', 'prompt', 'tool', 'build'],
        'africa': ['africa', 'african', 'nigeria', 'kenya', 'south africa', 'egypt', 'zimbabwe'],
        'global_south': ['global south', 'asia', 'india', 'latin america', 'developing'],
        'future_predictions': ['future', 'will', 'coming', 'next year', '2025', '2024', 'prediction'],
        'how_to_practical': ['how to', 'step', 'guide', 'tutorial', 'build', 'create', 'use'],
        'controversy': ['destroy', 'collapse', 'disaster', 'horror', 'insane', 'crisis', 'war'],
    }
    
    topic_counts = {topic: 0 for topic in topic_keywords}
    topic_examples = {topic: [] for topic in topic_keywords}
    
    for n in newsletters:
        title = n.get('title', '').lower()
        content = html_to_text(n.get('content_html', '')).lower()
        combined = f"{title} {content}"
        
        for topic, keywords in topic_keywords.items():
            if any(kw in combined for kw in keywords):
                topic_counts[topic] += 1
                if len(topic_examples[topic]) < 3:
                    topic_examples[topic].append(n.get('title', ''))
    
    # Calculate percentages
    total = len(newsletters)
    topic_analysis = {}
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
        topic_analysis[topic] = {
            'count': count,
            'percentage': count / total * 100 if total else 0,
            'examples': topic_examples[topic],
        }
    
    return {
        'topic_distribution': topic_analysis,
        'primary_themes': [t for t, d in topic_analysis.items() if d['percentage'] > 20],
        'niche_themes': [t for t, d in topic_analysis.items() if 5 < d['percentage'] <= 20],
    }


# ============================================================================
# Performance Correlation Analysis (NEW - with real open rates!)
# ============================================================================

def analyze_performance_correlations(newsletters: list[dict], stats: dict) -> dict:
    """
    Analyze what headline/content features correlate with higher open rates.
    This is the KEY insight for improving future newsletters.
    """
    
    if not stats:
        return {}
    
    # Build a combined dataset
    data = []
    for n in newsletters:
        title = n.get('title', '')
        title_key = title.strip().lower()
        
        if title_key in stats:
            stat = stats[title_key]
            open_rate = stat.get('open_rate', 0)
            if open_rate and open_rate > 0:
                # Headline features
                words = title.split()
                
                row = {
                    'title': title,
                    'open_rate': open_rate,
                    'word_count': len(words),
                    'char_count': len(title),
                    'has_question': '?' in title,
                    'has_colon': ':' in title,
                    'has_ellipsis': '...' in title,
                    'starts_with_number': bool(re.match(r'^\d+', title)),
                    'has_how_to': 'how to' in title.lower(),
                    'has_will': title.lower().startswith('will') or ' will ' in title.lower(),
                    'has_ai_term': any(t in title.lower() for t in ['ai', 'chatgpt', 'openai', 'gpt']),
                    'has_africa': 'africa' in title.lower(),
                    'has_strong_word': any(w in title.lower() for w in ['insane', 'destroy', 'disaster', 'horror', 'incredible', 'amazing']),
                }
                data.append(row)
    
    if len(data) < 5:
        return {}
    
    df = pd.DataFrame(data)
    
    correlations = {
        'sample_size': len(df),
        'avg_open_rate': df['open_rate'].mean(),
        'feature_impact': {},
        'top_performers': [],
        'insights': [],
    }
    
    # Analyze each binary feature
    binary_features = [
        ('has_question', 'Question headlines (?)'),
        ('has_colon', 'Colon headlines (:)'),
        ('has_ellipsis', 'Ellipsis headlines (...)'),
        ('starts_with_number', 'Number headlines (3 ways...)'),
        ('has_how_to', '"How to" headlines'),
        ('has_will', '"Will" predictions'),
        ('has_ai_term', 'AI terminology'),
        ('has_africa', 'Africa mentions'),
        ('has_strong_word', 'Strong emotional words'),
    ]
    
    for feature, label in binary_features:
        with_feature = df[df[feature] == True]['open_rate']
        without_feature = df[df[feature] == False]['open_rate']
        
        if len(with_feature) >= 2 and len(without_feature) >= 2:
            avg_with = with_feature.mean()
            avg_without = without_feature.mean()
            difference = avg_with - avg_without
            
            correlations['feature_impact'][label] = {
                'with_feature': round(avg_with, 4),
                'without_feature': round(avg_without, 4),
                'difference': round(difference, 4),
                'difference_pct': f"{difference * 100:+.1f}%",
                'count_with': len(with_feature),
                'count_without': len(without_feature),
                'recommendation': 'USE MORE' if difference > 0.03 else ('AVOID' if difference < -0.03 else 'NEUTRAL'),
            }
    
    # Headline length analysis
    short = df[df['word_count'] <= 7]['open_rate']
    medium = df[(df['word_count'] > 7) & (df['word_count'] <= 12)]['open_rate']
    long = df[df['word_count'] > 12]['open_rate']
    
    correlations['headline_length'] = {
        'short_1_7_words': {'avg_open_rate': round(short.mean(), 4) if len(short) > 0 else 0, 'count': len(short)},
        'medium_8_12_words': {'avg_open_rate': round(medium.mean(), 4) if len(medium) > 0 else 0, 'count': len(medium)},
        'long_13_plus_words': {'avg_open_rate': round(long.mean(), 4) if len(long) > 0 else 0, 'count': len(long)},
    }
    
    # Top 10 performers with their characteristics
    top_10 = df.nlargest(10, 'open_rate')
    for _, row in top_10.iterrows():
        features = []
        if row['has_question']: features.append('question')
        if row['has_colon']: features.append('colon')
        if row['has_ellipsis']: features.append('ellipsis')
        if row['starts_with_number']: features.append('number')
        if row['has_how_to']: features.append('how-to')
        if row['has_strong_word']: features.append('strong-word')
        
        correlations['top_performers'].append({
            'title': row['title'],
            'open_rate': round(row['open_rate'], 4),
            'features': features,
        })
    
    # Generate insights
    insights = []
    
    # Find strongest positive correlations
    positive_impacts = [(k, v) for k, v in correlations['feature_impact'].items() if v['difference'] > 0.02]
    positive_impacts.sort(key=lambda x: x[1]['difference'], reverse=True)
    
    for feature, data in positive_impacts[:3]:
        insights.append(f"✓ {feature}: +{data['difference']*100:.1f}% open rate ({data['count_with']} newsletters)")
    
    # Find strongest negative correlations
    negative_impacts = [(k, v) for k, v in correlations['feature_impact'].items() if v['difference'] < -0.02]
    negative_impacts.sort(key=lambda x: x[1]['difference'])
    
    for feature, data in negative_impacts[:2]:
        insights.append(f"✗ {feature}: {data['difference']*100:.1f}% open rate ({data['count_with']} newsletters)")
    
    correlations['insights'] = insights
    
    return correlations


# ============================================================================
# Generate Newsletter Bible
# ============================================================================

def generate_newsletter_bible(newsletters: list[dict], stats: dict) -> dict:
    """Generate comprehensive Newsletter Bible from all analysis."""
    
    print("Analyzing headlines...")
    headline_analysis = analyze_headlines(newsletters)
    
    print("Analyzing writing style...")
    style_analysis = analyze_writing_style(newsletters)
    
    print("Analyzing structure...")
    structure_analysis = analyze_structure(newsletters)
    
    print("Analyzing topics...")
    topic_analysis = analyze_topics(newsletters)
    
    print("Analyzing performance correlations...")
    performance_analysis = analyze_performance_correlations(newsletters, stats)
    
    # Combine into Bible
    bible = {
        'meta': {
            'newsletters_analyzed': len(newsletters),
            'generated_from': 'developai.substack.com',
            'author': 'Paul McNally',
        },
        
        'headline_formulas': {
            'optimal_length': f"{int(headline_analysis['avg_word_count'])} words ({int(headline_analysis['avg_char_count'])} characters)",
            'most_effective_patterns': [],
            'pattern_breakdown': headline_analysis['patterns'],
            'headline_templates': [],
            'opening_words_that_work': dict(headline_analysis['opening_words'].most_common(15)),
            'examples_by_type': headline_analysis['examples_by_type'],
        },
        
        'writing_voice': {
            'characteristics': style_analysis['voice_characteristics'],
            'signature_vocabulary': list(style_analysis['signature_vocabulary'].keys())[:30],
            'signature_phrases': style_analysis['signature_phrases'],
            'sentence_style': {
                'avg_length': f"{style_analysis['sentence_stats']['avg_length']:.1f} words",
                'punchy_short_sentences': f"{style_analysis['sentence_stats']['short_punchy_pct']:.1f}% are 10 words or less",
            },
            'paragraph_style': {
                'avg_length': f"{style_analysis['paragraph_stats']['avg_length']:.1f} words",
                'keeps_paragraphs_short': style_analysis['paragraph_stats']['short_para_pct'] > 50,
            },
            'opening_techniques': style_analysis['opening_patterns'],
            'closing_techniques': style_analysis['closing_patterns'],
        },
        
        'structure_blueprint': {
            'typical_length': structure_analysis.get('length_stats', {}).get('typical_range', 'Unknown'),
            'avg_word_count': structure_analysis.get('length_stats', {}).get('avg_word_count', 0),
            'sections': structure_analysis.get('section_stats', {}),
            'elements': structure_analysis.get('element_usage', {}),
            'section_heading_styles': structure_analysis.get('common_section_headings', {}),
        },
        
        'topic_strategy': {
            'primary_themes': topic_analysis.get('primary_themes', []),
            'topic_mix': topic_analysis.get('topic_distribution', {}),
            'winning_angles': [],  # To be filled with high-performing topic combos
        },
        
        'rules_for_success': [],  # Synthesized rules
        
        'cliches_to_avoid': [  # Generic phrases and cliches to NEVER use
            "Change is coming, and it's coming fast",
            "land on your feet",
            "this is your moment",
            "double down",
            "what makes you human",
            "Let's get ready for [year], together",
            "the future is now",
            "game changer",
            "think outside the box",
            "at the end of the day",
            "it's not rocket science",
            "the writing is on the wall",
            "paradigm shift",
            "low-hanging fruit",
            "move the needle",
            "circle back",
            "touch base",
            "synergy",
            "leverage",
            "disrupt",
            "innovative solution",
            "cutting edge",
            "state of the art",
            "take it to the next level",
            "raise the bar",
            "step up your game",
            "the bottom line",
            "it goes without saying",
            "needless to say",
            "in this day and age",
            "now more than ever",
            "the time is now",
            "seize the opportunity",
            "embrace change",
            "adapt or die",
            "survival of the fittest",
            "the only constant is change",
            "knowledge is power",
            "work smarter, not harder",
        ],
        
        'sample_high_performers': [],  # Top performing examples
        
        'performance_insights': performance_analysis,  # Data-driven insights from real open rates
    }
    
    # Generate synthesized rules
    rules = []
    
    # Headline rules
    if headline_analysis['patterns']['question_headlines']['percentage'] > 30:
        rules.append(f"Use question headlines ~{headline_analysis['patterns']['question_headlines']['percentage']:.0f}% of the time - they create engagement")
    
    if headline_analysis['patterns']['colon_headlines']['percentage'] > 20:
        rules.append("Use colon structure for 'Topic: Angle' headlines")
    
    rules.append(f"Keep headlines around {int(headline_analysis['avg_word_count'])} words")
    
    # Structure rules
    avg_words = structure_analysis.get('length_stats', {}).get('avg_word_count', 1000)
    rules.append(f"Target {int(avg_words)} words per newsletter")
    
    if structure_analysis.get('section_stats', {}).get('avg_h2_sections', 0) > 2:
        rules.append("Break content into 2-4 major sections with H2 headings")
    
    # Voice rules
    for trait in style_analysis['voice_characteristics']:
        rules.append(f"Voice: {trait}")
    
    # Anti-cliche rule
    rules.append("NEVER use generic cliches or corporate speak - be specific, direct, and authentic")
    
    bible['rules_for_success'] = rules
    
    # Add top performing if we have stats
    if stats:
        performers = []
        for n in newsletters:
            title = n.get('title', '').strip().lower()
            if title in stats:
                performers.append({
                    'title': n.get('title'),
                    'open_rate': stats[title].get('open_rate'),
                    'views': stats[title].get('views'),
                })
        
        # Sort by open rate
        performers.sort(key=lambda x: x.get('open_rate', 0) or 0, reverse=True)
        bible['sample_high_performers'] = performers[:10]
    
    return bible


def save_bible(bible: dict):
    """Save the Newsletter Bible to file."""
    with open(BIBLE_FILE, 'w', encoding='utf-8') as f:
        json.dump(bible, f, indent=2, ensure_ascii=False)
    print(f"Newsletter Bible saved to: {BIBLE_FILE}")


def load_bible() -> dict:
    """Load existing Newsletter Bible."""
    if not BIBLE_FILE.exists():
        return {}
    with open(BIBLE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================================
# Main
# ============================================================================

def run_analysis():
    """Run full analysis and generate Newsletter Bible."""
    print("=" * 60)
    print("NEWSLETTER STYLE ANALYZER")
    print("=" * 60)
    
    newsletters = load_all_newsletters()
    print(f"\nLoaded {len(newsletters)} newsletters")
    
    if not newsletters:
        print("No newsletters found. Run scrape_substack.py first.")
        return None
    
    stats = load_stats()
    print(f"Loaded stats for {len(stats)} newsletters")
    
    print("\nGenerating Newsletter Bible...")
    bible = generate_newsletter_bible(newsletters, stats)
    
    save_bible(bible)
    
    print("\n" + "=" * 60)
    print("NEWSLETTER BIBLE SUMMARY")
    print("=" * 60)
    
    print(f"\n📊 Analyzed: {bible['meta']['newsletters_analyzed']} newsletters")
    
    print(f"\n📝 HEADLINE FORMULA:")
    print(f"   Optimal length: {bible['headline_formulas']['optimal_length']}")
    
    print(f"\n🎤 VOICE CHARACTERISTICS:")
    for trait in bible['writing_voice']['characteristics']:
        print(f"   • {trait}")
    
    print(f"\n📐 STRUCTURE:")
    print(f"   Typical length: {bible['structure_blueprint']['typical_length']}")
    
    print(f"\n🎯 RULES FOR SUCCESS:")
    for rule in bible['rules_for_success']:
        print(f"   • {rule}")
    
    # Performance insights
    perf = bible.get('performance_insights', {})
    if perf:
        print(f"\n📈 PERFORMANCE INSIGHTS (based on {perf.get('sample_size', 0)} newsletters):")
        print(f"   Average open rate: {perf.get('avg_open_rate', 0):.1%}")
        
        if perf.get('insights'):
            print(f"\n   Data-driven findings:")
            for insight in perf['insights']:
                print(f"   {insight}")
        
        if perf.get('top_performers'):
            print(f"\n   🏆 Top 5 performers:")
            for i, tp in enumerate(perf['top_performers'][:5], 1):
                print(f"   {i}. {tp['open_rate']:.1%} - {tp['title'][:45]}...")
    
    return bible


if __name__ == "__main__":
    run_analysis()

