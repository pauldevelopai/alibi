"""
Newsletter Engine - The Complete Self-Improving Newsletter Generation System

This is the IDEAL architecture for newsletter generation:

1. PROMPT CONSTRUCTION (intelligent, adaptive)
   - Analyzes outline to understand what's needed
   - Semantic search for relevant facts (local embeddings - FREE)
   - Selects best RAG examples from past newsletters
   - Pulls targeted Bible sections for style
   - Structures prompt with attention to token position (important stuff first)

2. GENERATION (quality-focused)
   - GPT-4o for best quality
   - Fine-tuned model option for voice consistency
   - Configurable temperature and length

3. LEARNING LOOP (the key differentiator)
   - Tracks your edits to each draft
   - Identifies patterns in what you change
   - Automatically adjusts prompt construction
   - Over time: prompts get better, you edit less

Author: Paul McNally / Develop AI
"""

import json
import os
import re
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher, unified_diff

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Import our modules
try:
    from embeddings import (
        get_embedding,
        get_embeddings_batch,
        compute_similarity,
        SENTENCE_TRANSFORMERS_AVAILABLE,
    )
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from rag_system import retrieve_relevant_passages, load_embeddings
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

try:
    from knowledge_base import (
        semantic_search_facts,
        semantic_search_articles,
        get_relevant_facts,
        get_all_facts,
    )
    KB_AVAILABLE = True
except ImportError:
    KB_AVAILABLE = False

try:
    from style_analyzer import load_bible
    from deep_style_analyzer import load_deep_bible
    BIBLE_AVAILABLE = True
except ImportError:
    BIBLE_AVAILABLE = False

try:
    from fine_tuning import get_active_fine_tuned_model
    FINE_TUNING_AVAILABLE = True
except ImportError:
    FINE_TUNING_AVAILABLE = False

DATA_DIR = Path(__file__).parent / "data"
LEARNINGS_FILE = DATA_DIR / "prompt_learnings.json"
GENERATION_HISTORY_FILE = DATA_DIR / "generation_history.json"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class PromptComponents:
    """All components that go into a prompt."""
    outline: str
    facts: List[Dict]
    rag_examples: List[Dict]
    bible_sections: Dict
    deep_analysis: Dict
    learnings: List[str]
    
@dataclass
class GenerationResult:
    """Result of a newsletter generation."""
    id: str
    content: str
    prompt_components: Dict
    system_prompt: str
    user_prompt: str
    model: str
    metadata: Dict
    timestamp: str


# ============================================================================
# PART 1: INTELLIGENT PROMPT CONSTRUCTION
# ============================================================================

class PromptConstructor:
    """
    Intelligent prompt construction with:
    - Outline analysis
    - Semantic fact retrieval
    - RAG example selection
    - Bible section targeting
    - Token position optimization (important stuff first)
    """
    
    def __init__(self):
        self.bible = load_bible() if BIBLE_AVAILABLE else {}
        self.deep_bible = load_deep_bible() if BIBLE_AVAILABLE else {}
        self.learnings = self._load_learnings()
    
    def _load_learnings(self) -> Dict:
        """Load learned prompt improvements."""
        if LEARNINGS_FILE.exists():
            with open(LEARNINGS_FILE, 'r') as f:
                return json.load(f)
        return {
            'avoid_patterns': [],      # Things that led to edits
            'include_patterns': [],    # Things that improved output
            'section_weights': {},     # Which Bible sections matter most
            'fact_type_weights': {},   # Which fact types are used most
            'total_generations': 0,
            'total_edits_tracked': 0,
        }
    
    def analyze_outline(self, outline: str) -> Dict:
        """
        Use GPT-4o to deeply analyze the outline and extract:
        - Main topics for semantic search
        - Required fact types
        - Tone and style requirements
        - Structure expectations
        """
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at analyzing newsletter outlines to determine 
                    what context and information will be needed to write them well."""
                },
                {
                    "role": "user",
                    "content": f"""Analyze this newsletter outline and return a JSON object with:

1. "topics": List of 3-5 main topics/themes (for semantic search)
2. "search_queries": List of 5 specific search queries to find relevant facts
3. "fact_types_needed": List of fact types needed (statistics, quotes, examples, studies, etc.)
4. "tone": The intended tone (informative, urgent, celebratory, critical, etc.)
5. "sections": List of section names/types in the outline
6. "key_entities": Important people, companies, technologies mentioned
7. "context_priority": What context is MOST important for this specific piece

