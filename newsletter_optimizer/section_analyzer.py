"""
Section Analyzer - Analyzes section patterns across all newsletters

Identifies:
- Recurring section types (tools, tips, main story, etc.)
- Section frequencies
- Section ordering patterns
- Section characteristics
"""

import json
import re
from pathlib import Path
from collections import Counter, defaultdict
from typing import Optional

from bs4 import BeautifulSoup
import pandas as pd


DATA_DIR = Path(__file__).parent / "data"
RAW_DATA_FILE = DATA_DIR / "newsletters_raw.jsonl"
SECTIONS_FILE = DATA_DIR / "section_patterns.json"


# ============================================================================
# Section Type Definitions - Will be refined based on analysis
# ============================================================================

# Keywords that help identify section types
SECTION_TYPE_KEYWORDS = {
    'main_story': {
        'name': 'Main Story / Deep Dive',
        'description': 'The primary article or analysis piece',
        'keywords': [],  # Usually the first major section
        'icon': '📰',
    },
    'tools_and_tips': {
        'name': 'Tools & Tips',
        'description': 'Practical AI tools and how to use them',
        'keywords': ['tool', 'tips', 'how to', 'tutorial', 'guide', 'try this', 'use this'],
        'icon': '🛠️',
    },
    'news_roundup': {
        'name': 'News Roundup / This Week',
        'description': 'Quick news items and updates',
        'keywords': ['news', 'this week', 'roundup', 'updates', 'headlines', 'briefly'],
        'icon': '📋',
    },
    'africa_focus': {
        'name': 'Africa / Global South Focus',
        'description': 'Africa-specific AI news and analysis',
        'keywords': ['africa', 'african', 'global south', 'kenya', 'nigeria', 'south africa', 'zimbabwe'],
        'icon': '🌍',
    },
    'opinion_take': {
        'name': 'Opinion / Hot Take',
        'description': 'Personal opinion or provocative analysis',
        'keywords': ['i think', 'my view', 'opinion', 'here\'s the thing', 'let me be clear', 'controversial'],
        'icon': '💭',
    },
    'research_data': {
        'name': 'Research & Data',
        'description': 'Studies, statistics, and research findings',
        'keywords': ['study', 'research', 'data', 'survey', 'report', 'found that', 'percent', '%'],
        'icon': '📊',
    },
    'case_study': {
        'name': 'Case Study / Example',
        'description': 'Deep dive into a specific example or project',
        'keywords': ['case study', 'example', 'look at', 'consider', 'take the case'],
        'icon': '🔍',
    },
    'interview_quote': {
        'name': 'Interview / Expert Quote',
        'description': 'Quotes or insights from experts',
        'keywords': ['said', 'told me', 'according to', 'interview', 'spoke with', 'asked'],
        'icon': '🎤',
    },
    'regulation_legal': {
        'name': 'Regulation & Legal',
        'description': 'Policy, law, and regulatory updates',
        'keywords': ['regulation', 'law', 'legal', 'policy', 'eu ai act', 'government', 'court', 'lawsuit'],
        'icon': '⚖️',
    },
    'future_predictions': {
        'name': 'Future / Predictions',
        'description': 'What\'s coming next, predictions',
        'keywords': ['future', 'predict', 'will', 'going to', 'expect', '2025', '2026', 'next year'],
        'icon': '🔮',
    },
    'practical_advice': {
        'name': 'Practical Advice',
        'description': 'Actionable recommendations for readers',
        'keywords': ['should', 'recommend', 'advice', 'action', 'step', 'do this', 'try'],
        'icon': '✅',
    },
    'links_resources': {
        'name': 'Links & Resources',
        'description': 'External links and further reading',
        'keywords': ['link', 'read more', 'resource', 'further reading', 'check out', 'click'],
        'icon': '🔗',
    },
    'podcast_episode': {
        'name': 'Podcast Episode',
        'description': 'Podcast content or episode notes',
        'keywords': ['podcast', 'episode', 'listen', 'burn it down', 'audio'],
        'icon': '🎙️',
    },
    'event_conference': {
        'name': 'Event / Conference',
        'description': 'Conference coverage or event announcements',
        'keywords': ['conference', 'event', 'summit', 'forum', 'spoke at', 'attended'],
        'icon': '📅',
    },
    'call_to_action': {
        'name': 'Call to Action',
        'description': 'Engagement requests, subscriptions, sharing',
        'keywords': ['subscribe', 'share', 'forward', 'whatsapp', 'let me know', 'reply', 'comment'],
        'icon': '📣',
    },
    'develop_ai_updates': {
        'name': 'What\'s Happening at Develop AI',
        'description': 'Updates about Develop AI, upcoming events, projects',
        'keywords': ['develop ai', 'what is happening', 'what\'s happening', 'what\'s new', 'upcoming', 'working on', 'jamfest', 'innovation lab'],
        'icon': '🏠',
    },
    'closing_signoff': {
        'name': 'Closing / Sign-off',
        'description': 'The ending of the newsletter',
        'keywords': ['all the best', 'best', 'paul', 'thanks', 'until next', 'see you'],
        'icon': '👋',
    },
}


