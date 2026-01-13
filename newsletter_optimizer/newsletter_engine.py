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
from dataclasses import dataclass, asdict, field
from difflib import SequenceMatcher, unified_diff

from dotenv import load_dotenv
from openai import OpenAI
from topic_signature import build_topic_signature
from relevance_filter import filter_editorial_sources_by_topic, score_source_relevance

# Config: Topic relevance and fact filtering
KB_MIN_RELEVANCE_SCORE = 3.0  # Increased from 2.0 for stricter filtering
FACT_MIN_RELEVANCE_SCORE = 3.0  # Increased from 2.0 for stricter filtering
OPTIONAL_CONTEXT_FACTS_MAX = 1
ALLOW_EMPTY_KB_IF_PROVIDED_SOURCES = True

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

@dataclass
class RequiredInputCoverage:
    input_type: str
    must_use: bool = True
    description: str = ""
    allocated_sections: List[str] = field(default_factory=list)


@dataclass
class StyleProfile:
    tone: str = ""
    pacing: str = ""
    stance: str = ""
    taboos: List[str] = field(default_factory=list)
    style_tokens: List[str] = field(default_factory=list)


@dataclass
class NewsletterSection:
    id: str
    name: str
    goal: str
    word_count: int
    sources_needed_min: int = 0
    source_anchor_requirements: List[str] = field(default_factory=list)


@dataclass
class NewsletterPlan:
    theme: str
    audience: str
    purpose: str
    angle_choices: List[str]
    required_inputs_coverage: List[RequiredInputCoverage]
    style_profile: StyleProfile
    sections: List[NewsletterSection]
    call_to_action: str
    fact_risk_flags: List[str]
    outline_text: str
    target_length: int
    provided_sources_count: int = 0
    must_use_provided_sources_min: int = 1
    compiler_outline: Optional["CompilerOutline"] = None


@dataclass
class RetrievalExcerpt:
    id: str
    text: str = ""
    source: str = ""
    url: str = ""
    source_type: str = ""
    use_as: str = ""
    fingerprint_terms: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompilerKeyPoint:
    id: str
    text: str
    kind: str  # FACT | INTERPRETATION | VOICE_MOVE | CTA
    priority: int = 1
    needs_citation: bool = False
    suggested_sources: List[str] = field(default_factory=list)


@dataclass
class CompilerOutline:
    headline: str
    preview: str
    opening_hook: str
    central_question: str
    stance: str
    target_word_count: int
    story_type: str
    sections: List[Dict[str, Any]]
    must_include_points: List[str]
    avoid_points: List[str]
    source_pool_refs: List[Dict[str, Any]]
    kb_pool_refs: List[Dict[str, Any]]
    ui_artifacts_to_ignore: List[str] = field(default_factory=list)


@dataclass
class VoicePattern:
    pattern_type: str  # opening_hook | analytical_turn | moral_frame | rhetorical_question | closing_move
    description: str
    example_paraphrase: str
    when_to_use: str


# Source typing
class SourceType:
    EDITORIAL_EVIDENCE = "EDITORIAL_EVIDENCE"
    PERSONAL_CONTEXT = "PERSONAL_CONTEXT"
    MARKETING = "MARKETING"
    PLATFORM_BOILERPLATE = "PLATFORM_BOILERPLATE"


@dataclass
class RetrievalPack:
    excerpts: List[RetrievalExcerpt]


@dataclass
class AnchoredBullet:
    text: str
    anchors: List[str]
    intent: str


@dataclass
class AnchoredSection:
    section_id: str
    bullets: List[AnchoredBullet]


@dataclass
class AnchoredOutline:
    sections: List[AnchoredSection]


@dataclass
class RelevanceItem:
    id: str
    source_type: str  # past_newsletter | newsletter_bible | knowledge_base | provided_source | facts
    source_id: str
    title: str
    summary: str
    why_relevant: str
    use_as: str  # hook|lens|analogy|argument|counterpoint|context|example|closing|cta|voice_move
    keywords: List[str] = field(default_factory=list)
    confidence: float = 0.5