OUTLINE:
{outline}

Return ONLY valid JSON, no markdown formatting."""
                }
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        try:
            # Clean potential markdown formatting
            content = response.choices[0].message.content
            content = content.strip()
            if content.startswith('```'):
                content = re.sub(r'^```\w*\n?', '', content)
                content = re.sub(r'\n?```$', '', content)
            return json.loads(content)
        except:
            return {
                'topics': [outline[:100]],
                'search_queries': [outline[:100]],
                'fact_types_needed': ['statistics', 'examples'],
                'tone': 'informative',
                'sections': [],
                'key_entities': [],
                'context_priority': 'general'
            }
    
    def get_relevant_facts(self, analysis: Dict, max_facts: int = 12) -> List[Dict]:
        """
        Get facts using semantic search, prioritized by the outline analysis.
        """
        if not KB_AVAILABLE:
            return []
        
        all_facts = []
        seen = set()
        
        # Search for each query from the analysis
        queries = analysis.get('search_queries', [])
        fact_types = analysis.get('fact_types_needed', [])
        
        for query in queries[:5]:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                facts = semantic_search_facts(query, limit=5, min_similarity=0.25)
            else:
                facts = get_relevant_facts(query, max_facts=5)
            
            for fact in facts:
                # Facts use 'text' key, not 'fact_text'
                fact_id = fact.get('id', hash(fact.get('text', '')))
                if fact_id not in seen:
                    seen.add(fact_id)
                    # Boost score if fact type matches what's needed
                    if fact.get('fact_type') in fact_types:
                        fact['relevance_boost'] = 1.5
                    all_facts.append(fact)
        
        # Sort by relevance (with boost)
        all_facts.sort(
            key=lambda f: f.get('similarity', 0) * f.get('relevance_boost', 1.0),
            reverse=True
        )
        
        return all_facts[:max_facts]
    
    def get_rag_examples(self, analysis: Dict, max_examples: int = 5) -> List[Dict]:
        """
        Get relevant passages from past newsletters using semantic search.
        """
        if not RAG_AVAILABLE:
            return []
        
        examples = []
        seen_titles = set()
        
        # Search using topics from analysis
        topics = analysis.get('topics', [])
        
        for topic in topics[:3]:
            passages = retrieve_relevant_passages(topic, top_k=3, min_similarity=0.3)
            for p in passages:
                if p['title'] not in seen_titles:
                    seen_titles.add(p['title'])
                    examples.append(p)
        
        # Sort by similarity and return top examples
        examples.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        return examples[:max_examples]
    
    def get_targeted_bible_sections(self, analysis: Dict) -> Dict:
        """
        Pull specific Bible sections based on what this outline needs.
        Not everything - just what's relevant.
        """
        if not self.bible:
            return {}
        
        targeted = {}
        tone = analysis.get('tone', 'informative')
        sections_needed = analysis.get('sections', [])
        
        # Always include core voice elements
        if 'writing_voice' in self.bible:
            voice = self.bible['writing_voice']
            targeted['voice'] = {
                'tone': voice.get('tone_descriptors', [])[:5],
                'perspective': voice.get('perspective', ''),
                'signature_phrases': voice.get('signature_phrases', [])[:5],
            }
        
        # Include section-specific patterns if available
        if 'section_patterns' in self.bible:
            patterns = self.bible['section_patterns']
            
            # Match outline sections to Bible patterns
            for section in sections_needed:
                section_lower = section.lower()
                if 'intro' in section_lower or 'open' in section_lower:
                    if 'intro_patterns' in patterns:
                        targeted['intro_examples'] = patterns['intro_patterns'][:2]
                elif 'close' in section_lower or 'end' in section_lower:
                    if 'closing_patterns' in patterns:
                        targeted['closing_examples'] = patterns['closing_patterns'][:2]
        
        # Include signature elements
        if 'signature_elements' in self.bible:
            targeted['signatures'] = self.bible['signature_elements']
        
        # Add deep analysis insights if available
        if self.deep_bible:
            if 'vocabulary' in self.deep_bible:
                targeted['signature_words'] = self.deep_bible['vocabulary'].get('signature_words', [])[:10]
            if 'sentences' in self.deep_bible:
                targeted['sentence_style'] = {
                    'avg_length': self.deep_bible['sentences'].get('average_sentence_length'),
                    'question_frequency': self.deep_bible['sentences'].get('question_frequency'),
                }
            if 'semantic' in self.deep_bible:
                targeted['representative_sentences'] = self.deep_bible['semantic'].get('most_representative_sentences', [])[:3]
        
        return targeted
    
    def get_applicable_learnings(self, analysis: Dict) -> List[str]:
        """
        Get learnings that apply to this specific outline.
        """
        applicable = []
        
        # Check for patterns that match this outline's characteristics
        tone = analysis.get('tone', '')
        topics = analysis.get('topics', [])
        
        for learning in self.learnings.get('include_patterns', []):
            # Check if learning applies to this type of content
            if learning.get('applies_to_tone') == tone or not learning.get('applies_to_tone'):
                applicable.append(learning.get('instruction', ''))
        
        # Add avoidance instructions
        for avoid in self.learnings.get('avoid_patterns', []):
            applicable.append(f"AVOID: {avoid.get('pattern', '')}")
        
        return applicable[:5]  # Limit to top 5 learnings
    
    def build_prompt(
        self,
        outline: str,
        target_length: int = 800,
        outline_sources: List[Dict] = None,
        style_metrics: Dict = None
    ) -> Tuple[str, str, Dict]:
        """
        Build the optimal prompt with intelligent context selection
        and token position optimization.
        
        TOKEN POSITION STRATEGY:
        - System prompt: Voice/style (always attended to)
        - User prompt start: Most relevant examples (high attention)
        - User prompt middle: Facts and context
        - User prompt end: Outline and instructions (high attention for tasks)
        """
        # Step 1: Analyze the outline
        analysis = self.analyze_outline(outline)
        
        # Step 2: Gather relevant context
        facts = self.get_relevant_facts(analysis)
        rag_examples = self.get_rag_examples(analysis)
        bible_sections = self.get_targeted_bible_sections(analysis)
        learnings = self.get_applicable_learnings(analysis)
        
        # Step 3: Build system prompt (voice/identity)
        system_prompt = self._build_system_prompt(bible_sections, learnings, style_metrics or {})
        
        # Step 4: Build user prompt with token position optimization
        user_prompt = self._build_user_prompt(
            outline=outline,
            facts=facts,
            rag_examples=rag_examples,
            bible_sections=bible_sections,
            target_length=target_length,
            analysis=analysis,
            outline_sources=outline_sources or []
        )
        
        # Step 5: Collect metadata
        metadata = {
            'analysis': analysis,
            'facts_count': len(facts),
            'rag_examples_count': len(rag_examples),
            'bible_sections': list(bible_sections.keys()),
            'learnings_applied': len(learnings),
            'timestamp': datetime.now().isoformat(),
            'embedding_source': 'sentence-transformers (local)' if SENTENCE_TRANSFORMERS_AVAILABLE else 'none',
        }
        
        return system_prompt, user_prompt, metadata
    
    def _build_system_prompt(self, bible: Dict, learnings: List[str], style_metrics: Dict) -> str:
        """Build the system prompt with voice and identity."""
        
        prompt = """You are Paul McNally, writing your "Develop AI" newsletter for newsrooms and content creators in Africa and Asia.

