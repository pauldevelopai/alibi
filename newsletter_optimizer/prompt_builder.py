"""
Intelligent Prompt Builder for Newsletter Generation

This module constructs the OPTIMAL prompt by:
1. Analyzing the outline to understand what's needed
2. Retrieving relevant facts from Knowledge Base (semantic search)
3. Finding similar passages from past newsletters (RAG)
4. Selecting appropriate style guidance from Newsletter Bible
5. Assembling everything into a well-structured prompt

The goal: Give the generation model EXACTLY what it needs, no more, no less.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Load environment
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Import our modules
try:
    from rag_system import retrieve_relevant_passages, get_writing_examples
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

try:
    from knowledge_base import (
        semantic_search_facts,
        semantic_search_articles,
        get_relevant_facts,
        get_knowledge_context,
    )
    KB_AVAILABLE = True
except ImportError:
    KB_AVAILABLE = False

try:
    from style_analyzer import load_bible
    from deep_style_analyzer import load_deep_bible, get_deep_style_context
    BIBLE_AVAILABLE = True
except ImportError:
    BIBLE_AVAILABLE = False

try:
    from embeddings import SENTENCE_TRANSFORMERS_AVAILABLE
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

DATA_DIR = Path(__file__).parent / "data"

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ============================================================================
# Prompt Templates
# ============================================================================

SYSTEM_PROMPT_TEMPLATE = """You are Paul McNally, a journalist and AI expert writing the "Develop AI" newsletter for newsrooms and content creators in Africa and Asia.

{style_context}

CRITICAL RULES:
1. Write EXACTLY like Paul - use his voice, tone, and style
2. Be conversational but informative
3. Include practical takeaways
4. Reference sources when using facts
5. Keep the energy and enthusiasm authentic
"""

GENERATION_PROMPT_TEMPLATE = """# NEWSLETTER TO WRITE

## OUTLINE
{outline}

## RELEVANT FACTS & DATA (cite these!)
{facts_context}

## EXAMPLES FROM YOUR PAST WRITING (match this style!)
{rag_examples}

## INSTRUCTIONS
Write this newsletter section following the outline above.
- Match the voice and style from the examples
- Incorporate relevant facts with citations
- Keep it engaging and practical
- Target length: {target_length} words
"""


# ============================================================================
# Context Retrieval Functions
# ============================================================================

def analyze_outline(outline: str, quality_mode: bool = True) -> Dict:
    """
    Use AI to analyze the outline and extract key topics for retrieval.
    
    Returns topics, entities, and suggested fact types to search for.
    """
    model = "gpt-4o" if quality_mode else "gpt-4o-mini"
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Analyze this newsletter outline and extract key information for context retrieval."
            },
            {
                "role": "user", 
                "content": f"""Analyze this outline and return JSON with:
- main_topics: list of 3-5 main topics/themes
- search_queries: list of 3-5 semantic search queries to find relevant facts
- fact_types: what types of facts would be useful (statistics, quotes, examples, etc.)
- tone: the intended tone (informative, urgent, celebratory, etc.)

OUTLINE:
{outline}