def load_newsletters() -> list[dict]:
    """Load all newsletters from the raw data file."""
    newsletters = []
    if RAW_DATA_FILE.exists():
        with open(RAW_DATA_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    newsletters.append(json.loads(line))
    return newsletters


def extract_sections_from_html(html: str) -> list[dict]:
    """
    Extract sections from newsletter HTML.
    Sections can be defined by:
    - H2 or H3 headings
    - Bold text at start of paragraphs (common pattern in Develop AI)
    - Dividers/horizontal rules
    """
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'lxml')
    
    sections = []
    current_section = None
    
    def is_section_header(elem) -> tuple[bool, str]:
        """Check if an element is a section header. Returns (is_header, heading_text)."""
        
        # H2/H3 are always section headers
        if elem.name in ['h2', 'h3']:
            return True, elem.get_text(strip=True)
        
        # Check for paragraphs that start with bold text (common pattern)
        if elem.name == 'p':
            # Check if paragraph starts with <strong> or contains mostly bold text
            strong = elem.find('strong')
            if strong:
                strong_text = strong.get_text(strip=True)
                full_text = elem.get_text(strip=True)
                
                # If the bold text is most of the paragraph, or ends with : or ?
                # it's likely a section header
                if len(strong_text) > 10 and (
                    len(strong_text) >= len(full_text) * 0.8 or
                    strong_text.endswith(':') or
                    strong_text.endswith('?') or
                    (full_text.startswith(strong_text) and len(strong_text) > 20)
                ):
                    return True, strong_text
        
        return False, ''
    
    # Process all relevant elements
    for elem in soup.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'blockquote', 'hr', 'div']):
        
        is_header, heading_text = is_section_header(elem)
        
        if is_header and heading_text:
            # Start a new section
            if current_section and current_section.get('content', '').strip():
                sections.append(current_section)
            
            current_section = {
                'heading': heading_text,
                'heading_level': elem.name if elem.name in ['h2', 'h3'] else 'bold',
                'content': '',
                'word_count': 0,
                'has_list': False,
                'has_links': False,
                'has_blockquote': False,
            }
        elif elem.name == 'hr':
            # Horizontal rule might indicate section break
            if current_section and current_section.get('content', '').strip():
                sections.append(current_section)
                current_section = None
        elif current_section:
            # Add content to current section
            text = elem.get_text(strip=True)
            if text:
                current_section['content'] += ' ' + text
                current_section['word_count'] += len(text.split())
                
                if elem.name in ['ul', 'ol']:
                    current_section['has_list'] = True
                if elem.find('a'):
                    current_section['has_links'] = True
                if elem.name == 'blockquote':
                    current_section['has_blockquote'] = True
        else:
            # Content before any heading - this is the intro/main story
            text = elem.get_text(strip=True)
            if text:
                if not current_section:
                    current_section = {
                        'heading': '[Main Story]',
                        'heading_level': 'intro',
                        'content': text,
                        'word_count': len(text.split()),
                        'has_list': elem.name in ['ul', 'ol'],
                        'has_links': bool(elem.find('a')),
                        'has_blockquote': elem.name == 'blockquote',
                    }
                else:
                    current_section['content'] += ' ' + text
                    current_section['word_count'] += len(text.split())
    
    # Don't forget the last section
    if current_section and current_section.get('content', '').strip():
        sections.append(current_section)
    
    return sections