## YOUR VOICE AND STYLE
"""
        # Add voice characteristics
        if 'voice' in bible:
            voice = bible['voice']
            if voice.get('tone'):
                prompt += f"Tone: {', '.join(voice['tone'])}\n"
            if voice.get('perspective'):
                prompt += f"Perspective: {voice['perspective']}\n"
            if voice.get('signature_phrases'):
                prompt += f"Signature phrases you use: {', '.join(voice['signature_phrases'])}\n"
        
        # Add signature words
        if 'signature_words' in bible:
            prompt += f"\nWords you frequently use: {', '.join(bible['signature_words'])}\n"
        
        # Add representative sentences
        if 'representative_sentences' in bible:
            prompt += "\nExamples of your typical sentences:\n"
            for sent in bible['representative_sentences']:
                prompt += f'- "{sent[:100]}..."\n'

        # Add structure and formulas
        if 'structure_patterns' in bible:
            prompt += "\n## HOW YOU STRUCTURE A NEWSLETTER\n"
            patterns = bible['structure_patterns']
            if patterns.get('typical_sections'):
                prompt += f"- Typical sections: {', '.join(patterns['typical_sections'][:6])}\n"
            if patterns.get('opening_style'):
                prompt += f"- Openings: {patterns['opening_style']}\n"
            if patterns.get('closing_style'):
                prompt += f"- Closings: {patterns['closing_style']}\n"

        if 'headline_formulas' in bible:
            prompt += "\nHeadline patterns that work for you:\n"
            for formula, data in list(bible['headline_formulas'].items())[:4]:
                example = data.get('examples', [''])[0] if isinstance(data, dict) else ''
                prompt += f"- {formula}: e.g., \"{example}\" \n"

        if 'rules_for_success' in bible:
            prompt += "\nRules that drive performance (follow these):\n"
            for rule in bible['rules_for_success'][:6]:
                prompt += f"- {rule}\n"

        if 'cliches_to_avoid' in bible:
            prompt += "\nCliches and weak phrases to avoid:\n"
            prompt += ", ".join(bible['cliches_to_avoid'][:10]) + "\n"

        if 'cta_patterns' in bible:
            prompt += "\nCalls-to-action that fit your voice:\n"
            prompt += "; ".join(bible['cta_patterns'][:4]) + "\n"

        # Africa/Global South emphasis
        # Africa/Global South emphasis ONLY when style controls request it
        africa_dial = style_metrics.get('africa_focus', 50)
        global_south_dial = style_metrics.get('global_south_focus', 50)
        if (africa_dial > 65 or global_south_dial > 65) and 'topic_strategy' in bible:
            themes = bible['topic_strategy'].get('primary_themes', [])
            if themes:
                prompt += "\nAfrica/Global South focus (dial enabled):\n"
                prompt += ", ".join(themes[:6]) + "\n"
        
        # Add learned instructions
        if learnings:
            prompt += "\n## LEARNED PREFERENCES (from your past edits)\n"
            for learning in learnings:
                prompt += f"- {learning}\n"
        
        prompt += """