Return ONLY valid JSON."""
            }
        ],
        temperature=0.3,
        max_tokens=500
    )
    
    try:
        return json.loads(response.choices[0].message.content)
    except:
        return {
            'main_topics': [outline[:100]],
            'search_queries': [outline[:100]],
            'fact_types': ['statistics', 'quotes'],
            'tone': 'informative'
        }


def get_relevant_facts_for_outline(outline: str, max_facts: int = 10, quality_mode: bool = True) -> str:
    """
    Get facts from knowledge base that are relevant to the outline.
    Uses semantic search if available, falls back to keyword matching.
    """
    if not KB_AVAILABLE:
        return ""
    
    # Analyze outline to get search queries (GPT-4o in quality mode)
    analysis = analyze_outline(outline, quality_mode=quality_mode)
    search_queries = analysis.get('search_queries', [outline[:200]])
    
    all_facts = []
    seen_facts = set()
    
    for query in search_queries:
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            facts = semantic_search_facts(query, limit=5, min_similarity=0.25)
        else:
            facts = get_relevant_facts(query, max_facts=5, min_relevance=2.0)
        
        for fact in facts:
            fact_text = fact.get('fact_text', '')
            if fact_text and fact_text not in seen_facts:
                seen_facts.add(fact_text)
                all_facts.append(fact)
    
    if not all_facts:
        return ""
    
    # Format facts with citations
    context = ""
    for i, fact in enumerate(all_facts[:max_facts], 1):
        fact_text = fact.get('fact_text', '')
        source = fact.get('source_title', fact.get('source_url', 'Unknown'))
        url = fact.get('source_url', '')
        similarity = fact.get('similarity', fact.get('relevance_score', 0))
        
        context += f"{i}. {fact_text}\n"
        context += f"   Source: {source}"
        if url:
            context += f" ({url})"
        context += f"\n"
        if similarity:
            context += f"   Relevance: {similarity:.0%}\n" if isinstance(similarity, float) and similarity <= 1 else f"   Score: {similarity}\n"
        context += "\n"
    
    return context


def get_rag_examples_for_outline(outline: str, num_examples: int = 5) -> str:
    """
    Get relevant passages from past newsletters using RAG.
    """
    if not RAG_AVAILABLE:
        return ""
    
    # Use the outline directly for semantic search
    return get_writing_examples(outline, num_examples=num_examples)


def get_style_context() -> str:
    """
    Get style context from Newsletter Bible and Deep Analysis.
    """
    if not BIBLE_AVAILABLE:
        return ""
    
    context = ""
    
    # Load Newsletter Bible
    bible = load_bible()
    if bible:
        # Key style elements
        voice = bible.get('writing_voice', {})
        if voice:
            context += "## YOUR WRITING VOICE\n"
            
            tone = voice.get('tone_descriptors', [])
            if tone:
                context += f"Tone: {', '.join(tone[:5])}\n"
            
            perspective = voice.get('perspective', '')
            if perspective:
                context += f"Perspective: {perspective}\n"
            
            sig_phrases = voice.get('signature_phrases', [])
            if sig_phrases:
                context += f"Signature phrases: {', '.join(sig_phrases[:5])}\n"
            
            context += "\n"
        
        # Section patterns
        sections = bible.get('section_patterns', {})
        if sections:
            intros = sections.get('intro_patterns', [])
            if intros:
                context += f"Intro style examples:\n"
                for intro in intros[:2]:
                    context += f"  - \"{intro[:100]}...\"\n"
            context += "\n"
    
    # Add deep analysis context
    deep_context = get_deep_style_context()
    if deep_context:
        context += deep_context
    
    return context


# ============================================================================
# Main Prompt Builder
# ============================================================================

def build_newsletter_prompt(
    outline: str,
    target_length: int = 800,
    include_facts: bool = True,
    include_rag: bool = True,
    include_style: bool = True,
    max_facts: int = 10,
    max_rag_examples: int = 5,
    quality_mode: bool = True
) -> Tuple[str, str, Dict]:
    """
    Build the optimal prompt for newsletter generation.
    
    Args:
        outline: The newsletter outline/structure
        target_length: Target word count for output
        include_facts: Whether to include knowledge base facts
        include_rag: Whether to include RAG examples
        include_style: Whether to include style context
        max_facts: Maximum facts to include
        max_rag_examples: Maximum RAG passages to include
    
    Returns:
        Tuple of (system_prompt, user_prompt, metadata)
    """
    metadata = {
        'outline_length': len(outline),
        'timestamp': datetime.now().isoformat(),
        'quality_mode': quality_mode,
        'analysis_model': 'gpt-4o' if quality_mode else 'gpt-4o-mini',
        'components_included': []
    }
    
    # 1. Get style context
    style_context = ""
    if include_style:
        style_context = get_style_context()
        if style_context:
            metadata['components_included'].append('style_bible')
    
    # 2. Build system prompt
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        style_context=style_context if style_context else "Write in Paul's characteristic conversational, informative style."
    )
    
    # 3. Get facts from knowledge base
    facts_context = ""
    if include_facts:
        facts_context = get_relevant_facts_for_outline(outline, max_facts, quality_mode=quality_mode)
        if facts_context:
            metadata['components_included'].append('knowledge_base_facts')
            metadata['facts_count'] = facts_context.count('\n\n')
    
    # 4. Get RAG examples
    rag_examples = ""
    if include_rag:
        rag_examples = get_rag_examples_for_outline(outline, max_rag_examples)
        if rag_examples:
            metadata['components_included'].append('rag_examples')
    
    # 5. Build generation prompt
    user_prompt = GENERATION_PROMPT_TEMPLATE.format(
        outline=outline,
        facts_context=facts_context if facts_context else "(No specific facts retrieved - use general knowledge)",
        rag_examples=rag_examples if rag_examples else "(No specific examples - write in Paul's conversational tech journalism style)",
        target_length=target_length
    )
    
    # Calculate token estimates
    import tiktoken
    try:
        enc = tiktoken.encoding_for_model("gpt-4o")
        metadata['system_tokens'] = len(enc.encode(system_prompt))
        metadata['user_tokens'] = len(enc.encode(user_prompt))
        metadata['total_prompt_tokens'] = metadata['system_tokens'] + metadata['user_tokens']
    except:
        metadata['total_prompt_tokens'] = len(system_prompt.split()) + len(user_prompt.split())
    
    return system_prompt, user_prompt, metadata


def generate_newsletter_quality(
    outline: str,
    target_length: int = 800,
    temperature: float = 0.7
) -> Dict:
    """
    Generate newsletter using QUALITY mode - GPT-4o at every step.
    
    This is the premium pipeline:
    1. GPT-4o analyzes outline for optimal retrieval
    2. Semantic search finds best facts & examples
    3. GPT-4o generates the final content
    """
    # Build prompt with quality analysis
    system_prompt, user_prompt, metadata = build_newsletter_prompt(
        outline=outline,
        target_length=target_length,
        quality_mode=True
    )
    
    metadata['pipeline'] = 'quality'
    metadata['model'] = 'gpt-4o'
    
    # Generate with GPT-4o
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        max_tokens=target_length * 2
    )
    
    content = response.choices[0].message.content
    
    metadata['output_tokens'] = response.usage.completion_tokens
    metadata['total_tokens'] = response.usage.total_tokens
    metadata['output_words'] = len(content.split())
    
    return {
        'content': content,
        'metadata': metadata,
        'system_prompt': system_prompt,
        'user_prompt': user_prompt
    }


def generate_newsletter(
    outline: str,
    model: str = "gpt-4o",
    target_length: int = 800,
    temperature: float = 0.7,
    use_fine_tuned: bool = False,
    fine_tuned_model: str = None,
    quality_mode: bool = True
) -> Dict:
    """
    Generate a newsletter section using the intelligent prompt builder.
    
    Args:
        outline: The outline to generate from
        model: Base model to use (gpt-4o, gpt-4o-mini, etc.)
        target_length: Target word count
        temperature: Generation temperature
        use_fine_tuned: Whether to use fine-tuned model
        fine_tuned_model: Specific fine-tuned model ID
    
    Returns:
        Dict with generated content, metadata, and prompt info
    """
    # Build the optimal prompt
    system_prompt, user_prompt, metadata = build_newsletter_prompt(
        outline=outline,
        target_length=target_length
    )
    
    # Determine which model to use
    if use_fine_tuned and fine_tuned_model:
        generation_model = fine_tuned_model
        metadata['model_type'] = 'fine-tuned'
    else:
        generation_model = model
        metadata['model_type'] = 'base'
    
    metadata['model'] = generation_model
    
    # Generate
    response = client.chat.completions.create(
        model=generation_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        max_tokens=target_length * 2  # Allow some buffer
    )
    
    content = response.choices[0].message.content
    
    # Add response metadata
    metadata['output_tokens'] = response.usage.completion_tokens
    metadata['total_tokens'] = response.usage.total_tokens
    metadata['output_words'] = len(content.split())
    
    return {
        'content': content,
        'metadata': metadata,
        'system_prompt': system_prompt,
        'user_prompt': user_prompt
    }


# ============================================================================
# Model Recommendation
# ============================================================================

def recommend_model(outline: str, priority: str = "quality") -> Dict:
    """
    Recommend the best model based on the outline and priority.
    
    Args:
        outline: The newsletter outline
        priority: "quality", "speed", or "cost"
    
    Returns:
        Model recommendation with reasoning
    """
    # Analyze complexity
    word_count = len(outline.split())
    has_technical = any(word in outline.lower() for word in ['code', 'technical', 'algorithm', 'api', 'programming'])
    has_analysis = any(word in outline.lower() for word in ['analysis', 'compare', 'evaluate', 'research', 'study'])
    is_long_form = word_count > 200 or 'deep dive' in outline.lower()
    
    recommendations = {
        "quality": {
            "model": "gpt-4o",
            "reasoning": "Best overall quality, handles nuance well",
            "use_fine_tuned": False,  # Use base with rich context
            "estimated_cost": "$0.02-0.05 per generation"
        },
        "speed": {
            "model": "gpt-4o-mini",
            "reasoning": "Fast and good quality for iterations",
            "use_fine_tuned": False,
            "estimated_cost": "$0.001-0.003 per generation"
        },
        "cost": {
            "model": "gpt-4o-mini",
            "reasoning": "Most cost-effective while maintaining quality",
            "use_fine_tuned": False,
            "estimated_cost": "$0.001-0.003 per generation"
        },
        "voice_match": {
            "model": "fine-tuned",
            "reasoning": "Your fine-tuned model knows your voice best",
            "use_fine_tuned": True,
            "estimated_cost": "Varies by base model"
        }
    }
    
    # Adjust based on content
    rec = recommendations.get(priority, recommendations["quality"]).copy()
    
    if has_technical and priority == "quality":
        rec["notes"] = "Technical content detected - GPT-4o handles this best"
    
    if is_long_form:
        rec["notes"] = rec.get("notes", "") + " Long-form content - consider breaking into sections"
    
    if has_analysis:
        rec["model"] = "gpt-4o"
        rec["notes"] = rec.get("notes", "") + " Analysis content benefits from GPT-4o's reasoning"
    
    return rec


# ============================================================================
# Status and Testing
# ============================================================================

def get_prompt_builder_status() -> Dict:
    """Get status of all prompt builder components."""
    return {
        'rag_available': RAG_AVAILABLE,
        'knowledge_base_available': KB_AVAILABLE,
        'bible_available': BIBLE_AVAILABLE,
        'semantic_search': SENTENCE_TRANSFORMERS_AVAILABLE,
        'components': {
            'outline_analysis': True,  # Always available (uses OpenAI)
            'fact_retrieval': KB_AVAILABLE,
            'rag_examples': RAG_AVAILABLE,
            'style_context': BIBLE_AVAILABLE,
        }
    }


# ============================================================================
# CLI Test
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("INTELLIGENT PROMPT BUILDER")
    print("=" * 60)
    
    # Check status
    status = get_prompt_builder_status()
    print("\n📊 Component Status:")
    for component, available in status['components'].items():
        icon = "✅" if available else "❌"
        print(f"   {icon} {component}")
    
    # Test with sample outline
    test_outline = """
    # This Week in AI for African Newsrooms
    
    ## Opening
    - Hook about recent AI development in Africa
    - What this means for journalists
    
    ## Main Story: AI Tools Launch
    - New AI tools specifically for African languages
    - How newsrooms can use them
    - Cost considerations
    
    ## Practical Tips
    - 3 ways to start using AI today
    - Common mistakes to avoid
    
    ## Closing
    - Call to action
    - What's coming next week
    """
    
    print("\n📝 Test Outline:")
    print(test_outline[:200] + "...")
    
    print("\n🔧 Building prompt...")
    system_prompt, user_prompt, metadata = build_newsletter_prompt(test_outline)
    
    print("\n📊 Prompt Metadata:")
    for key, value in metadata.items():
        print(f"   {key}: {value}")
    
    print("\n🎯 Model Recommendation:")
    rec = recommend_model(test_outline, priority="quality")
    for key, value in rec.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 60)