def classify_section_type(section: dict) -> str:
    """
    Classify a section into one of the defined types.
    Returns the type key.
    """
    heading = section.get('heading', '').lower()
    content = section.get('content', '').lower()
    full_text = f"{heading} {content}"
    
    # Score each type
    scores = {}
    for type_key, type_def in SECTION_TYPE_KEYWORDS.items():
        score = 0
        for keyword in type_def['keywords']:
            if keyword.lower() in full_text:
                # Heading matches are worth more
                if keyword.lower() in heading:
                    score += 3
                else:
                    score += 1
        scores[type_key] = score
    
    # Get the best match
    best_type = max(scores, key=scores.get)
    
    # If no keywords matched, make educated guesses
    if scores[best_type] == 0:
        # Check if it's the intro
        if section.get('heading') == '[Introduction]':
            return 'main_story'
        
        # Check word count - long sections are usually main stories
        if section.get('word_count', 0) > 300:
            return 'main_story'
        
        # Short sections with links might be resources
        if section.get('has_links') and section.get('word_count', 0) < 100:
            return 'links_resources'
        
        # Default to main_story for unclassified
        return 'main_story'
    
    return best_type


def analyze_newsletter_structure(newsletter: dict) -> dict:
    """
    Analyze the section structure of a single newsletter.
    """
    title = newsletter.get('title', '')
    html = newsletter.get('content_html', '')
    
    sections = extract_sections_from_html(html)
    
    classified_sections = []
    for section in sections:
        section_type = classify_section_type(section)
        classified_sections.append({
            'heading': section['heading'],
            'type': section_type,
            'type_name': SECTION_TYPE_KEYWORDS.get(section_type, {}).get('name', 'Unknown'),
            'word_count': section['word_count'],
            'has_list': section['has_list'],
            'has_links': section['has_links'],
            'has_blockquote': section['has_blockquote'],
        })
    
    return {
        'title': title,
        'section_count': len(sections),
        'sections': classified_sections,
        'section_types': [s['type'] for s in classified_sections],
    }


def analyze_all_newsletters() -> dict:
    """
    Analyze section patterns across all newsletters.
    """
    print("Loading newsletters...")
    newsletters = load_newsletters()
    
    if not newsletters:
        print("No newsletters found")
        return {}
    
    print(f"Analyzing {len(newsletters)} newsletters...")
    
    all_analyses = []
    section_type_counter = Counter()
    section_sequences = []
    sections_by_type = defaultdict(list)
    
    for newsletter in newsletters:
        analysis = analyze_newsletter_structure(newsletter)
        all_analyses.append(analysis)
        
        # Count section types
        for section in analysis['sections']:
            section_type_counter[section['type']] += 1
            sections_by_type[section['type']].append({
                'heading': section['heading'],
                'word_count': section['word_count'],
                'newsletter': newsletter.get('title', '')[:50],
            })
        
        # Track section sequences
        if analysis['section_types']:
            section_sequences.append(analysis['section_types'])
    
    # Calculate statistics
    total_sections = sum(section_type_counter.values())
    
    section_stats = {}
    for section_type, count in section_type_counter.items():
        type_info = SECTION_TYPE_KEYWORDS.get(section_type, {})
        examples = sections_by_type.get(section_type, [])
        
        # Get unique heading examples
        unique_headings = list(set(s['heading'] for s in examples if s['heading'] != '[Introduction]'))[:10]
        
        section_stats[section_type] = {
            'name': type_info.get('name', section_type),
            'icon': type_info.get('icon', '📄'),
            'description': type_info.get('description', ''),
            'count': count,
            'percentage': round(count / total_sections * 100, 1),
            'newsletters_with': len([a for a in all_analyses if section_type in a['section_types']]),
            'example_headings': unique_headings,
            'avg_word_count': round(sum(s['word_count'] for s in examples) / len(examples), 0) if examples else 0,
        }
    
    # Find common section sequences (patterns)
    sequence_patterns = Counter()
    for seq in section_sequences:
        # Look at 2-section and 3-section patterns
        for i in range(len(seq) - 1):
            pair = tuple(seq[i:i+2])
            sequence_patterns[pair] += 1
        for i in range(len(seq) - 2):
            triple = tuple(seq[i:i+3])
            sequence_patterns[triple] += 1
    
    # Most common patterns
    common_patterns = []
    for pattern, count in sequence_patterns.most_common(15):
        if count >= 3:  # At least 3 occurrences
            pattern_names = [SECTION_TYPE_KEYWORDS.get(p, {}).get('name', p) for p in pattern]
            common_patterns.append({
                'pattern': list(pattern),
                'pattern_names': pattern_names,
                'count': count,
            })
    
    # Calculate typical newsletter structures
    section_counts = [a['section_count'] for a in all_analyses]
    
    result = {
        'newsletter_count': len(newsletters),
        'total_sections_analyzed': total_sections,
        'avg_sections_per_newsletter': round(sum(section_counts) / len(section_counts), 1),
        'min_sections': min(section_counts),
        'max_sections': max(section_counts),
        'section_types': section_stats,
        'common_patterns': common_patterns,
        'all_analyses': all_analyses,  # Keep for detailed lookup
    }
    
    return result