## CRITICAL RULES
1. Write EXACTLY like Paul - match the voice and examples above
2. Be conversational but informative
3. Include practical, actionable takeaways
4. Reference sources when using facts (include links)
5. Keep the energy authentic - not hype, not dry
"""
        return prompt
    
    def _build_user_prompt(
        self,
        outline: str,
        facts: List[Dict],
        rag_examples: List[Dict],
        bible_sections: Dict,
        target_length: int,
        analysis: Dict,
        outline_sources: List[Dict]
    ) -> str:
        """
        Build user prompt with TOKEN POSITION OPTIMIZATION.
        
        Structure (attention pattern):
        [HIGH] Examples from past writing (match this!)
        [MED]  Relevant facts to incorporate
        [HIGH] The outline to follow
        [HIGH] Final instructions
        """
        prompt = ""
        
        # SECTION 1: RAG Examples (HIGH attention - at start)
        if rag_examples:
            prompt += "# EXAMPLES FROM YOUR PAST NEWSLETTERS\n"
            prompt += "Match this voice and style EXACTLY:\n\n"
            for i, ex in enumerate(rag_examples[:3], 1):
                # Chunks use 'newsletter_title' not 'title'
                title = ex.get('newsletter_title', ex.get('title', 'Past Newsletter'))
                text = ex.get('text', '')[:500]
                prompt += f"---\n"
                prompt += f"From: \"{title}\"\n"
                prompt += f"{text}...\n\n"
            prompt += "---\n\n"
        
        # SECTION 2: Intro examples from Bible (if available)
        if 'intro_examples' in bible_sections:
            prompt += "# HOW YOU TYPICALLY START\n"
            for intro in bible_sections['intro_examples'][:2]:
                prompt += f'- "{intro[:150]}..."\n'
            prompt += "\n"
        
        # SECTION 3: Facts and Data (MEDIUM attention - middle)
        if outline_sources:
            prompt += "# PROVIDED SOURCES (must cite if used)\n\n"
            for src in outline_sources:
                if isinstance(src, dict):
                    title = src.get('title', 'Source')
                    url = src.get('url', '')
                    pub = src.get('publication', src.get('source', ''))
                    date = src.get('date', '')
                    prompt += f"- {title}"
                    if url:
                        prompt += f": {url}"
                    if pub or date:
                        prompt += f" ({', '.join([x for x in [pub, date] if x])})"
                    prompt += "\n"
            prompt += "\n"

        if facts:
            prompt += "# FACTS AND DATA TO USE (cite sources!)\n\n"
            for i, fact in enumerate(facts[:8], 1):
                # Facts use 'text' key, not 'fact_text'
                fact_text = fact.get('text', fact.get('fact_text', ''))
                source = fact.get('source_title', fact.get('source_name', 'Unknown'))
                url = fact.get('source_url', fact.get('citation', ''))
                
                prompt += f"{i}. {fact_text}\n"
                prompt += f"   Source: {source}"
                if url:
                    prompt += f" ({url})"
                prompt += "\n\n"
        
        # SECTION 4: The Outline (HIGH attention - near end)
        prompt += "# THE NEWSLETTER TO WRITE\n\n"
        prompt += outline
        prompt += "\n\n"
        
        # SECTION 5: Final Instructions (HIGH attention - at end)
        prompt += "# INSTRUCTIONS\n\n"
        prompt += f"1. Write approximately {target_length} words\n"
        prompt += "2. Follow the outline structure exactly\n"
        prompt += "3. Match the voice from the examples above\n"
        prompt += "4. Incorporate relevant facts with citations\n"
        prompt += "5. Make it engaging and practical\n"
        
        if analysis.get('tone'):
            prompt += f"6. Maintain a {analysis['tone']} tone throughout\n"
        
        return prompt


# ============================================================================
# PART 2: GENERATION
# ============================================================================

class NewsletterGenerator:
    """
    Generate newsletters with quality-first approach.
    - GPT-4o for best quality
    - Fine-tuned model option for voice consistency
    """
    
    def __init__(self):
        self.prompt_constructor = PromptConstructor()
        self.fine_tuned_model = self._get_fine_tuned_model()
    
    def build_prompt_from_outline_data(
        self,
        outline_data: Dict,
        idea: str = "",
        style_metrics: Dict = None,
        story_type_data: Dict = None
    ) -> Tuple[str, str, Dict]:
        """
        Build an intelligent prompt from the Write tab's structured outline_data.
        
        This converts the outline_data format to a text outline, then uses
        the intelligent prompt construction with:
        - Semantic fact search
        - RAG examples from past newsletters
        - Targeted Bible sections
        - Learnings from past edits
        
        Args:
            outline_data: Structured outline from Write tab
            idea: The original idea/topic
            style_metrics: The 22 style dial values
            story_type_data: Story type characteristics
        
        Returns:
            Tuple of (system_prompt, user_prompt, metadata)
        """
        # Convert structured outline_data to text format
        outline_text = self._outline_data_to_text(outline_data, idea, style_metrics, story_type_data)
        
        # Calculate target word count from outline_data
        main_words = outline_data.get('main_story', {}).get('target_word_count', 500)
        section_words = sum(s.get('target_word_count', 150) for s in outline_data.get('additional_sections', []))
        target_length = main_words + section_words + 100  # Buffer for intro/outro
        
        # Use the intelligent prompt builder
        system_prompt, user_prompt, metadata = self.prompt_constructor.build_prompt(
            outline=outline_text,
            target_length=target_length,
            outline_sources=outline_data.get('sources', []),
            style_metrics=style_metrics
        )
        
        # Add outline_data specific info to metadata
        metadata['headline'] = outline_data.get('headline', '')
        metadata['preview'] = outline_data.get('preview', '')
        metadata['target_word_count'] = target_length
        metadata['sources_provided'] = len(outline_data.get('sources', []))
        
        return system_prompt, user_prompt, metadata
    
    def _outline_data_to_text(
        self,
        outline_data: Dict,
        idea: str,
        style_metrics: Dict = None,
        story_type_data: Dict = None
    ) -> str:
        """Convert structured outline_data to text format for analysis."""
        
        text = f"# {outline_data.get('headline', idea)}\n\n"
        text += f"*{outline_data.get('preview', '')}*\n\n"
        if idea:
            text += f"Original idea/context: {idea}\n\n"
        
        # Opening hook
        if outline_data.get('opening_hook'):
            text += f"## Opening Hook\n{outline_data['opening_hook']}\n\n"
        
        # Main story
        main = outline_data.get('main_story', {})
        if main:
            text += f"## Main Story: {main.get('heading', 'Main Section')}\n"
            text += f"Target: {main.get('target_word_count', 500)} words\n\n"
            text += "Key Points:\n"
            for point in main.get('key_points', []):
                text += f"- {point}\n"
            if main.get('user_notes'):
                text += f"\nNotes: {main['user_notes']}\n"
            text += "\n"
        
        # Additional sections
        for section in outline_data.get('additional_sections', []):
            text += f"## {section.get('heading', 'Section')}\n"
            text += f"Target: {section.get('target_word_count', 150)} words\n\n"
            for bp in section.get('bullet_points', []):
                if bp.strip():
                    text += f"- {bp}\n"
            if section.get('user_notes'):
                text += f"\nNotes: {section['user_notes']}\n"
            text += "\n"
        
        # Sources
        sources = outline_data.get('sources', [])
        if sources:
            text += "## Sources\n"
            for s in sources:
                text += f"- {s.get('title', 'Source')}: {s.get('url', '')}\n"
            text += "\n"
        
        # Style metrics summary
        if style_metrics:
            high_metrics = [k for k, v in style_metrics.items() if v > 70]
            if high_metrics:
                text += f"## Style Focus\nEmphasize: {', '.join(high_metrics[:5])}\n\n"
        
        # Story type
        if story_type_data:
            text += f"## Story Type: {story_type_data.get('name', 'Standard')}\n"
            text += f"{story_type_data.get('description', '')}\n\n"
        
        return text
    
    def _get_fine_tuned_model(self) -> Optional[str]:
        """Get the active fine-tuned model if available."""
        if FINE_TUNING_AVAILABLE:
            try:
                return get_active_fine_tuned_model()
            except:
                pass
        return None
    
    def generate(
        self,
        outline: str,
        target_length: int = 800,
        model: str = "gpt-4o",
        use_fine_tuned: bool = False,
        temperature: float = 0.7
    ) -> GenerationResult:
        """
        Generate a newsletter section.
        
        Args:
            outline: The newsletter outline
            target_length: Target word count
            model: Base model to use
            use_fine_tuned: Whether to use fine-tuned model
            temperature: Generation temperature
        """
        # Build optimal prompt
        system_prompt, user_prompt, metadata = self.prompt_constructor.build_prompt(
            outline=outline,
            target_length=target_length
        )
        
        # Determine model
        if use_fine_tuned and self.fine_tuned_model:
            generation_model = self.fine_tuned_model
            metadata['model_type'] = 'fine-tuned'
        else:
            generation_model = model
            metadata['model_type'] = 'base'
        
        # Generate
        response = client.chat.completions.create(
            model=generation_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=target_length * 2
        )
        
        content = response.choices[0].message.content
        
        # Create result
        generation_id = hashlib.md5(
            f"{outline}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        result = GenerationResult(
            id=generation_id,
            content=content,
            prompt_components=metadata,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=generation_model,
            metadata={
                'output_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
                'output_words': len(content.split()),
                'temperature': temperature,
            },
            timestamp=datetime.now().isoformat()
        )
        
        # Save to history for learning
        self._save_generation(result)
        
        return result
    
    def _save_generation(self, result: GenerationResult):
        """Save generation to history for learning loop."""
        history = []
        if GENERATION_HISTORY_FILE.exists():
            try:
                with open(GENERATION_HISTORY_FILE, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        history.append(asdict(result))
        
        # Keep last 100 generations
        history = history[-100:]
        
        DATA_DIR.mkdir(exist_ok=True)
        with open(GENERATION_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)


# ============================================================================
# PART 3: LEARNING LOOP
# ============================================================================

class LearningLoop:
    """
    Track edits and improve prompt construction over time.
    
    The key insight: by tracking what you change in drafts,
    we can learn what the prompt should have included or avoided.
    """
    
    def __init__(self):
        self.learnings = self._load_learnings()
    
    def _load_learnings(self) -> Dict:
        """Load existing learnings."""
        if LEARNINGS_FILE.exists():
            with open(LEARNINGS_FILE, 'r') as f:
                return json.load(f)
        return {
            'avoid_patterns': [],
            'include_patterns': [],
            'section_weights': {},
            'fact_type_weights': {},
            'edit_history': [],
            'total_generations': 0,
            'total_edits_tracked': 0,
        }
    
    def _save_learnings(self):
        """Save learnings to file."""
        DATA_DIR.mkdir(exist_ok=True)
        with open(LEARNINGS_FILE, 'w') as f:
            json.dump(self.learnings, f, indent=2)
    
    def track_edit(
        self,
        generation_id: str,
        original: str,
        edited: str,
        notes: str = ""
    ) -> Dict:
        """
        Track an edit and extract learnings.
        
        Args:
            generation_id: ID of the generation that was edited
            original: The original generated content
            edited: The edited/final content
            notes: Optional notes about why changes were made
        
        Returns:
            Analysis of the edit with extracted learnings
        """
        # Calculate edit metrics
        similarity = SequenceMatcher(None, original, edited).ratio()
        edit_distance = 1 - similarity
        
        # Get the diff
        original_lines = original.split('\n')
        edited_lines = edited.split('\n')
        diff = list(unified_diff(original_lines, edited_lines, lineterm=''))
        
        # Analyze what changed
        additions = [line[1:] for line in diff if line.startswith('+') and not line.startswith('+++')]
        removals = [line[1:] for line in diff if line.startswith('-') and not line.startswith('---')]
        
        # Use AI to extract learnings
        learnings = self._extract_learnings(original, edited, additions, removals, notes)
        
        # Store the edit
        edit_record = {
            'generation_id': generation_id,
            'timestamp': datetime.now().isoformat(),
            'edit_distance': edit_distance,
            'similarity': similarity,
            'additions_count': len(additions),
            'removals_count': len(removals),
            'notes': notes,
            'learnings': learnings,
        }
        
        self.learnings['edit_history'].append(edit_record)
        self.learnings['total_edits_tracked'] += 1
        
        # Apply learnings
        self._apply_learnings(learnings)
        
        # Save
        self._save_learnings()
        
        return {
            'edit_distance': edit_distance,
            'similarity': similarity,
            'changes': {
                'additions': len(additions),
                'removals': len(removals),
            },
            'learnings_extracted': learnings,
        }
    
    def _extract_learnings(
        self,
        original: str,
        edited: str,
        additions: List[str],
        removals: List[str],
        notes: str
    ) -> Dict:
        """Use AI to extract learnings from the edit."""
        
        # Prepare context for AI analysis
        additions_text = '\n'.join(additions[:20])  # Limit for token efficiency
        removals_text = '\n'.join(removals[:20])
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You analyze newsletter edits to extract learnings for future generation.
                    Your goal: identify patterns that should be encouraged or avoided in future prompts."""
                },
                {
                    "role": "user",
                    "content": f"""Analyze this edit and extract learnings.

## CONTENT THAT WAS REMOVED (the AI wrote this but it was cut):
{removals_text[:2000]}

## CONTENT THAT WAS ADDED (the human added this):
{additions_text[:2000]}

## EDITOR'S NOTES:
{notes if notes else 'No notes provided'}

Return JSON with:
1. "avoid_instructions": List of specific things to avoid in future (based on what was removed)
2. "include_instructions": List of things to include in future (based on what was added)
3. "style_observations": Any style patterns noticed
4. "content_gaps": What content was missing that the human had to add
5. "quality_issues": Any quality issues that led to removals

Return ONLY valid JSON."""
                }
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        try:
            content = response.choices[0].message.content
            content = content.strip()
            if content.startswith('```'):
                content = re.sub(r'^```\w*\n?', '', content)
                content = re.sub(r'\n?```$', '', content)
            return json.loads(content)
        except:
            return {
                'avoid_instructions': [],
                'include_instructions': [],
                'style_observations': [],
                'content_gaps': [],
                'quality_issues': [],
            }
    
    def _apply_learnings(self, learnings: Dict):
        """Apply extracted learnings to improve future prompts."""
        
        # Add avoid patterns
        for avoid in learnings.get('avoid_instructions', []):
            if avoid and avoid not in [p.get('pattern') for p in self.learnings['avoid_patterns']]:
                self.learnings['avoid_patterns'].append({
                    'pattern': avoid,
                    'added': datetime.now().isoformat(),
                    'frequency': 1,
                })
        
        # Add include patterns
        for include in learnings.get('include_instructions', []):
            if include:
                self.learnings['include_patterns'].append({
                    'instruction': include,
                    'added': datetime.now().isoformat(),
                })
        
        # Keep lists manageable (most recent/frequent)
        self.learnings['avoid_patterns'] = self.learnings['avoid_patterns'][-20:]
        self.learnings['include_patterns'] = self.learnings['include_patterns'][-20:]
    
    def get_improvement_summary(self) -> Dict:
        """Get a summary of how the system has improved."""
        if not self.learnings['edit_history']:
            return {'message': 'No edits tracked yet'}
        
        edit_distances = [e['edit_distance'] for e in self.learnings['edit_history']]
        
        # Calculate improvement over time
        if len(edit_distances) >= 5:
            first_5_avg = sum(edit_distances[:5]) / 5
            last_5_avg = sum(edit_distances[-5:]) / 5
            improvement = ((first_5_avg - last_5_avg) / first_5_avg) * 100 if first_5_avg > 0 else 0
        else:
            improvement = 0
        
        return {
            'total_edits_tracked': len(edit_distances),
            'average_edit_distance': sum(edit_distances) / len(edit_distances),
            'improvement_percentage': improvement,
            'avoid_patterns_learned': len(self.learnings['avoid_patterns']),
            'include_patterns_learned': len(self.learnings['include_patterns']),
            'recent_edit_distances': edit_distances[-5:],
        }