@dataclass
class RelevanceBrief:
    theme: str
    angles: List[str]
    selected_items: List[RelevanceItem]
    exclusions: List[str]
    selection_stats: Dict[str, Any]


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

    # ------------------------------------------------------------------
    # Voice pattern extraction (no raw text leakage)
    # ------------------------------------------------------------------
    def extract_voice_patterns(self, past_newsletters: List[Dict]) -> List[VoicePattern]:
        patterns = []
        pattern_cycle = [
            "opening_hook",
            "analytical_turn",
            "moral_frame",
            "rhetorical_question",
            "closing_move",
        ]
        forbidden = ["subscribe", "follow", "sign up", "scroll", "http", "www", ".com", "$"]

        for idx, nl in enumerate(past_newsletters):
            title = nl.get('newsletter_title', nl.get('title', f"Past {idx+1}"))
            pattern_type = pattern_cycle[idx % len(pattern_cycle)]
            desc = f"A {pattern_type.replace('_',' ')} built around {title}"
            paraphrase = f"A {pattern_type.replace('_',' ')} that frames {title} without quoting it."

            if any(term in paraphrase.lower() for term in forbidden):
                continue

            patterns.append(
                VoicePattern(
                    pattern_type=pattern_type,
                    description=desc,
                    example_paraphrase=paraphrase,
                    when_to_use="Use when you need a sharp setup or pivot."
                )
            )

        return patterns[:5]

    # ------------------------------------------------------------------
    # Source classification
    # ------------------------------------------------------------------
    def classify_source(self, text: str, meta: Dict) -> str:
        t = (text or "") + " " + " ".join(str(v) for v in meta.values())
        tl = t.lower()
        if any(k in tl for k in ["sign up", "pricing", "$", "per month", "per year", "subscribe", "discount"]):
            return SourceType.MARKETING
        if any(k in tl for k in ["follow us", "tiktok", "whatsapp", "linkedin", "twitter", "x.com", "instagram", "facebook"]):
            return SourceType.PLATFORM_BOILERPLATE
        if any(k in tl for k in ["thank you for attending", "joined us at", "conference", "event"]):
            return SourceType.PERSONAL_CONTEXT
        return SourceType.EDITORIAL_EVIDENCE

    # ------------------------------------------------------------------
    # NewsletterPlan builder and validation
    # ------------------------------------------------------------------
    def _build_newsletter_plan(
        self,
        outline_text: str,
        outline_data: Dict,
        outline_sources: List[Dict],
        facts: List[Dict],
        rag_examples: List[Dict],
        bible_sections: Dict,
        analysis: Dict,
        target_length: int,
        style_metrics: Dict,
        compiler_outline: Optional[CompilerOutline] = None
    ) -> NewsletterPlan:
        """Compile a structured NewsletterPlan that the prompt will use."""

        theme = compiler_outline.headline if compiler_outline else (outline_data.get('headline') or analysis.get('topics', ['Newsletter'])[0] if analysis else (outline_text.splitlines()[0] if outline_text else "Newsletter"))
        angles = []
        if compiler_outline and compiler_outline.preview:
            angles.append(compiler_outline.preview)
        if compiler_outline and compiler_outline.central_question:
            angles.append(compiler_outline.central_question)
        if analysis and analysis.get('topics'):
            angles.extend(analysis['topics'][:2])

        # Required input types present in this prompt-build
        required_input_types = []
        if outline_text:
            required_input_types.append('outline')
        if facts:
            required_input_types.append('facts')
        if rag_examples:
            required_input_types.append('rag_examples')
        if bible_sections:
            required_input_types.append('bible_style')
        if outline_sources:
            required_input_types.append('provided_sources')
        if self.learnings.get('include_patterns'):
            required_input_types.append('learnings')

        # Build coverage list
        coverage = []
        for itype in required_input_types:
            coverage.append(
                RequiredInputCoverage(
                    input_type=itype,
                    must_use=True,
                    description=f"Must incorporate {itype.replace('_', ' ')}",
                )
            )

        # Style profile assembled from dials + bible
        style_profile = StyleProfile(
            tone=analysis.get('tone', ''),
            pacing='',
            stance='critical' if style_metrics.get('controversy_level', 50) > 60 else '',
            taboos=self.bible.get('cliches_to_avoid', [])[:10] if self.bible else [],
            style_tokens=self.bible.get('writing_voice', {}).get('signature_phrases', [])[:6] if self.bible else [],
        )

        # Sections from compiler_outline if provided
        sections = []

        def section_id(name: str) -> str:
            return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-') or "section"

        if compiler_outline:
            for sec in compiler_outline.sections:
                sec_name = sec.get('title', 'Section')
                sec_id = sec.get('section_id', section_id(sec_name))
                sections.append(
                    NewsletterSection(
                        id=sec_id,
                        name=sec_name,
                        goal=sec.get('focus', sec_name),
                        word_count=sec.get('word_count', 150),
                        sources_needed_min=1,
                        source_anchor_requirements=required_input_types.copy() if required_input_types else ['outline']
                    )
                )
        if not sections:
            # fallback to previous behavior with minimal sections
            main_name = outline_data.get('headline', 'Main Story')
            main_sec_id = section_id(main_name)
            sections.append(
                NewsletterSection(
                    id=main_sec_id,
                    name=main_name,
                    goal="Develop the main narrative with key insights.",
                    word_count=target_length,
                    sources_needed_min=1,
                    source_anchor_requirements=required_input_types.copy() if required_input_types else ['outline']
                )
            )

        plan = NewsletterPlan(
            theme=theme,
            audience="Journalists and content creators in Africa/Asia",
            purpose="Write a newsletter issue",
            angle_choices=angles[:3] or [theme],
            required_inputs_coverage=coverage,
            style_profile=style_profile,
            sections=sections,
            call_to_action="Invite readers to reply and share with colleagues.",
            fact_risk_flags=analysis.get('fact_types_needed', []) if analysis else [],
            outline_text=outline_text,
            target_length=target_length,
            provided_sources_count=len(outline_sources),
        )

        return plan

    # ------------------------------------------------------------------
    # Relevance brief selection
    # ------------------------------------------------------------------
    def _extract_keywords(self, text: str, limit: int = 12) -> List[str]:
        if not text:
            return []
        tokens = re.findall(r"[A-Za-z0-9']+", text.lower())
        stop = set([
            "the","and","or","of","in","a","to","for","on","with","that","is","are","was","were","it","this","as","at","by","from",
            "an","be","have","has","had","but","not","your","you","i","we","they","their","them","our","us","will","would","can",
            "could","should","may","might","also","about","into","than","more","most","some","any","all","just","like","if","so",
            "no","yes","do","does","did","because","when","what","who","which","how","why","where","while","over","under","up","down",
            "out","new","old"
        ])
        freq = {}
        for t in tokens:
            if len(t) <= 3 or t in stop:
                continue
            freq[t] = freq.get(t, 0) + 1
        return [t for t, _ in sorted(freq.items(), key=lambda x: (-x[1], -len(x[0])))][:limit]

    def build_relevance_brief(
        self,
        plan: NewsletterPlan,
        facts: List[Dict],
        rag_examples: List[Dict],
        outline_sources: List[Dict],
        compiler_outline: Optional[CompilerOutline] = None
    ) -> RelevanceBrief:
        theme = plan.theme
        angles = plan.angle_choices[:2]
        central_q = compiler_outline.central_question if compiler_outline else ""
        keywords = self._extract_keywords(theme + " " + " ".join(angles) + " " + central_q)
        style_tokens = plan.style_profile.style_tokens if plan.style_profile else []
        keywords.extend(style_tokens[:3])
        fact_keywords = []
        if compiler_outline:
            for sec in compiler_outline.sections:
                for kp in sec.get('key_points', []):
                    if kp.get('kind') == "FACT":
                        fact_keywords.extend(self._extract_keywords(kp.get('text', ''), limit=5))
        keywords.extend(fact_keywords[:6])
        keywords = list(dict.fromkeys(keywords))[:15]

        selected: List[RelevanceItem] = []
        exclusions: List[str] = []

        def score(text: str, title: str = "") -> int:
            t = (text or "") + " " + (title or "")
            return sum(1 for k in keywords if k.lower() in t.lower())

        # Voice patterns from past newsletters (no raw text)
        voice_patterns = self.extract_voice_patterns(rag_examples)
        vp_items = []
        for i, vp in enumerate(voice_patterns):
            sc = score(vp.description, vp.example_paraphrase)
            vp_items.append((sc, RelevanceItem(
                id=f"VP_{i+1}",
                source_type="voice_pattern",
                source_id=str(i+1),
                title=vp.pattern_type,
                summary=vp.example_paraphrase,
                why_relevant=vp.description,
                use_as="voice_move",
                keywords=keywords,
                confidence=0.6
            )))
        vp_items = sorted(vp_items, key=lambda x: -x[0])[:5]
        selected.extend([ri for _, ri in vp_items if ri.summary.strip()])

        # Facts (knowledge base) -> 2-4, prioritize fact keywords and central question actors
        kb_items = []
        for idx, f in enumerate(facts):
            title = f.get('source_title', f.get('source_name', 'Fact'))
            txt = f.get('text', f.get('fact_text', ''))
            sc = score(txt, title)
            if fact_keywords:
                sc += sum(1 for k in fact_keywords if k.lower() in txt.lower())
            if central_q:
                sc += sum(1 for k in self._extract_keywords(central_q, limit=6) if k.lower() in txt.lower())
            kb_items.append((sc, RelevanceItem(
                id=f"E_{f.get('id', idx)}",
                source_type="knowledge_base",
                source_id=f.get('id', str(idx)),
                title=title,
                summary=txt[:240],
                why_relevant="Data point for this story",
                use_as="argument",
                keywords=keywords,
                confidence=0.5 + 0.05*sc
            )))
        kb_items = sorted(kb_items, key=lambda x: -x[0])[:4]
        selected.extend([ri for _, ri in kb_items if ri.summary.strip()])

        # Provided sources -> include as reference items
        for i, src in enumerate(outline_sources[:4]):
            title = src.get('title', f"Provided Source {i+1}")
            summary = (src.get('summary') or src.get('content') or '')[:200]
            selected.append(RelevanceItem(
                id=f"PS_{i+1}",
                source_type="provided_source",
                source_id=src.get('url', str(i+1)),
                title=title,
                summary=summary,
                why_relevant="User-provided source",
                use_as="reference",
                keywords=keywords,
                confidence=0.9
            ))

        selection_stats = {
            'past_newsletters': len([r for r in selected if r.source_type == 'past_newsletter']),
            'knowledge_base': len([r for r in selected if r.source_type == 'knowledge_base']),
            'provided_source': len([r for r in selected if r.source_type == 'provided_source']),
        }

        return RelevanceBrief(
            theme=theme,
            angles=angles,
            selected_items=selected,
            exclusions=exclusions,
            selection_stats=selection_stats
        )

    def _validate_newsletter_plan(
        self,
        plan: NewsletterPlan,
        required_input_types: List[str]
    ) -> List[str]:
        """Validate the plan against required inputs and section anchors."""
        errors = []

        coverage_map = {c.input_type: c for c in plan.required_inputs_coverage}

        # a) every required_input_type appears
        missing_types = [t for t in required_input_types if t not in coverage_map]
        if missing_types:
            errors.append(f"Missing coverage for: {', '.join(missing_types)}")

        # b) must_use true for core required inputs
        missing_must = [t for t in required_input_types if coverage_map.get(t) and not coverage_map[t].must_use]
        if missing_must:
            errors.append(f"Required inputs not marked must_use: {', '.join(missing_must)}")

        # c) each required input allocated to at least one section
        for t in required_input_types:
            anchored = any(t in sec.source_anchor_requirements for sec in plan.sections)
            if not anchored:
                errors.append(f"Required input '{t}' not allocated to any section")

        # ensure each section has anchor requirements if we have required inputs
        if required_input_types:
            for sec in plan.sections:
                if not sec.source_anchor_requirements:
                    errors.append(f"Section '{sec.name}' missing source_anchor_requirements")

        return errors
    
    def _validate_provided_sources_usage(
        self,
        plan: NewsletterPlan,
        anchored_outline: AnchoredOutline
    ) -> List[str]:
        """Validate that provided sources are actually used in the anchored outline."""
        errors = []
        
        if plan.must_use_provided_sources_min <= 0:
            return errors
        
        # Count provided source anchors (PS_*) in the outline
        provided_anchors = set()
        for section in anchored_outline.sections:
            for bullet in section.bullets:
                for anchor in bullet.anchors:
                    if anchor.startswith('PS_'):
                        provided_anchors.add(anchor)
        
        if len(provided_anchors) < plan.must_use_provided_sources_min:
            errors.append(
                f"Must use at least {plan.must_use_provided_sources_min} provided source(s), "
                f"but only {len(provided_anchors)} were anchored in outline"
            )
        
        return errors
    
    def _validate_outline_semantics(
        self,
        anchored_outline: AnchoredOutline,
        topic_sig
    ) -> List[str]:
        """Validate that outline bullets are semantic and not placeholders."""
        errors = []
        
        # Placeholder patterns to reject
        placeholder_patterns = [
            r'key\s+point\s+\d+',
            r'supporting\s+the\s+goal',
            r'develop\s+the\s+main\s+narrative',
            r'placeholder',
            r'tbd',
            r'to\s+be\s+determined',
            r'add\s+content\s+here',
            r'\[\s*\.\.\.\s*\]',
        ]
        
        # Required concept stems for at least one bullet to mention
        required_concepts = [
            'platform', 'incentive', 'monetiz', 'policy', 'verification', 
            'harm', 'accountability', 'regulation', 'consent', 'victim',
            'model', 'dataset', 'training', 'bias', 'accuracy', 'error'
        ]
        
        has_required_concept = False
        generic_bullet_count = 0
        total_bullets = 0
        
        for section in anchored_outline.sections:
            for bullet in section.bullets:
                bullet_text = bullet.text.lower()
                total_bullets += 1
                
                # Check for placeholder patterns
                for pattern in placeholder_patterns:
                    if re.search(pattern, bullet_text):
                        errors.append(
                            f"Placeholder bullet detected in '{section.section_id}': '{bullet.text[:50]}...'"
                        )
                        break
                
                # Check if bullet mentions topic entities/keywords
                if topic_sig:
                    has_entity = any(ent.lower() in bullet_text for ent in topic_sig.entities)
                    has_keyword = any(kw in bullet_text for kw in topic_sig.keywords)
                    if not has_entity and not has_keyword:
                        generic_bullet_count += 1
                
                # Check for required concepts
                if any(concept in bullet_text for concept in required_concepts):
                    has_required_concept = True
        
        # Allow up to 50% generic bullets (some bullets can be transitional/meta)
        if total_bullets > 0 and generic_bullet_count > total_bullets * 0.5:
            errors.append(
                f"Too many generic bullets ({generic_bullet_count}/{total_bullets}) missing topic keywords"
            )
        
        if not has_required_concept:
            errors.append(
                "Outline missing concrete claims about mechanisms, actors, harms, or policies"
            )
        
        return errors
    
    def _sanitize_visual_prompt(self, text: str) -> tuple[str, bool]:
        """
        Sanitize visual prompts to prevent harmful imagery generation.
        Returns (sanitized_text, was_sanitized).
        """
        if not text:
            return text, False
        
        text_lower = text.lower()
        
        # Unsafe keywords
        unsafe_keywords = {
            'undress', 'strip', 'nude', 'naked', 'sexual', 'breasts', 
            'intimate', 'explicit', 'nsfw', 'pornographic'
        }
        
        # Gender/person keywords
        gender_keywords = {'woman', 'women', 'girl', 'girls', 'female', 'lady', 'ladies'}
        
        # Check if prompt contains unsafe + gender keywords
        has_unsafe = any(kw in text_lower for kw in unsafe_keywords)
        has_gender = any(kw in text_lower for kw in gender_keywords)
        
        if has_unsafe and has_gender:
            # Replace with safe alternative
            safe_alternatives = [
                "Abstract illustration of a phone screen with an 'AI-generated' warning label, blurred faces, and a platform logo in the background",
                "Collage of verification signals: metadata tags, 'synthetic media' labels, and newsroom fact-check tools",
                "A courtroom-themed sketch: 'consent' missing, 'platform accountability' on trial",
                "Digital illustration: a shield with 'verification' protecting against deepfake imagery, checkmarks and warning symbols",
            ]
            # Pick based on text hash for consistency
            idx = abs(hash(text)) % len(safe_alternatives)
            return safe_alternatives[idx], True
        
        # Check for any unsafe keywords alone (without gender) - still risky
        if has_unsafe:
            return "Abstract digital illustration showing AI technology and content verification systems", True
        
        return text, False
    
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

    # ------------------------------------------------------------------
    # Outline compiler (UI outline -> CompilerOutline)
    # ------------------------------------------------------------------
    def _classify_keypoint(self, text: str) -> str:
        t = text.lower()
        if any(tok in t for tok in ['subscribe', 'share', 'reply', 'join', 'cta', 'support']):
            return "CTA"
        if re.search(r'\b\d+[%]?\b', t) or any(tok in t for tok in ['according to', 'data', 'study', 'report', 'evidence', 'statistic', 'research']):
            return "FACT"
        if any(tok in t for tok in ['joke', 'haha', 'laugh', 'aside', 'personal', 'story', 'analogy']):
            return "VOICE_MOVE"
        return "INTERPRETATION"

    def compile_outline(
        self,
        ui_outline: Dict,
        style_metrics: Dict,
        source_pool: List[Dict],
        kb_pool: List[Dict],
        include_promos: bool = False
    ) -> CompilerOutline:
        headline = ui_outline.get('headline') or ui_outline.get('title') or "Newsletter"
        preview = ui_outline.get('preview') or ui_outline.get('summary') or ""
        opening_hook = ui_outline.get('opening_hook', "")
        central_question = ui_outline.get('central_question') or f"What about {headline}?"

        stance = "critical but fair"
        if style_metrics.get('skepticism_level', 50) > 65 or style_metrics.get('doom_level', 50) > 65:
            stance = "critical"
        elif style_metrics.get('optimism_level', 50) > 65:
            stance = "optimistic"

        target_word_count = ui_outline.get('target_word_count') or 800
        story_type = ui_outline.get('story_type', 'news_analysis')

        def to_ckp(text: str, idx: int) -> CompilerKeyPoint:
            kind = self._classify_keypoint(text)
            return CompilerKeyPoint(
                id=f"kp_{idx}",
                text=text,
                kind=kind,
                needs_citation=(kind == "FACT"),
                priority=1,
                suggested_sources=[]
            )

        sections = []
        kp_idx = 0

        # Main story
        main = ui_outline.get('main_story', {})
        main_points = main.get('key_points', [])
        if main_points:
            kps = []
            for p in main_points:
                if not p:
                    continue
                kp_idx += 1
                kps.append(asdict(to_ckp(p, kp_idx)))
            sections.append({
                'section_id': 'main',
                'title': main.get('heading', 'Main Story'),
                'focus': main.get('heading', 'Main Story'),
                'word_count': main.get('target_word_count', 500),
                'key_points': kps
            })

        for sec_i, sec in enumerate(ui_outline.get('additional_sections', [])):
            kps = []
            for p in sec.get('bullet_points', []):
                if not p:
                    continue
                kp_idx += 1
                kps.append(asdict(to_ckp(p, kp_idx)))
            sections.append({
                'section_id': f"sec_{sec_i}",
                'title': sec.get('heading', f"Section {sec_i+1}"),
                'focus': sec.get('heading', ''),
                'word_count': sec.get('target_word_count', 150),
                'key_points': kps
            })

        # Pools (refs only)
        editorial_sources = []
        personal_context = []
        marketing_items = []
        boilerplate_items = []

        for s in source_pool:
            stype = self.classify_source(s.get('summary', '') or s.get('title', ''), s)
            if stype == SourceType.EDITORIAL_EVIDENCE:
                editorial_sources.append(s)
            elif stype == SourceType.PERSONAL_CONTEXT:
                personal_context.append(s)
            elif stype == SourceType.MARKETING:
                marketing_items.append(s)
            else:
                boilerplate_items.append(s)

        source_pool_refs = editorial_sources[:8]
        kb_pool_refs = kb_pool[:8]

        must_include_points = [headline, preview]
        avoid_points = ui_outline.get('avoid_points', [])
        avoid_points.append("Do not include UI artifacts like 'Created with ChatGPT'")

        return CompilerOutline(
            headline=headline,
            preview=preview,
            opening_hook=opening_hook,
            central_question=central_question,
            stance=stance,
            target_word_count=target_word_count,
            story_type=story_type,
            sections=sections,
            must_include_points=must_include_points,
            avoid_points=avoid_points,
            source_pool_refs=source_pool_refs,
            kb_pool_refs=kb_pool_refs,
            ui_artifacts_to_ignore=["Created with ChatGPT"]
        )
    # Retrieval pack helpers
    # ------------------------------------------------------------------
    def _build_retrieval_pack(
        self,
        facts: List[Dict],
        rag_examples: List[Dict],
        relevance_brief: RelevanceBrief,
        outline_sources: List[Dict],
        topic_sig=None,
        allow_empty_kb_after_filter: bool = True
    ) -> RetrievalPack:
        """Create a RetrievalPack from selected relevance items only."""
        excerpts: List[RetrievalExcerpt] = []

        def _fingerprints(text: str, max_terms: int = 8) -> List[str]:
            """Extract distinctive fingerprint terms (simple heuristic, no deps)."""
            if not text:
                return []
            # tokenize crudely
            tokens = re.findall(r"[A-Za-z0-9']+", text.lower())
            stop = set([
                "the", "and", "or", "of", "in", "a", "to", "for", "on", "with", "that",
                "is", "are", "was", "were", "it", "this", "as", "at", "by", "from",
                "an", "be", "have", "has", "had", "but", "not", "your", "you", "i",
                "we", "they", "their", "them", "our", "us", "will", "would", "can",
                "could", "should", "may", "might", "also", "about", "into", "than",
                "more", "most", "some", "any", "all", "just", "like", "if", "so",
                "no", "yes", "do", "does", "did", "because", "when", "what", "who",
                "which", "how", "why", "where", "while", "over", "under", "up", "down",
                "out", "new", "old"
            ])
            freq = {}
            for t in tokens:
                if len(t) <= 3:
                    continue
                if t in stop:
                    continue
                freq[t] = freq.get(t, 0) + 1
            # pick rarer terms by inverse frequency (simple sort)
            sorted_terms = sorted(freq.items(), key=lambda x: (x[1], -len(x[0])))
            return [t for t, _ in sorted_terms[:max_terms]]

        # Caps
        max_total_excerpts = 18
        max_excerpt_chars = 800

        # Map relevance items to excerpts (voice vs substance) with source gating
        before_kb = len([ri for ri in relevance_brief.selected_items if ri.source_type == "knowledge_base"])
        after_kb = 0
        editorial_excerpts = 0
        for item in relevance_brief.selected_items:
            txt = item.summary[:max_excerpt_chars]
            rid = item.id
            source_type = item.source_type
            if source_type == "voice_pattern":
                # treat as voice anchor; use past_newsletter type for diversity tests
                source_type = "past_newsletter"
            # classify and filter
            stype = self.classify_source(txt, {"title": item.title})
            if stype != "EDITORIAL_EVIDENCE" and source_type not in ["editorial_voice"]:
                continue
            # Topic relevance filter for KB/editorial
            if topic_sig and source_type in ["knowledge_base", "facts"]:
                sc = score_source_relevance(txt, topic_sig, None)
                if sc < 2.0:
                    continue
                else:
                    after_kb += 1
            excerpts.append(
                RetrievalExcerpt(
                    id=rid,
                    text=txt,
                    source=item.title,
                    url="",
                    source_type=source_type,
                    use_as=item.use_as,
                    fingerprint_terms=_fingerprints(txt),
                    raw={'title': item.title, 'summary': item.summary}
                )
            )
            if stype == "EDITORIAL_EVIDENCE":
                editorial_excerpts += 1
            if len(excerpts) >= max_total_excerpts:
                break

        # Provided sources: include as thin references (always allowed)
        for i, src in enumerate(outline_sources[:4]):
            rid = f"PS_{i+1}"
            title = src.get('title', 'Provided Source')
            url = src.get('url', '')
            summary = (src.get('summary') or src.get('content') or '')[:200]
            excerpts.append(
                RetrievalExcerpt(
                    id=rid,
                    text=summary,
                    source=title,
                    url=url,
                    source_type="provided_source",
                    use_as="reference",
                    fingerprint_terms=_fingerprints(summary + " " + title),
                    raw=src
                )
            )
            if len(excerpts) >= max_total_excerpts:
                break

        if editorial_excerpts == 0 and not allow_empty_kb_after_filter:
            raise ValueError("RetrievalPack: no editorial evidence sources after filtering")

        self.last_kb_filter_counts = {'before': before_kb, 'after': after_kb}

        return RetrievalPack(excerpts=excerpts)

    # ------------------------------------------------------------------
    # Anchored outline generation
    # ------------------------------------------------------------------
    def generate_anchored_outline(self, plan: NewsletterPlan, pack: RetrievalPack) -> AnchoredOutline:
        """Generate an anchored outline ensuring every bullet is tied to anchors."""
        anchor_ids = [ex.id for ex in pack.excerpts]
        if not anchor_ids:
            raise ValueError("AnchoredOutline: no anchors available in RetrievalPack")

        voice_ids = [ex.id for ex in pack.excerpts if ex.source_type in ['past_newsletter', 'newsletter_bible', 'editorial_voice', 'voice_pattern']]
        substance_ids = [ex.id for ex in pack.excerpts if ex.source_type in ['knowledge_base', 'facts', 'provided_source', 'editorial_evidence']]
        if not voice_ids or not substance_ids:
            raise ValueError("AnchoredOutline: missing voice or substance anchors for diversity")

        sections: List[AnchoredSection] = []
        intents_cycle = ["hook", "argument", "example", "context", "transition", "cta", "tool"]

        for sec_idx, sec in enumerate(plan.sections):
            bullets: List[AnchoredBullet] = []

            # Use 3-5 bullets per section based on word count
            desired = min(5, max(3, sec.word_count // 150))

            # Ensure diversity: one voice + one substance anchor per section
            selected_anchors = []
            if voice_ids:
                selected_anchors.append(voice_ids[sec_idx % len(voice_ids)])
            if substance_ids:
                selected_anchors.append(substance_ids[sec_idx % len(substance_ids)])

            # Fill remaining with round robin
            while len(selected_anchors) < desired:
                selected_anchors.append(anchor_ids[(sec_idx + len(selected_anchors)) % len(anchor_ids)])

            for b_idx, anchor in enumerate(selected_anchors):
                bullet_text = f"{sec.name}: key point {b_idx+1} supporting the goal '{sec.goal}'"
                intent = intents_cycle[(sec_idx + b_idx) % len(intents_cycle)]
                bullets.append(
                    AnchoredBullet(
                        text=bullet_text,
                        anchors=[anchor],
                        intent=intent
                    )
                )

            # Hard gates
            if not bullets:
                raise ValueError(f"AnchoredOutline: section '{sec.name}' has no bullets")
            if not any(b.anchors for b in bullets):
                raise ValueError(f"AnchoredOutline: section '{sec.name}' bullets missing anchors")

            # ensure at least one unique anchor per section
            unique = set()
            for b in bullets:
                unique.update(b.anchors)
            if len(unique) < 1:
                raise ValueError(f"AnchoredOutline: section '{sec.name}' lacks unique anchors")

            sections.append(AnchoredSection(section_id=sec.id, bullets=bullets))

        return AnchoredOutline(sections=sections)

    # ------------------------------------------------------------------
    # Coverage audit and fixes
    # ------------------------------------------------------------------
    def audit_coverage(self, plan: Dict, pack: Dict, outline: str, draft_text: str) -> Dict:
        """Heuristic, deterministic audit of coverage and anchoring."""
        report = {
            'missing_required_input_types': [],
            'missing_sections': [],
            'missing_must_include_points': [],
            'anchor_usage_stats': {},
            'unanchored_claims': [],
            'redundancy_flags': [],
            'voice_match_flags': [],
            'pass': True,
        }

        # Normalize plan/pack if dicts
        def _get_plan_sections(p):
            try:
                return p.get('sections', [])
            except Exception:
                return []

        def _get_required_inputs(p):
            try:
                return p.get('required_inputs_coverage', [])
            except Exception:
                return []

        def _get_style_tokens(p):
            try:
                sp = p.get('style_profile', {})
                return sp.get('style_tokens', [])
            except Exception:
                return []

        # Anchor usage stats
        pack_excerpts = []
        try:
            for ex in pack.get('sections', []):  # pack is actually anchored_outline dict
                pass
        except Exception:
            pass

        # We stored anchored_outline in metadata; actual pack of excerpts isn't in metadata
        # so we cannot compute excerpt hits here without refactoring storage. Provide minimal stats.

        # Voice checks
        style_tokens = _get_style_tokens(plan)
        missing_voice = [t for t in style_tokens if t.lower() not in draft_text.lower()]
        if missing_voice:
            report['voice_match_flags'] = missing_voice

        # Sections / length check (approx)
        sections = _get_plan_sections(plan)
        if sections:
            words = draft_text.split()
            total_words = len(words)
            for sec in sections:
                target = sec.get('word_count', 0)
                if target <= 0:
                    continue
                # approximate: require at least 50% of target words overall
                if total_words < 0.5 * target:
                    report['missing_sections'].append(sec.get('name', 'section'))

        # must_include_points: if present
        mip = plan.get('must_include_points', []) if isinstance(plan, dict) else []
        for pt in mip:
            if pt and pt.lower() not in draft_text.lower():
                report['missing_must_include_points'].append(pt)

        # Required inputs coverage: minimal heuristic — assume if draft length>0 it's present; we lack per-type evidence
        # Mark missing if draft is empty
        if not draft_text.strip():
            for c in _get_required_inputs(plan):
                if c.get('must_use'):
                    report['missing_required_input_types'].append(c.get('input_type'))

        # Gather fingerprint terms from pack if present
        fingerprint_terms = []
        try:
            for ex in pack.get('excerpts', []):
                fingerprint_terms.extend(ex.get('fingerprint_terms', []))
        except Exception:
            pass

        # Unanchored claims heuristic
        sentences = re.split(r'(?<=[.!?])\s+', draft_text)
        factual_markers = ['according to', 'data', 'study', 'percent', '%', 'increase', 'decrease', 'billion', 'million', 'report', 'survey', 'research', 'evidence', 'figure', 'statistic', 'number']
        for s in sentences:
            if any(tok in s.lower() for tok in factual_markers):
                anchored = False
                for fp in fingerprint_terms:
                    if fp and fp.lower() in s.lower():
                        anchored = True
                        break
                if not anchored:
                    if not style_tokens or all(tok.lower() not in s.lower() for tok in style_tokens):
                        report['unanchored_claims'].append({'sentence': s.strip(), 'reason': 'factual-without-anchor', 'suggested_action': 'mark as needs verification'})

        # Redundancy: repeated sentences
        seen = {}
        for s in sentences:
            stem = s.strip().lower()[:40]
            if not stem:
                continue
            seen[stem] = seen.get(stem, 0) + 1
        for stem, cnt in seen.items():
            if cnt > 1:
                report['redundancy_flags'].append(stem)

        # Dumping detection (very rough)
        kb_count = len([ex for ex in pack.get('excerpts', []) if ex.get('source_type') == 'knowledge_base']) if isinstance(pack, dict) else 0
        if kb_count > 4:
            report['dumping_detected'] = True
        long_blocks = [s for s in sentences if len(s) > 800]
        if len(long_blocks) > 0:
            report['dumping_detected'] = True
        url_hits = len(re.findall(r'https?://', draft_text))
        if url_hits > 5:
            report['dumping_detected'] = True
        if "created with chatgpt" in draft_text.lower():
            report['dumping_detected'] = True

        # Relevance drift: low overlap with theme/angles
        theme = plan.get('theme', '') if isinstance(plan, dict) else ''
        angles = plan.get('angles', []) if isinstance(plan, dict) else []
        bundle_words = [w for w in (theme + " " + " ".join(angles)).lower().split() if len(w) > 3]
        if len(bundle_words) >= 2:
            overlap_hits = sum(1 for s in sentences if any(k in s.lower() for k in bundle_words[:6]))
            if overlap_hits < 1:
                report['relevance_drift'] = True

        # Pass/fail
        if report.get('dumping_detected') or report.get('relevance_drift'):
            report['pass'] = False
        if report['missing_required_input_types'] or report['missing_sections'] or report['missing_must_include_points'] or report['unanchored_claims']:
            report['pass'] = False

        return report

    def audit_failed(self, report: Dict) -> bool:
        return not report.get('pass', False)

    def apply_fixes(self, draft_text: str, audit_report: Dict, plan: Dict, pack: Dict, outline: str) -> str:
        """Apply minimal, deterministic fixes based on audit report."""
        text = draft_text

        # Insert missing must_include_points (append near end)
        if audit_report.get('missing_must_include_points'):
            addendum = "\n\n" + "\n".join([f"- {pt}" for pt in audit_report['missing_must_include_points']])
            text += "\n\nMissing required points:\n" + addendum

        # Mark unanchored claims
        for claim in audit_report.get('unanchored_claims', []):
            sent = claim.get('sentence', '')
            if sent and sent in text:
                text = text.replace(sent, sent + " (needs verification)")

        # Reduce redundancy: drop repeated stems
        sentences = re.split(r'(?<=[.!?])\s+', text)
        seen = set()
        deduped = []
        for s in sentences:
            stem = s.strip().lower()[:40]
            if stem in seen:
                continue
            seen.add(stem)
            deduped.append(s)
        text = " ".join(deduped)

        # Light voice reinforcement
        style_tokens = []
        try:
            sp = plan.get('style_profile', {})
            style_tokens = sp.get('style_tokens', [])
        except Exception:
            pass
        for tok in style_tokens[:3]:
            if tok.lower() not in text.lower():
                text += f"\n\n{tok}"

        return text
    
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
    
    def get_relevant_facts(self, analysis: Dict, max_facts: int = 12, topic_sig=None, provided_sources=None) -> List[Dict]:
        """
        Get facts using semantic search, prioritized by the outline analysis.
        
        Now supports topic-aware retrieval: retrieves a larger pool, then filters by topic.
        """
        if not KB_AVAILABLE:
            return []
        
        # Retrieve LARGER pool initially (3-4x desired) so we can filter down
        retrieval_pool_size = max_facts * 4
        
        all_facts = []
        seen = set()
        
        # Search for each query from the analysis
        queries = analysis.get('search_queries', [])
        fact_types = analysis.get('fact_types_needed', [])
        
        # Use more results per query since we'll filter
        results_per_query = max(8, retrieval_pool_size // len(queries)) if queries else 10
        
        for query in queries[:5]:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                facts = semantic_search_facts(query, limit=results_per_query, min_similarity=0.2)
            else:
                facts = get_relevant_facts(query, max_facts=results_per_query)
            
            for fact in facts:
                # Facts use 'text' key, not 'fact_text'
                fact_id = fact.get('id', hash(fact.get('text', '')))
                if fact_id not in seen:
                    seen.add(fact_id)
                    # Boost score if fact type matches what's needed
                    if fact.get('fact_type') in fact_types:
                        fact['relevance_boost'] = 1.5
                    # Mark if optional context (not directly relevant)
                    if fact.get('fact_type') == 'optional_context':
                        fact['is_optional_context'] = True
                    all_facts.append(fact)
        
        # Sort by relevance (with boost)
        all_facts.sort(
            key=lambda f: f.get('similarity', 0) * f.get('relevance_boost', 1.0),
            reverse=True
        )
        
        # TOPIC-AWARE FILTERING: If topic signature provided, filter immediately
        if topic_sig and provided_sources is not None:
            print(f"🔍 TOPIC-AWARE FILTERING: Retrieved {len(all_facts)} facts from semantic search")
            print(f"   Topic entities: {list(topic_sig.entities)[:5]}")
            print(f"   Topic keywords: {list(topic_sig.keywords)[:10]}")
            # Apply topic filter to the retrieved pool
            filtered_facts, filter_metrics = self.filter_facts_by_topic(
                all_facts[:retrieval_pool_size], 
                topic_sig, 
                provided_sources or []
            )
            # Store metrics for later retrieval
            self.last_fact_filter_metrics = filter_metrics
            print(f"   ✅ After filtering: {len(filtered_facts)} relevant facts (dropped {filter_metrics.get('dropped', 0)})")
            
            # Show what facts we're returning
            print(f"\n   📋 RETURNING {min(len(filtered_facts), max_facts)} FACTS:")
            for i, fact in enumerate(filtered_facts[:max_facts], 1):
                title = fact.get('source_title', '')[:50]
                print(f"      {i}. {title}")
            print()
            
            return filtered_facts[:max_facts]
        
        # Fallback: return top N (backward compatible)
        print(f"⚠️ WARNING: Topic-aware filtering SKIPPED (topic_sig={topic_sig is not None}, provided_sources={provided_sources is not None})")
        print(f"   Returning {len(all_facts[:max_facts])} unfiltered facts")
        return all_facts[:max_facts]
    
    def filter_facts_by_topic(self, facts: List[Dict], topic_sig, provided_sources: List[Dict]) -> tuple[List[Dict], Dict]:
        """Filter facts by topic relevance, cap optional context, track metrics."""
        if not topic_sig or not facts:
            return facts, {'before': len(facts), 'relevant': len(facts), 'optional': 0, 'dropped': 0}
        
        # Provided source URLs for bypass checking
        provided_urls = {src.get('url', '').lower() for src in provided_sources if src.get('url')}
        
        # Extract topic terms for strict matching
        topic_terms = set()
        if topic_sig.entities:
            topic_terms.update(e.lower() for e in topic_sig.entities)
        if topic_sig.keywords:
            topic_terms.update(k.lower() for k in topic_sig.keywords if len(k) > 3)
        
        relevant_facts = []
        optional_context_facts = []
        dropped = []
        
        for fact in facts:
            fact_text = fact.get('text', '') or fact.get('fact_text', '')
            fact_source = fact.get('source_url', '')
            fact_source_title = fact.get('source_title', '')
            is_optional = fact.get('is_optional_context', False)
            
            # Always keep facts from provided sources
            if fact_source and fact_source.lower() in provided_urls:
                relevant_facts.append(fact)
                continue
            
            # Score relevance
            fact_full_text = fact_text + " " + fact_source_title
            score = score_source_relevance(fact_full_text, topic_sig, section_id=None)
            
            # ULTRA-STRICT CHECK: Facts must mention PRIMARY actors/topics, not just related terms
            fact_lower = fact_full_text.lower()
            
            # PRIMARY identifiers - must mention these to be relevant
            primary_actors = {'grok', 'musk', 'elon musk', 'x platform', 'twitter'}
            primary_topics = {'deepfake', 'deepfakes', 'hijab', 'hijabs', 'sari', 'saris', 
                             'non-consensual', 'ncii'}
            
            mentions_primary_actor = any(actor in fact_lower for actor in primary_actors)
            mentions_primary_topic = any(topic in fact_lower for topic in primary_topics)
            
            # Must mention EITHER a primary actor OR primary topic
            is_highly_relevant = mentions_primary_actor or mentions_primary_topic
            
            if score >= FACT_MIN_RELEVANCE_SCORE and is_highly_relevant:
                print(f"  ✅ KEPT fact (score {score:.1f}, relevant): {fact_source_title[:50]}")
                relevant_facts.append(fact)
            elif score >= FACT_MIN_RELEVANCE_SCORE:
                print(f"  ❌ DROPPED fact (score {score:.1f}, not specific): {fact_source_title[:50]}")
            elif is_optional and score >= 0:  # Optional context can be tangentially related
                optional_context_facts.append(fact)
            else:
                dropped.append(fact)
                # Log dropped facts for debugging
                if score < FACT_MIN_RELEVANCE_SCORE:
                    print(f"  Dropped fact (low score {score:.1f}): {fact_source_title[:50]}")
                elif not mentions_topic:
                    print(f"  Dropped fact (no topic match): {fact_source_title[:50]}")
        
        # Cap optional context
        optional_context_facts = optional_context_facts[:OPTIONAL_CONTEXT_FACTS_MAX]
        
        filtered_facts = relevant_facts + optional_context_facts
        
        metrics = {
            'before': len(facts),
            'relevant': len(relevant_facts),
            'optional': len(optional_context_facts),
            'dropped': len(dropped)
        }
        
        return filtered_facts, metrics
    
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
        style_metrics: Dict = None,
        outline_struct: Dict = None,
        compiler_outline: Optional[CompilerOutline] = None
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
        print(f"📊 ANALYSIS SEARCH QUERIES: {analysis.get('search_queries', [])[:3]}")
        
        # Step 2: Build compiler outline FIRST (needed for topic signature)
        compiler_outline = self.compile_outline(
            ui_outline=outline_struct or {},
            style_metrics=style_metrics or {},
            source_pool=outline_sources or [],
            kb_pool=[],
            include_promos=False
        )
        
        # Step 3: Build topic signature EARLY
        tmp_plan = NewsletterPlan(
            theme=compiler_outline.headline,
            audience="",
            purpose="",
            angle_choices=[compiler_outline.preview or compiler_outline.headline],
            required_inputs_coverage=[],
            style_profile=StyleProfile(),
            sections=[],
            call_to_action="",
            fact_risk_flags=[],
            outline_text=outline,
            target_length=target_length,
            compiler_outline=compiler_outline,
        )
        topic_sig = build_topic_signature(tmp_plan, {}, outline_sources or [], [])
        
        # Step 4: Gather relevant context WITH TOPIC FILTERING
        # Pass topic_sig to get_relevant_facts so it filters during retrieval
        from datetime import datetime as dt_now
        print(f"\n{'='*60}")
        print(f"🔥 TOPIC-AWARE FACT RETRIEVAL (NEW CODE) {dt_now.now().strftime('%H:%M:%S')}")
        print(f"   Theme: {tmp_plan.theme}")
        print(f"   Provided sources: {len(outline_sources or [])}")
        print(f"{'='*60}\n")
        facts = self.get_relevant_facts(analysis, topic_sig=topic_sig, provided_sources=outline_sources or [])
        rag_examples = self.get_rag_examples(analysis)
        bible_sections = self.get_targeted_bible_sections(analysis)
        learnings = self.get_applicable_learnings(analysis)
        
        # Allow continuation if we have facts or rag examples even when no editorial sources were provided
        if not compiler_outline.source_pool_refs and not facts and not rag_examples:
            raise ValueError("No editorial evidence sources available")
        
        # Build relevance brief and retrieval pack
        relevance_brief = self.build_relevance_brief(tmp_plan, facts, rag_examples, outline_sources or [], compiler_outline)
        # Facts already filtered, retrieve metrics
        fact_filter_metrics = getattr(self, 'last_fact_filter_metrics', {'before': len(facts), 'relevant': len(facts), 'optional': 0, 'dropped': 0})
        pack = self._build_retrieval_pack(facts, rag_examples, relevance_brief, outline_sources or [], topic_sig=topic_sig)

        # Required input types present
        required_input_types = []
        if outline:
            required_input_types.append('outline')
        if outline_sources:
            required_input_types.append('provided_sources')
        if facts:
            required_input_types.append('facts')
        if rag_examples:
            required_input_types.append('rag_examples')
        if bible_sections:
            required_input_types.append('bible_style')
        if learnings:
            required_input_types.append('learnings')

        # Build NewsletterPlan with validation + up to 2 retries
        plan = None
        errors = []
        for attempt in range(3):
            plan = self._build_newsletter_plan(
                outline_text=outline,
                outline_data=outline_struct or {},
                outline_sources=outline_sources or [],
                facts=facts,
                rag_examples=rag_examples,
                bible_sections=bible_sections,
                analysis=analysis,
                target_length=target_length,
                style_metrics=style_metrics or {},
                compiler_outline=compiler_outline
            )
            errors = self._validate_newsletter_plan(plan, required_input_types)
            if not errors:
                break
        if errors:
            raise ValueError(f"NewsletterPlan validation failed after retries: {errors}")

        # Build AnchoredOutline with hard gates and topic relevance
        # Note: facts are already filtered by topic (done in get_relevant_facts)
        relevance_brief = self.build_relevance_brief(plan, facts, rag_examples, compiler_outline.source_pool_refs, compiler_outline)
        topic_sig = None
        pack = None
        anchored_outline = None
        # Track fact filtering metrics (facts already filtered in get_relevant_facts)
        fact_filter_metrics = getattr(self, 'last_fact_filter_metrics', 
                                      {'before': len(facts), 'relevant': len(facts), 'optional': 0, 'dropped': 0})
        try:
            topic_sig = build_topic_signature(plan, {}, compiler_outline.source_pool_refs, facts)
            # Facts already topic-filtered, just build pack
            pack = self._build_retrieval_pack(facts, rag_examples, relevance_brief, compiler_outline.source_pool_refs, topic_sig=topic_sig)
            anchored_outline = self.generate_anchored_outline(plan, pack)
            # Validate provided sources usage (retry once if fails)
            ps_errors = self._validate_provided_sources_usage(plan, anchored_outline)
            semantic_errors = self._validate_outline_semantics(anchored_outline, topic_sig)
            if ps_errors or semantic_errors:
                # Retry outline generation with stronger emphasis
                anchored_outline = self.generate_anchored_outline(plan, pack)
                ps_errors = self._validate_provided_sources_usage(plan, anchored_outline)
                semantic_errors = self._validate_outline_semantics(anchored_outline, topic_sig)
                if ps_errors or semantic_errors:
                    all_errors = ps_errors + semantic_errors
                    raise ValueError(f"Anchored outline validation failed: {'; '.join(all_errors)}")
            topic_sig = build_topic_signature(plan, asdict(anchored_outline) if anchored_outline else {}, compiler_outline.source_pool_refs, facts)
        except Exception:
            # fall back to pack without topic filtering if needed
            if not pack:
                pack = self._build_retrieval_pack(facts, rag_examples, relevance_brief, compiler_outline.source_pool_refs, topic_sig=None)
            if not anchored_outline:
                anchored_outline = self.generate_anchored_outline(plan, pack)

        # Step 3: Build system prompt (voice/identity)
        system_prompt = self._build_system_prompt(bible_sections, learnings, style_metrics or {})
        
        # Step 4: Build user prompt using the validated plan
        user_prompt = self._build_user_prompt(
            outline=plan.outline_text,
            facts=facts,
            rag_examples=rag_examples,
            bible_sections=bible_sections,
            target_length=plan.target_length,
            analysis=analysis,
            outline_sources=outline_sources or [],
            plan=plan,
            anchored_outline=anchored_outline
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
            'newsletter_plan': asdict(plan),
            'anchored_outline': asdict(anchored_outline),
            'relevance_brief': asdict(relevance_brief),
            'topic_signature': {
                'theme': topic_sig.theme if topic_sig else '',
                'entities': list(topic_sig.entities)[:5] if topic_sig else [],
                'keywords': list(topic_sig.keywords)[:8] if topic_sig else [],
            },
            'kb_relevance_filtered_count': getattr(self, 'last_kb_filter_counts', {}),
            'fact_relevance_filtered': fact_filter_metrics,
        }
        
        return system_prompt, user_prompt, metadata
    
    def _build_system_prompt(self, bible: Dict, learnings: List[str], style_metrics: Dict) -> str:
        """Build the system prompt with voice and identity."""
        
        prompt = """You are Paul McNally, writing your "Develop AI" newsletter for newsrooms and content creators in Africa and Asia.

## YOUR VOICE AND STYLE
"""
        # Add voice characteristics from writing_voice (not raw text)
        if 'writing_voice' in bible:
            voice = bible['writing_voice']
            if voice.get('tone'):
                prompt += f"Tone: {voice['tone']}\n"
            if voice.get('energy'):
                prompt += f"Energy: {voice['energy']}\n"
            if voice.get('sentence_rhythm'):
                prompt += f"Sentence rhythm: {voice['sentence_rhythm']}\n"
            if voice.get('paragraph_style'):
                prompt += f"Paragraphs: {voice['paragraph_style']}\n"
            if voice.get('how_you_open'):
                prompt += f"How you open: {voice['how_you_open']}\n"
            if voice.get('how_you_argue'):
                prompt += f"How you argue: {voice['how_you_argue']}\n"
            if voice.get('how_you_transition'):
                prompt += f"Transitions: {voice['how_you_transition']}\n"
        
        # Fallback to old 'voice' key if writing_voice not present
        elif 'voice' in bible:
            voice = bible['voice']
            if voice.get('tone'):
                prompt += f"Tone: {', '.join(voice['tone']) if isinstance(voice['tone'], list) else voice['tone']}\n"
            if voice.get('perspective'):
                prompt += f"Perspective: {voice['perspective']}\n"
            if voice.get('signature_phrases'):
                prompt += f"Signature phrases you use: {', '.join(voice['signature_phrases'])}\n"

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
1. Write EXACTLY like Paul McNally - match his voice, cadence, and sentence structure from the examples above
2. DO NOT use generic AI writing patterns like "Let's dive into", "gripping scenario", "silver lining", "Let's unpack", "without further ado"
3. DO NOT write like ChatGPT - avoid formulaic transitions, corporate jargon, and empty phrases
4. Use Paul's direct, critical, journalistic style - sharp observations, not smoothed-over commentary
5. Reference sources ACCURATELY - check publication names (Wired vs NYT, etc.)
6. DO NOT INVENT URLs, article titles, or sources - only use what's explicitly provided in the prompt
7. Include practical, actionable takeaways specific to newsrooms/creators
8. Keep energy authentic - critical when needed, not artificially balanced
9. Use short paragraphs, varied sentence length, conversational rhythm
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
        outline_sources: List[Dict],
        plan: NewsletterPlan = None,
        anchored_outline: AnchoredOutline = None
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
        
        # SECTION 1: Voice patterns (no raw text)
        if plan and hasattr(plan, 'compiler_outline') and plan.compiler_outline:
            pass  # voice patterns already in relevance brief
        
        # SECTION 2: Opening STYLE patterns from Bible (snippets showing HOW, not text to copy)
        if 'intro_examples' in bible_sections:
            prompt += "# YOUR OPENING STYLE (patterns to match, not text to copy)\n"
            for intro in bible_sections['intro_examples'][:2]:
                # Show only 100 chars - enough to see the PATTERN, not enough to copy verbatim
                prompt += f'- Opening pattern: "{intro[:100]}..."\n'
            prompt += "\n"
        
        # SECTION 3: Newsletter Plan summary (ground the model)
        if plan:
            prompt += "# NEWSLETTER PLAN (structured)\n"
            prompt += f"Theme: {plan.theme}\n"
            prompt += f"Audience: {plan.audience}\n"
            prompt += f"Purpose: {plan.purpose}\n"
            if plan.angle_choices:
                prompt += "Angle choices (ranked):\n"
                for idx, angle in enumerate(plan.angle_choices, 1):
                    prompt += f"{idx}. {angle}\n"
            prompt += "\nSections to follow:\n"
            for sec in plan.sections:
                prompt += f"- {sec.name} (Goal: {sec.goal}; Words: {sec.word_count}; Sources min: {sec.sources_needed_min}; Anchors: {', '.join(sec.source_anchor_requirements)})\n"
            prompt += "\nCall to action: " + plan.call_to_action + "\n\n"
        
        # SECTION 3a: Style Dials (from user settings) - SHOW ALL 22 METRICS
        # Pass style_metrics directly from the method parameter, not via StyleProfile
        # StyleProfile only has 5 fields, but we need all 22 style dials
        style_metrics_to_show = style_metrics or {}
        if style_metrics_to_show:
            # Show non-default style settings (anything != 50)
            active_styles = []
            for key, val in style_metrics_to_show.items():
                if isinstance(val, (int, float)) and val != 50:
                    # Convert snake_case to readable
                    readable = key.replace('_', ' ').title()
                    if val > 65:
                        active_styles.append(f"{readable}: HIGH ({val})")
                    elif val < 35:
                        active_styles.append(f"{readable}: LOW ({val})")
                    else:
                        active_styles.append(f"{readable}: {val}")
            
            if active_styles:
                prompt += "# STYLE FOCUS (user dials)\n"
                for style in active_styles:  # Show ALL non-default settings
                    prompt += f"- {style}\n"
                prompt += "\n"

        # SECTION 3b: Compiler Outline summary (compact)
        comp = plan.compiler_outline if hasattr(plan, 'compiler_outline') else None

        if comp:
            prompt += "# COMPILER OUTLINE (compact)\n"
            prompt += f"Headline: {comp.headline}\n"
            prompt += f"Central Question: {comp.central_question}\n"
            prompt += f"Stance: {comp.stance}\n"
            prompt += f"Must include: {', '.join(comp.must_include_points[:3])}\n"
            prompt += f"Avoid: {', '.join(comp.avoid_points[:3])}\n"
            prompt += "Sections:\n"
            for s in comp.sections[:4]:
                prompt += f"- {s.get('title','')} ({s.get('word_count','')} words)\n"
            prompt += "\n"

        # SECTION 3.4: Voice Patterns (selected only)
        rb = None
        try:
            rb = relevance_brief  # passed below
        except Exception:
            rb = None
        if rb:
            vps = [it for it in rb.selected_items if it.source_type in ['voice_pattern', 'editorial_voice']]
            if vps:
                prompt += "# VOICE PATTERNS (rhetorical moves)\n"
                for vp in vps[:5]:
                    prompt += f"- {vp.title}: {vp.summary} | use_as: {vp.use_as}\n"
                prompt += "\n"

        # SECTION 3.5: Anchored Outline (every bullet cites anchors)
        if anchored_outline:
            prompt += "# ANCHORED OUTLINE (use anchors per bullet; do not invent facts)\n"
            prompt += "⚠️ **CRITICAL:** These are SUGGESTED bullet points tied to sources. Use them as guidance but DO NOT invent URLs or sources not listed below.\n"
            prompt += json.dumps(asdict(anchored_outline), ensure_ascii=False)
            prompt += "\n\n"

        # SECTION 3.6: Relevance Brief (selected items only)
        if rb:
            prompt += "# RELEVANCE BRIEF (selected only)\n"
            for item in rb.selected_items[:10]:
                prompt += f"- {item.title} [{item.source_type}] why: {item.why_relevant} use_as: {item.use_as}\n"
            if rb.exclusions:
                prompt += "Exclusions: " + "; ".join(rb.exclusions[:5]) + "\n"
            prompt += "\n"

        # SECTION 4: Facts and Data (MEDIUM attention - middle)
        if outline_sources:
            must_use_count = plan.must_use_provided_sources_min if plan else 1
            prompt += f"# PROVIDED SOURCES (YOU MUST USE AT LEAST {must_use_count} in main story)\n"
            prompt += "## ⚠️ ATTRIBUTION WARNING: Cite these sources ACCURATELY by their publication name!\n"
            prompt += "## 🚨 CRITICAL: ONLY use sources listed below - DO NOT invent article titles, URLs, or publications\n\n"
            for src in outline_sources:
                if isinstance(src, dict):
                    title = src.get('title', 'Source')
                    url = src.get('url', '')
                    # Extract publication from URL if not provided
                    pub = src.get('publication', src.get('source', ''))
                    if not pub and url:
                        if 'wired.com' in url:
                            pub = 'Wired'
                        elif 'nytimes.com' in url or 'nyti.ms' in url:
                            pub = 'The New York Times'
                        elif 'techcrunch.com' in url:
                            pub = 'TechCrunch'
                        elif 'theverge.com' in url:
                            pub = 'The Verge'
                        elif 'techpolicy.press' in url:
                            pub = 'Tech Policy Press'
                    date = src.get('date', '')
                    
                    prompt += f"- **{pub or 'Unknown'}**: {title}"
                    if url:
                        prompt += f"\n  URL: {url}"
                    if date:
                        prompt += f"\n  Date: {date}"
                    prompt += "\n\n"
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
        
        # SECTION 5: The Outline (HIGH attention - near end)
        prompt += "# THE NEWSLETTER TO WRITE\n\n"
        prompt += outline
        prompt += "\n\n"
        
        # SECTION 6: Final Instructions (HIGH attention - at end)
        prompt += "# INSTRUCTIONS\n\n"
        prompt += f"1. **Word Count Target:** Write approximately {target_length} words TOTAL\n"
        prompt += "   - This is the EXACT sum of all section word counts shown in the outline above\n"
        prompt += "   - Hit the INDIVIDUAL section targets: they add up to this total\n"
        prompt += "   - Example: 'Main Story: 800 words' means write 800 words for that section\n"
        prompt += "2. Follow the outline structure exactly - each section should match its target word count shown above\n"
        prompt += "   - The outline shows KEY POINTS as bullets - develop each into full paragraphs\n"
        prompt += "   - Do NOT just write a single opening paragraph - cover ALL key points shown\n"
        prompt += "   - Structure: intro → develop each key point → conclusion\n"
        prompt += "3. CRITICAL: Write in Paul McNally's voice - study the examples above and match:\n"
        prompt += "   - His sentence rhythm and paragraph length\n"
        prompt += "   - His critical, journalistic tone (not smoothed over)\n"
        prompt += "   - His direct observations and sharp takes\n"
        prompt += "   - NO ChatGPT phrases: no 'dive into', 'silver lining', 'unpack', 'gripping', etc.\n"
        prompt += "4. ATTRIBUTION: Double-check source publications - cite Wired as Wired, NYT as NYT, etc.\n"
        prompt += "5. 🚨 DO NOT INVENT URLs OR CITATIONS - only use the sources explicitly provided above\n"
        prompt += "6. 🚨 DO NOT reference articles, studies, or sources that aren't in the PROVIDED SOURCES or FACTS sections\n"
        prompt += "   - If you need to mention something but don't have a source for it, describe it generally WITHOUT claiming a specific source\n"
        prompt += "   - Example: ✅ 'Recent developments in AI...' ❌ 'According to TechCrunch (url), ...'\n"
        prompt += "7. Use only the selected items in the Relevance Brief and RetrievalPack. Do not include large quoted blocks from past newsletters or full knowledge base dumps.\n"
        prompt += "8. Use the ANCHORED OUTLINE bullets and their anchors; do not invent facts outside anchors\n"
        prompt += "9. Incorporate relevant facts with accurate citations\n"
        prompt += "10. Make it engaging, practical, and authentic to Paul's voice\n"
        
        if analysis.get('tone'):
            prompt += f"9. Maintain a {analysis['tone']} tone throughout\n"

        # Artifact blocking
        forbidden = ["created with chatgpt"]
        for f in forbidden:
            prompt = prompt.replace(f, "")
        
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
        # CRITICAL: Sanitize opening hook BEFORE any processing
        original_hook = outline_data.get('opening_hook', '')
        if original_hook:
            from image_service import _sanitize_visual_prompt
            sanitized_hook, was_sanitized = _sanitize_visual_prompt(original_hook)
            # Overwrite in outline_data so sanitized version is used everywhere
            outline_data = {**outline_data, 'opening_hook': sanitized_hook}
            hook_sanitized = was_sanitized
            if was_sanitized:
                print(f"⚠️ Opening hook sanitized for safety")
        else:
            hook_sanitized = False
            sanitized_hook = original_hook
        
        # Convert structured outline_data to text format (uses sanitized hook)
        outline_text = self._outline_data_to_text(outline_data, idea, style_metrics, story_type_data)
        
        # Calculate target word count from outline_data - EXACT sum, no buffer
        main_words = outline_data.get('main_story', {}).get('target_word_count', 500)
        section_words = sum(s.get('target_word_count', 150) for s in outline_data.get('additional_sections', []))
        target_length = main_words + section_words  # Exact sum from outline, no buffer added
        
        # Use the intelligent prompt builder
        system_prompt, user_prompt, metadata = self.prompt_constructor.build_prompt(
            outline=outline_text,
            target_length=target_length,
            outline_sources=outline_data.get('sources', []),
            style_metrics=style_metrics,
            outline_struct=outline_data
        )
        
        # Add outline_data specific info to metadata
        metadata['headline'] = outline_data.get('headline', '')
        metadata['preview'] = outline_data.get('preview', '')
        metadata['target_word_count'] = target_length
        metadata['sources_provided'] = len(outline_data.get('sources', []))
        
        # Add hook sanitization metadata
        metadata['hook_sanitized'] = hook_sanitized
        metadata['original_hook'] = original_hook
        metadata['sanitized_hook'] = sanitized_hook
        
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
            
            # Include story structure if available
            if main.get('structure'):
                text += "Story Structure:\n"
                for i, structure_point in enumerate(main.get('structure', []), 1):
                    text += f"{i}. {structure_point}\n"
                text += "\n"
            
            text += "Key Points to Develop:\n"
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
            target_length=target_length,
            outline_sources=[],
            style_metrics={},
            outline_struct={},
            compiler_outline=None
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

        # ---------------- AUDIT + FIX LOOP (max 1 retry) ----------------
        def build_result(txt: str, meta_extra: Dict[str, Any]) -> GenerationResult:
            generation_id = hashlib.md5(
                f"{outline}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12]
            meta = {
                'output_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
                'output_words': len(txt.split()),
                'temperature': temperature,
            }
            meta.update(meta_extra)
            return GenerationResult(
                id=generation_id,
                content=txt,
                prompt_components=metadata,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=generation_model,
                metadata=meta,
                timestamp=datetime.now().isoformat()
            )

        audit_report = self.prompt_constructor.audit_coverage(
            plan=metadata.get('newsletter_plan', {}),
            pack=metadata.get('anchored_outline', {}),
            outline=outline,
            draft_text=content
        )

        if self.prompt_constructor.audit_failed(audit_report):
            fixed = self.prompt_constructor.apply_fixes(
                draft_text=content,
                audit_report=audit_report,
                plan=metadata.get('newsletter_plan', {}),
                pack=metadata.get('anchored_outline', {}),
                outline=outline
            )
            # re-audit once
            audit_report_fixed = self.prompt_constructor.audit_coverage(
                plan=metadata.get('newsletter_plan', {}),
                pack=metadata.get('anchored_outline', {}),
                outline=outline,
                draft_text=fixed
            )
            result = build_result(fixed, {'audit': audit_report_fixed})
        else:
            result = build_result(content, {'audit': audit_report})
        
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