def save_analysis(analysis: dict):
    """Save the section analysis to file."""
    # Don't save the full analyses, too large
    save_data = {k: v for k, v in analysis.items() if k != 'all_analyses'}
    
    with open(SECTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)
    print(f"Saved to {SECTIONS_FILE}")


def load_analysis() -> dict:
    """Load the section analysis from file."""
    if not SECTIONS_FILE.exists():
        return {}
    with open(SECTIONS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_section_templates() -> list[dict]:
    """
    Get section templates for the generator UI.
    Returns a list of commonly used section types with their details.
    """
    analysis = load_analysis()
    
    if not analysis:
        return []
    
    templates = []
    section_types = analysis.get('section_types', {})
    
    # Sort by frequency
    sorted_types = sorted(
        section_types.items(),
        key=lambda x: x[1].get('count', 0),
        reverse=True
    )
    
    for type_key, type_data in sorted_types:
        if type_data.get('count', 0) >= 3:  # Only include common sections
            templates.append({
                'key': type_key,
                'name': type_data.get('name', type_key),
                'icon': type_data.get('icon', '📄'),
                'description': type_data.get('description', ''),
                'frequency': type_data.get('newsletters_with', 0),
                'percentage': type_data.get('percentage', 0),
                'example_headings': type_data.get('example_headings', []),
                'avg_word_count': type_data.get('avg_word_count', 200),
            })
    
    # Add Letter+ specific sections (always available)
    templates.append({
        'key': 'ai_transparency',
        'name': 'AI Transparency / How AI Helped',
        'icon': '🤖',
        'description': 'Explain how much AI was used in creating this newsletter - be transparent with readers',
        'frequency': 0,
        'percentage': 0,
        'example_headings': [
            'How AI helped write this newsletter',
            'AI Transparency: How this letter was made',
            'Behind the scenes: AI in this issue'
        ],
        'avg_word_count': 150,
        'category': 'meta',
    })
    
    templates.append({
        'key': 'letterplus_development',
        'name': 'Letter+ App Development',
        'icon': '🛠️',
        'description': 'Share what improvements were made to the Letter+ app while creating this newsletter',
        'frequency': 0,
        'percentage': 0,
        'example_headings': [
            'Letter+ development updates',
            'What I built in Letter+ this week',
            'App updates: Making Letter+ better'
        ],
        'avg_word_count': 200,
        'category': 'meta',
    })
    
    return templates


# ============================================================================
# Main
# ============================================================================

def run_analysis():
    """Run the full section analysis."""
    print("=" * 60)
    print("SECTION PATTERN ANALYZER")
    print("=" * 60)
    
    analysis = analyze_all_newsletters()
    
    if not analysis:
        print("No data to analyze")
        return None
    
    save_analysis(analysis)
    
    print(f"\n📊 Analyzed {analysis['newsletter_count']} newsletters")
    print(f"📑 Found {analysis['total_sections_analyzed']} total sections")
    print(f"📈 Average {analysis['avg_sections_per_newsletter']} sections per newsletter")
    print(f"   (Range: {analysis['min_sections']} - {analysis['max_sections']})")
    
    print("\n🏷️ SECTION TYPES (by frequency):")
    section_types = analysis.get('section_types', {})
    sorted_types = sorted(section_types.items(), key=lambda x: x[1]['count'], reverse=True)
    
    for type_key, type_data in sorted_types:
        icon = type_data.get('icon', '📄')
        name = type_data.get('name', type_key)
        count = type_data.get('count', 0)
        pct = type_data.get('percentage', 0)
        newsletters = type_data.get('newsletters_with', 0)
        
        print(f"\n  {icon} {name}")
        print(f"     Count: {count} ({pct}%)")
        print(f"     Appears in: {newsletters} newsletters")
        
        examples = type_data.get('example_headings', [])[:3]
        if examples:
            print(f"     Examples: {', '.join(examples[:3])}")
    
    print("\n🔄 COMMON SECTION SEQUENCES:")
    for pattern in analysis.get('common_patterns', [])[:8]:
        names = ' → '.join(pattern['pattern_names'])
        print(f"  {names} ({pattern['count']}x)")
    
    return analysis


if __name__ == "__main__":
    run_analysis()