# ============================================================================
# UNIFIED INTERFACE: Newsletter Engine
# ============================================================================

class NewsletterEngine:
    """
    The complete self-improving newsletter generation system.
    
    Usage:
        engine = NewsletterEngine()
        
        # Generate a newsletter
        result = engine.generate(outline, target_length=800)
        
        # After you edit it, track the changes
        engine.track_edit(result.id, result.content, edited_content)
        
        # Over time, the system learns and improves
        summary = engine.get_improvement_summary()
    """
    
    def __init__(self):
        self.generator = NewsletterGenerator()
        self.learning_loop = LearningLoop()
    
    def generate(
        self,
        outline: str,
        target_length: int = 800,
        model: str = "gpt-4o",
        use_fine_tuned: bool = False,
        temperature: float = 0.7
    ) -> GenerationResult:
        """
        Generate a newsletter using the intelligent prompt system.
        
        Args:
            outline: Your newsletter outline
            target_length: Target word count
            model: Model to use (default: gpt-4o for quality)
            use_fine_tuned: Use your fine-tuned model instead
            temperature: Creativity level (0.0-1.0)
        
        Returns:
            GenerationResult with content and metadata
        """
        return self.generator.generate(
            outline=outline,
            target_length=target_length,
            model=model,
            use_fine_tuned=use_fine_tuned,
            temperature=temperature
        )
    
    def track_edit(
        self,
        generation_id: str,
        original: str,
        edited: str,
        notes: str = ""
    ) -> Dict:
        """
        Track your edits to improve future generations.
        
        Call this after you've edited a generated newsletter.
        The system will learn from your changes.
        
        Args:
            generation_id: The ID from the GenerationResult
            original: The original generated content
            edited: Your edited version
            notes: Optional notes about why you made changes
        
        Returns:
            Analysis of the edit and extracted learnings
        """
        return self.learning_loop.track_edit(
            generation_id=generation_id,
            original=original,
            edited=edited,
            notes=notes
        )
    
    def get_improvement_summary(self) -> Dict:
        """Get a summary of how the system has improved over time."""
        return self.learning_loop.get_improvement_summary()
    
    def get_status(self) -> Dict:
        """Get status of all system components."""
        return {
            'embeddings': {
                'available': EMBEDDINGS_AVAILABLE,
                'sentence_transformers': SENTENCE_TRANSFORMERS_AVAILABLE,
            },
            'rag': {
                'available': RAG_AVAILABLE,
            },
            'knowledge_base': {
                'available': KB_AVAILABLE,
            },
            'bible': {
                'available': BIBLE_AVAILABLE,
            },
            'fine_tuning': {
                'available': FINE_TUNING_AVAILABLE,
                'model': self.generator.fine_tuned_model,
            },
            'learning': self.get_improvement_summary(),
        }


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 NEWSLETTER ENGINE - Self-Improving Generation System")
    print("=" * 70)
    
    engine = NewsletterEngine()
    
    # Show status
    status = engine.get_status()
    print("\n📊 System Status:")
    print(f"   Embeddings: {'✅' if status['embeddings']['available'] else '❌'}")
    print(f"   Sentence Transformers: {'✅' if status['embeddings']['sentence_transformers'] else '❌'}")
    print(f"   RAG System: {'✅' if status['rag']['available'] else '❌'}")
    print(f"   Knowledge Base: {'✅' if status['knowledge_base']['available'] else '❌'}")
    print(f"   Newsletter Bible: {'✅' if status['bible']['available'] else '❌'}")
    print(f"   Fine-tuned Model: {status['fine_tuning']['model'] or 'None'}")
    
    # Show learning status
    learning = status['learning']
    print("\n📈 Learning Status:")
    if 'message' in learning:
        print(f"   {learning['message']}")
    else:
        print(f"   Edits tracked: {learning['total_edits_tracked']}")
        print(f"   Avoid patterns learned: {learning['avoid_patterns_learned']}")
        print(f"   Include patterns learned: {learning['include_patterns_learned']}")
        if learning['improvement_percentage']:
            print(f"   Improvement: {learning['improvement_percentage']:.1f}%")
    
    print("\n" + "=" * 70)
    print("Ready to generate! Use: engine.generate(outline)")
    print("=" * 70)
