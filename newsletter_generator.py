"""
Newsletter Generator - AI Writer Trained on Paul McNally's Style

Uses the Newsletter Bible + sample newsletters to generate new content
that matches Paul's voice, style, and proven formulas.
"""

import os
import json
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

from style_analyzer import load_bible, load_all_newsletters, html_to_text

# Deep style analyzer for enhanced writing style context
try:
    from deep_style_analyzer import get_deep_style_context, load_deep_bible
    DEEP_STYLE_AVAILABLE = True
except ImportError:
    DEEP_STYLE_AVAILABLE = False
    def get_deep_style_context(topic: str = "") -> str:
        return ""
    def load_deep_bible():
        return {}

# Try to import learning system
try:
    from learning_system import get_learning_context
    LEARNING_AVAILABLE = True
except ImportError:
    LEARNING_AVAILABLE = False
    def get_learning_context():
        return ""

# Try to import RAG system
try:
    from rag_system import get_writing_examples, build_embeddings_database
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    def get_writing_examples(topic, num_examples=5):
        return ""

# Try to import fine-tuning system
try:
    from fine_tuning import get_active_fine_tuned_model
    FINE_TUNING_AVAILABLE = True
except ImportError:
    FINE_TUNING_AVAILABLE = False
    def get_active_fine_tuned_model():
        return None

# Try to import knowledge base for content context
try:
    from knowledge_base import get_knowledge_context, get_relevant_facts_context, mark_facts_as_used
    KNOWLEDGE_BASE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_BASE_AVAILABLE = False
    def get_knowledge_context(*args, **kwargs):
        return ""

# Try to import performance learnings from newsletter database
try:
    from newsletter_database import get_performance_learnings
    PERFORMANCE_LEARNINGS_AVAILABLE = True
except ImportError:
    PERFORMANCE_LEARNINGS_AVAILABLE = False
    def get_performance_learnings():
        return ""
    def get_relevant_facts_context(*args, **kwargs):
        return "", []
    def mark_facts_as_used(*args, **kwargs):
        pass

# Try to import news fetcher for real news in outlines
try:
    from news_fetcher import get_recent_ai_news, fetch_last_two_days
    NEWS_FETCHER_AVAILABLE = True
except ImportError:
    NEWS_FETCHER_AVAILABLE = False
    def get_recent_ai_news(*args, **kwargs):
        return []
    def fetch_last_two_days(*args, **kwargs):
        return []

# Try to import usage logging
try:
    from openai_dashboard import log_api_call
    USAGE_LOGGING_AVAILABLE = True
except ImportError:
    USAGE_LOGGING_AVAILABLE = False
    def log_api_call(*args, **kwargs):
        pass


# Load environment
load_dotenv()

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Paths
DATA_DIR = Path(__file__).parent / "data"
BIBLE_FILE = DATA_DIR / "newsletter_bible.json"

# Model for generation - using a capable model for creative writing
DEFAULT_GENERATION_MODEL = "gpt-4.1"  # Fallback model for full newsletter generation
FALLBACK_MODEL = "gpt-4o"  # Fallback if gpt-4.1 not available


def get_fine_tuned_model_tier() -> str:
    """
    Determine the tier of the active fine-tuned model.
    Returns: 'gpt-4o', 'gpt-4o-mini', or None
    """
    if not FINE_TUNING_AVAILABLE:
        return None
    
    fine_tuned = get_active_fine_tuned_model()
    if not fine_tuned:
        return None
    
    # Parse the model name to determine tier
    # Fine-tuned models look like: ft:gpt-4o-2024-08-06:org:suffix:id
    # or: ft:gpt-4o-mini-2024-07-18:org:suffix:id
    model_lower = fine_tuned.lower()
    if 'gpt-4o-mini' in model_lower:
        return 'gpt-4o-mini'
    elif 'gpt-4o' in model_lower:
        return 'gpt-4o'
    return None


def get_generation_model(task_type: str = "full") -> str:
    """
    Get the model to use for generation based on task type AND fine-tuned model tier.
    
    SMART MODEL SELECTION:
    
    If fine-tuned gpt-4o is available:
    - Use it directly for ALL tasks (single-stage generation)
    - Your voice + powerful reasoning in one model
    
    If fine-tuned gpt-4o-mini is available:
    - Use it for short tasks (headlines, style prompts)
    - Use GPT-4.1 for full newsletter (two-stage generation)
    
    If no fine-tuned model:
    - Use GPT-4.1 for everything
    
    Args:
        task_type: "full" for full newsletter, "short" for headlines/ideas
    """
    if FINE_TUNING_AVAILABLE:
        fine_tuned = get_active_fine_tuned_model()
        if fine_tuned:
            tier = get_fine_tuned_model_tier()
            
            # GPT-4o fine-tuned: Use for EVERYTHING (single-stage)
            if tier == 'gpt-4o':
                return fine_tuned
            
            # GPT-4o-mini fine-tuned: Only use for short tasks
            if tier == 'gpt-4o-mini':
                if task_type == "short":
                    return fine_tuned
                else:
                    # For full newsletter, use GPT-4.1 (two-stage generation)
                    return DEFAULT_GENERATION_MODEL
    
    return DEFAULT_GENERATION_MODEL


def should_use_two_stage_generation() -> bool:
    """
    Determine if we should use two-stage generation.
    
    Two-stage is needed when:
    - Fine-tuned model is gpt-4o-mini (not powerful enough for full generation)
    
    Single-stage is used when:
    - Fine-tuned model is gpt-4o (powerful enough on its own)
    - No fine-tuned model (just use GPT-4.1)
    """
    tier = get_fine_tuned_model_tier()
    return tier == 'gpt-4o-mini'


# Legacy alias for backwards compatibility
GENERATION_MODEL = DEFAULT_GENERATION_MODEL


# ============================================================================
# Build Training Context
# ============================================================================

def get_style_context(bible: dict) -> str:
    """Build a style guide context from the Newsletter Bible."""
    
    context = """# PAUL MCNALLY'S NEWSLETTER STYLE GUIDE

You are writing as Paul McNally, author of the Develop AI newsletter on Substack.
This newsletter is read by journalists, editors, and media decision-makers interested in AI, regulation, and the future of news.

## ⚠️ CRITICAL: WHAT MAKES PAUL'S WRITING DISTINCTIVE

Paul's writing is:
- PUNCHY, not verbose. Short sentences. Then longer ones for depth. Then short again.
- PERSONAL. "I spoke to..." "When I was at..." "I've been thinking about..."
- SPECIFIC. Real names. Real links. Real projects. Real quotes.
- SKEPTICAL of hype but CURIOUS about possibilities
- GROUNDED in African/Global South perspectives
- DIRECT. No corporate speak. No filler words. No "In today's rapidly evolving landscape..."

Paul's writing is NOT:
- Verbose or wordy
- Full of clichés like "game-changer" or "revolutionize"
- Generic or applicable to any newsletter
- Full of invented statistics or fake sources
- Breathlessly positive about AI
- Written like a marketing brochure

## VOICE EXAMPLES

BAD (generic AI-speak):
"AI tools are quietly transforming every step of the process. If you're not using them, you're already behind."

GOOD (Paul's actual voice):
"I've been playing with NotebookLM for a few weeks now. It's interesting. Not revolutionary, but interesting."

BAD (verbose):
"The leading edge of newsletter publishing isn't coming from major newsrooms alone. It's coming from people and teams who are using AI to do real work, every day."

GOOD (punchy):
"The big publishers are scrambling. But the interesting stuff? It's happening in Lagos. In Nairobi. In small newsrooms with no budget but a lot of ideas."

## STRUCTURE RULES
"""
    
    context += f"""
- Keep it SHORT: {bible.get('structure_blueprint', {}).get('avg_word_count', 800):.0f} words max for main story
- Paragraphs: 2-3 sentences MAX. Then break.
- Use bold text for section headers, not just H2 tags
- Mix: personal anecdote → analysis → specific example → question to reader

## WHAT MUST BE IN EVERY NEWSLETTER

1. **Specific names and sources**: Real people, real publications, real links
2. **A personal angle**: "I tried this..." or "I spoke to..." or "I was at..."
3. **Current events**: Reference things happening NOW, not generic trends
4. **Africa/Global South perspective**: At least one reference
5. **Practical takeaway**: What can the reader actually DO with this?
6. **Skepticism**: Question the hype, ask who benefits, note what's missing

## ⛔ NEVER DO THIS

1. **NEVER invent statistics or studies** - If you don't have real data, don't make it up
2. **NEVER use phrases like**:
   - "The landscape is evolving"
   - "Game-changer"
   - "In today's world"
   - "Transformative potential"
   - "Revolutionary"
3. **NEVER write generic content** that could apply to any newsletter
4. **NEVER write walls of text** - break it up
5. **NEVER be breathlessly positive** about AI - maintain healthy skepticism
6. **NEVER use placeholder sources** like "A recent report from..." without specifics

## SIGNATURE VOCABULARY
Use these words Paul actually uses:
{', '.join(bible.get('writing_voice', {}).get('signature_vocabulary', [])[:20])}

## SENTENCE PATTERNS PAUL USES
- Start with "I" sometimes: "I've been..." "I spoke to..." "I tried..."
- Use "you" directly: "You've probably seen..." "You should try..."
- Short punchy sentences: "That's the problem." "It won't work." "Here's why."
- Questions to reader: "So what does this mean for you?"
"""
    
    return context


def get_sample_newsletters(newsletters: list[dict], n: int = 3) -> str:
    """Get sample newsletters as training examples - fewer but more complete."""
    
    samples = """# REAL EXAMPLES FROM PAUL'S NEWSLETTERS

Study these carefully. Notice:
- The short paragraphs
- The personal voice ("I spoke to...", "I've been...")
- The specific names and sources
- The skeptical but curious tone
- The punchy sentences mixed with longer analysis

"""
    
    # Get a diverse sample - try to get newsletters with good open rates
    for i, newsletter in enumerate(newsletters[:n], 1):
        title = newsletter.get('title', 'Untitled')
        content = html_to_text(newsletter.get('content_html', ''))
        
        # Get more content for better examples
        if len(content) > 3000:
            content = content[:3000] + "\n\n[... newsletter continues ...]"
        
        samples += f"""
================================================================================
EXAMPLE {i}: "{title}"
================================================================================

{content}

"""
    
    samples += """
================================================================================
END OF EXAMPLES
================================================================================

Now write in THIS style - not generic AI content. Be Paul.
"""
    
    return samples


# ============================================================================
# Newsletter Generation Prompts
# ============================================================================

def build_generation_prompt(
    idea: str,
    bible: dict,
    newsletters: list[dict],
    format_type: str = "full",
    additional_instructions: str = "",
    outline_data: dict = None
) -> tuple:
    """
    Build the system and user prompts for newsletter generation.
    
    Returns:
        Tuple of (system_prompt, user_prompt, facts_used)
        where facts_used is a list of fact dicts that were injected.
    """
    
    # System prompt with style context
    style_context = get_style_context(bible)
    sample_context = get_sample_newsletters(newsletters, n=3)  # Reduced since we have RAG
    
    # Get learning context from user's previous edits
    learning_context = get_learning_context()
    
    # Get RAG context - relevant passages from past newsletters on this topic
    rag_context = ""
    if RAG_AVAILABLE and idea:
        try:
            rag_context = get_writing_examples(idea, num_examples=5)
            if rag_context:
                rag_context = f"\n\n{rag_context}\n\n"
        except Exception as e:
            print(f"RAG retrieval error: {e}")
            rag_context = ""
    
    # Get knowledge base context - factual information about AI, Africa, media
    # This provides WHAT to write about (facts, sources, data)
    # The style context provides HOW to write (your voice)
    knowledge_context = ""
    facts_context = ""
    facts_used = []
    
    if KNOWLEDGE_BASE_AVAILABLE:
        try:
            # Get article-level context
            knowledge_context = get_knowledge_context(topic=idea, max_articles=8, max_chars=4000)
            if knowledge_context:
                knowledge_context = f"\n\n{knowledge_context}\n\n"
            
            # NEW: Get automatically matched, citable facts
            facts_context, facts_used = get_relevant_facts_context(
                topic=idea, 
                max_facts=12,
                max_chars=3000
            )
            if facts_context:
                facts_context = f"\n\n{facts_context}\n\n"
                
        except Exception as e:
            print(f"Knowledge base error: {e}")
            knowledge_context = ""
            facts_context = ""
    
    # Get performance learnings from past newsletters
    # This includes notes on what worked, what didn't, and Substack metrics
    performance_context = ""
    if PERFORMANCE_LEARNINGS_AVAILABLE:
        try:
            performance_learnings = get_performance_learnings()
            if performance_learnings:
                performance_context = f"""

## PERFORMANCE LEARNINGS FROM PAST NEWSLETTERS

The following are insights from the author's published newsletters and their Substack performance.
Use these learnings to guide your writing - emulate what worked, avoid what didn't:

{performance_learnings}
"""
        except Exception as e:
            print(f"Performance learnings error: {e}")
            performance_context = ""
    
    system_prompt = f"""{style_context}

{sample_context}

{rag_context}

{learning_context}

{knowledge_context}

{facts_context}

{performance_context}

You are now ready to write a new newsletter in Paul McNally's voice and style.
Match his tone, structure, vocabulary, and approach exactly.

# 🚨🚨🚨 THE MOST IMPORTANT RULE: DO NOT LIE 🚨🚨🚨

**NEVER FABRICATE:**
- Personal experiences or anecdotes you don't know are real
- Places, dates, or events (e.g., "I was in Zanzibar when...")
- Workshops, talks, or meetings unless specified in the outline
- Statistics, percentages, or data unless from a provided source
- Quotes from anyone unless provided
- Partnerships or collaborations unless specified

**THE RULE:** If it's a specific claim about a person, place, event, date, or statistic - and it wasn't provided by the user or in the sources - DO NOT INCLUDE IT.

**YOU CAN WRITE:**
- Analysis and opinions (these don't need sources)
- The user's key points from their outline (they wrote these!)
- General discussion of AI tools and concepts
- Content based on provided sources with citations

THE MOST IMPORTANT THING: Use the writing examples above as your template.
Copy their rhythm, their sentence structure, their way of making points.
DO NOT write like a generic AI. Write EXACTLY like those examples.

## 📊 USING THE KNOWLEDGE BASE AND FACTS

1. **CITABLE FACTS** (above): These facts have been automatically matched to your topic.
   - Each fact includes a ready-to-use [Source](URL) citation
   - Weave relevant facts naturally into your writing
   - Prioritize 🟢 high-confidence facts over 🟡 medium or 🟠 low
   - ALWAYS include the citation link when using a fact

2. **ARTICLES** (above): Use these for broader context and additional sources.
   - Cite with inline links: [Source Name](URL)

3. **STRICT RULE**: If you reference data, statistics, or claims:
   - It MUST come from the Knowledge Base above
   - It MUST have the citation included
   - If it's not in the Knowledge Base, DON'T invent it
"""
    
    # User prompt based on format type
    if format_type == "full":
        user_prompt = f"""Write a complete newsletter based on this idea:

**IDEA:** {idea}

{additional_instructions}

Return the newsletter in this format:

## HEADLINE
[Your headline - follow Paul's headline formulas]

## PREVIEW
[2-3 sentence preview/subtitle for email]

## BODY
[Full newsletter body - approximately {bible.get('structure_blueprint', {}).get('avg_word_count', 1000):.0f} words]
[Use Paul's voice, structure, and style exactly]
[Include 2-3 H2 section headings]
[End with a thought-provoking close]
"""
    
    elif format_type == "headlines_only":
        user_prompt = f"""Generate 10 headline options for this newsletter idea:

**IDEA:** {idea}

{additional_instructions}

For each headline, use a DIFFERENT approach from Paul's proven formulas:
1. Provocative question
2. Colon structure (Topic: Angle)
3. Number/listicle style
4. Future prediction ("Will X...")
5. Confrontational ("X vs Y")
6. How-to practical
7. Contrarian take
8. Global South angle
9. Dramatic/urgent
10. Clear explanatory

Return each headline numbered 1-10.
"""
    
    elif format_type == "outline":
        # Check if user requested extra sections (will be in additional_instructions)
        has_extra_sections = "NEWSLETTER STRUCTURE" in additional_instructions and "sections" in additional_instructions.lower()
        
        # Build the JSON structure based on whether extra sections are requested
        if has_extra_sections:
            json_structure = '''{{
    "headline_options": [
        "Headline option 1 - how-to style",
        "Headline option 2 - provocative statement", 
        "Headline option 3 - Africa/Global South angle",
        "Headline option 4 - dramatic with ellipsis",
        "Headline option 5 - practical/clear"
    ],
    "preview_options": [
        "Preview option 1 - 2 sentences max",
        "Preview option 2 - different angle"
    ],
    "opening_hook": "A compelling first paragraph that grabs attention. Make it personal, provocative, or surprising.",
    "main_story": {{
        "heading": "Main Story Heading (based on the idea)",
        "structure": [
            "Opening: [Specific hook for THIS story - not generic]",
            "Context: [Why THIS specific issue/topic matters now]",
            "Analysis: [The specific angle or insight for THIS story]", 
            "Examples: [What specific examples/data will illustrate THIS point]",
            "Impact: [How THIS affects readers/industry/region]",
            "Takeaway: [What readers should specifically do or think about THIS]"
        ],
        "key_points": [
            "Key insight 1 specific to THIS idea",
            "Key insight 2 specific to THIS idea",
            "Key insight 3 specific to THIS idea"
        ],
        "target_word_count": 600,
        "notes": "This should be 400-600 words. The main intellectual substance of the newsletter."
    }},
    "additional_sections": [
        {{
            "type": "section_type_from_instructions",
            "heading": "Section Heading",
            "bullet_points": [
                "Point 1 to cover",
                "Point 2 to cover"
            ],
            "target_word_count": 100,
            "notes": "Brief notes"
        }}
    ],
    "closing_approach": "Description of how to end - thought-provoking, call to action, or forward-looking",
    "suggested_links": [
        "Search suggestion 1 - what to look for",
        "Search suggestion 2 - what to look for"
    ],
    "image_prompts": [
        "DALL-E prompt 1: A detailed, specific image description for the newsletter header",
        "DALL-E prompt 2: Alternative visual approach for the main story"
    ],
    "tone_notes": "Brief notes on the overall tone to strike"
}}'''
            # Check if news section is requested and fetch real news
            real_news_context = ""
            has_news_section = "news" in additional_instructions.lower() or "roundup" in additional_instructions.lower()
            
            if has_news_section and NEWS_FETCHER_AVAILABLE:
                try:
                    recent_news = get_recent_ai_news(days=3)
                    if recent_news:
                        real_news_context = "\n\n## 📰 REAL NEWS FOR YOUR NEWS SECTION (use these - they are verified!)\n\n"
                        real_news_context += "These are REAL recent news stories with working URLs. Use them in your news roundup section:\n\n"
                        for i, article in enumerate(recent_news[:8], 1):
                            title = article.get('title', 'Untitled')
                            url = article.get('url', '')
                            source = article.get('source', 'Unknown')
                            published = article.get('published', '')[:10] if article.get('published') else ''
                            summary = article.get('summary', '')[:200] if article.get('summary') else ''
                            
                            real_news_context += f"{i}. **{title}**\n"
                            real_news_context += f"   - Source: {source}\n"
                            real_news_context += f"   - URL: {url}\n"
                            if published:
                                real_news_context += f"   - Date: {published}\n"
                            if summary:
                                real_news_context += f"   - Summary: {summary}...\n"
                            real_news_context += "\n"
                except Exception as e:
                    print(f"Could not fetch news for outline: {e}")
            
            extra_sections_instructions = f"""
IMPORTANT: The user has requested EXTRA SECTIONS (see NEWSLETTER STRUCTURE above).
Create additional_sections based on the section types they selected.
ONLY include the section types they specified - no more, no less.
{real_news_context}

🚨 CRITICAL - NEWS MUST BE REAL 🚨

For any news/roundup sections:
1. **USE THE REAL NEWS ABOVE** - If real news is provided above, use those stories with their actual URLs
2. **INCLUDE THE URL** - Every news item MUST have the real URL from the list above
3. **NO FAKE NEWS** - Do NOT invent stories. Only use the verified news provided above.
4. If no real news was provided, use "[TOPIC] Description | Search: 'search terms'" format

For "develop_ai" or personal update sections:
- Use "[USER TO ADD]" placeholders - the user will fill in their own updates
"""
        else:
            # NO extra sections - main story only
            json_structure = '''{{
    "headline_options": [
        "Headline option 1 - how-to style",
        "Headline option 2 - provocative statement", 
        "Headline option 3 - Africa/Global South angle",
        "Headline option 4 - dramatic with ellipsis",
        "Headline option 5 - practical/clear"
    ],
    "preview_options": [
        "Preview option 1 - 2 sentences max",
        "Preview option 2 - different angle"
    ],
    "opening_hook": "A compelling first paragraph that grabs attention. Make it personal, provocative, or surprising.",
    "main_story": {{
        "heading": "Main Story Heading (based on the idea)",
        "structure": [
            "Opening: [Specific hook for THIS story - not generic]",
            "Context: [Why THIS specific issue/topic matters now]",
            "Analysis: [The specific angle or insight for THIS story]", 
            "Examples: [What specific examples/data will illustrate THIS point]",
            "Impact: [How THIS affects readers/industry/region]",
            "Takeaway: [What readers should specifically do or think about THIS]"
        ],
        "key_points": [
            "Key insight 1 specific to THIS idea",
            "Key insight 2 specific to THIS idea",
            "Key insight 3 specific to THIS idea"
        ],
        "target_word_count": 800,
        "notes": "This should be 600-800 words since there are no extra sections. The main intellectual substance of the newsletter."
    }},
    "additional_sections": [],
    "closing_approach": "Description of how to end - thought-provoking, call to action, or forward-looking",
    "suggested_links": [
        "Search suggestion 1 - what to look for",
        "Search suggestion 2 - what to look for"
    ],
    "image_prompts": [
        "DALL-E prompt 1: A detailed, specific image description for the newsletter header",
        "DALL-E prompt 2: Alternative visual approach for the main story"
    ],
    "tone_notes": "Brief notes on the overall tone to strike"
}}'''
            extra_sections_instructions = """
IMPORTANT: The user has requested MAIN STORY ONLY - no extra sections.
Set "additional_sections" to an empty array [].
Focus entirely on creating a comprehensive, detailed main_story.
The main story should be longer (600-800 words) since it's the only content.
"""
        
        user_prompt = f"""Create a detailed outline for this ONE SPECIFIC newsletter idea.
Every part of the outline (headlines, previews, main_story, additional_sections) must stay tightly focused on this idea and NOT drift to other topics:

**IDEA:** {idea}

{additional_instructions}

{extra_sections_instructions}

STRUCTURE RULES:
- "main_story": The MAIN STORY - a deep-dive article based on the idea. This is the PRIMARY content.
- "additional_sections": ONLY if user requested extra sections above. Otherwise, empty array [].
- "headline_options": 3-7 different headline ideas that are ALL clearly and directly about the IDEA above. Do NOT reuse headlines from other topics or past newsletters.
- "preview_options": 2-4 short previews/subtitles that feel like email preview text for THIS exact idea, not generic AI commentary.

🚨 CRITICAL - DO NOT INVENT SOURCES OR URLs 🚨

**SOURCES - CRITICAL RULES:**
1. **DO NOT INVENT URLs** - NEVER create fake article URLs like "https://techcrunch.com/2025/..." or "https://wired.com/ai-health"
2. **DO NOT INVENT ARTICLE TITLES** - NEVER create fake article headlines
3. **ONLY USE PROVIDED SOURCES** - If Knowledge Base or sources are provided above, use ONLY those URLs
4. **IF NO SOURCES PROVIDED** - Set "sources": [] (empty array) or use "suggested_links" with search terms ONLY
5. **FORMAT FOR SOURCES** - If sources ARE provided above with URLs, use them. Otherwise leave sources empty.

**Example of WRONG (inventing URLs):**
❌ "sources": [{{"title": "Google removes AI health summaries", "url": "https://techcrunch.com/2025/12/google-ai-health"}}]

**Example of CORRECT (no sources provided):**
✅ "sources": []
✅ "suggested_links": ["Search: 'Google AI health summaries removed 2025'", "Search: 'AI healthcare accuracy issues'"]

**IF YOU DON'T HAVE A REAL URL FROM THE KNOWLEDGE BASE OR PROVIDED SOURCES ABOVE, DO NOT CREATE ONE.**

Return a JSON object with this exact structure:
{json_structure}

Return ONLY valid JSON.
"""
    
    elif format_type == "from_outline":
        # Generate full newsletter from a user-edited outline
        if not outline_data:
            raise ValueError("outline_data required for from_outline format")
        
        # Build a summary of ALL user edits at the very top
        main_story = outline_data.get('main_story', {})
        additional_sections = outline_data.get('additional_sections', [])
        
        edits_summary = """
# 🚨 USER EDITS - YOU MUST INCLUDE ALL OF THESE 🚨

The user has edited this outline. Every edit below MUST appear in your output.

"""
        # Summarize main story edits
        if main_story.get('key_points'):
            edits_summary += "## MAIN STORY KEY POINTS (MUST INCLUDE ALL):\n"
            for i, point in enumerate(main_story.get('key_points', []), 1):
                edits_summary += f"{i}. {point}\n"
            edits_summary += "\n"
        
        if main_story.get('user_notes'):
            edits_summary += f"## USER'S NOTES FOR MAIN STORY:\n{main_story['user_notes']}\n\n"
        
        # Summarize additional sections edits
        for i, section in enumerate(additional_sections, 1):
            section_heading = section.get('heading', f'Section {i}')
            bullets = section.get('bullet_points', [])
            if bullets:
                edits_summary += f"## {section_heading.upper()} - POINTS TO COVER:\n"
                for j, bullet in enumerate(bullets, 1):
                    edits_summary += f"{j}. {bullet}\n"
                edits_summary += "\n"
            if section.get('user_notes'):
                edits_summary += f"User notes for {section_heading}: {section['user_notes']}\n\n"
        
        user_prompt = f"""{edits_summary}

---

Write a newsletter based on this outline.

# ⚠️ CRITICAL: READ THIS CAREFULLY

You are writing as Paul McNally. Here is what Paul's ACTUAL newsletters look like:

## REAL EXAMPLE FROM PAUL:

"I was in Moldova earlier this year speaking on AI and podcasting at their annual Podcast Fest and giving a workshop to a range of newsrooms from around the country on AI implementation. Thank you to DW Akademie for making this happen. Podcasting is largely video focused in the region and AI avatars, created with platforms like HeyGen, are becoming increasingly common.

**AI lesson:** You can use Cursor and ElevenLabs to build your own AI daily podcast on all the newsletters and news you find interesting (in a language of your choice) and listen to that while making your morning coffee. Contact me for more details on how to build this."

## WHAT MAKES THIS PAUL'S STYLE:

1. **REAL PLACES** - "I was in Moldova" - not "I spoke to a tech editor"
2. **REAL ORGANIZATIONS** - "DW Akademie" - not "a major media company"
3. **REAL TOOLS WITH NAMES** - "HeyGen", "Cursor", "ElevenLabs" - not "AI tools"
4. **PRACTICAL TAKEAWAYS** - "build your own AI daily podcast" - not vague advice
5. **SHORT PARAGRAPHS** - 2-3 sentences max
6. **BLOCKQUOTES FOR LESSONS** - formatted clearly
7. **PERSONAL EXPERIENCE** - "giving a workshop" - not generic observations

## 🚨🚨🚨 CRITICAL: DO NOT LIE OR FABRICATE 🚨🚨🚨

**THIS IS THE MOST IMPORTANT RULE. EVERYTHING YOU WRITE MUST BE TRUE.**

### YOU MUST NOT INVENT:
❌ Personal experiences ("I was in Zanzibar..." - unless the user wrote this)
❌ Anecdotes ("The idea was born on a hot day in..." - FAKE)
❌ Workshops or events you ran (unless explicitly stated in the outline)
❌ Organizations you worked with (unless in the provided sources/notes)
❌ Statistics or percentages (unless from a provided source with URL)
❌ Quotes from anyone (unless provided)
❌ Dates, places, or events (unless provided)

### EXAMPLES OF LIES TO AVOID:
❌ "The idea for Letter+ was born on a baking hot day in Zanzibar" - FABRICATED
❌ "I was working with DW Akademie on this project" - FABRICATED (unless stated)
❌ "Last week in Lagos, I met a journalist who..." - FABRICATED
❌ "45% of newsrooms are now using AI" - FABRICATED (no source)

### WHAT YOU CAN WRITE:
✅ General analysis and opinions (these don't need sources)
✅ Information from the user's outline notes (USE THESE - they are real)
✅ Information from provided sources with URLs
✅ Known facts about tools (ChatGPT, Cursor, etc. exist - you can discuss them)
✅ The user's stated key points and bullet points (these came from the user!)

### THE RULE:
**If the user didn't write it in their outline, and it's not from a provided source, and it's a specific claim about a person/place/event/statistic - DO NOT INCLUDE IT.**

Write analysis and opinions freely. But NEVER fabricate specific experiences, anecdotes, or data.

## STYLE GUIDELINES:
✅ Use numbered lists for lessons/points
✅ Use blockquotes for key takeaways
✅ Keep paragraphs to 2-3 sentences max
✅ Write in first person ("I think...", "In my view...")
✅ Be direct and practical

---

# 🚨🚨🚨 MANDATORY: USE THESE EXACT HEADLINE AND PREVIEW 🚨🚨🚨

**DO NOT WRITE A DIFFERENT HEADLINE. USE THIS EXACTLY:**

# {outline_data.get('headline', 'No headline selected')}

*{outline_data.get('preview', 'No preview selected')}*

**THE ABOVE HEADLINE AND PREVIEW WERE WRITTEN BY THE USER. DO NOT CHANGE THEM.**

---

## 📰 MAIN STORY:
"""
        # Handle new format with main_story
        main_story = outline_data.get('main_story', {})
        if main_story:
            main_word_count = main_story.get('target_word_count', 500)
            user_prompt += f"""
### {main_story.get('heading', 'Main Story')}

⚠️ **TARGET LENGTH: {main_word_count} WORDS** - This is the user's specified length. Hit this target!

**Story structure to follow:**
"""
            for structure_point in main_story.get('structure', []):
                user_prompt += f"- {structure_point}\n"
            
            user_prompt += "\n**Key points to develop:**\n"
            for point in main_story.get('key_points', main_story.get('bullet_points', [])):
                user_prompt += f"- {point}\n"
            
            if main_story.get('user_notes'):
                user_prompt += f"\n**USER'S SPECIFIC INPUT FOR MAIN STORY:** {main_story['user_notes']}\n"
        
        # Add additional sections (news roundup, tools, etc.)
        additional_sections = outline_data.get('additional_sections', [])
        if additional_sections:
            user_prompt += """

---

## 📑 ADDITIONAL SECTIONS:
"""
            for i, section in enumerate(additional_sections, 1):
                section_type = section.get('type', 'general')
                section_word_count = section.get('target_word_count', 100)
                user_prompt += f"""
### {section.get('heading', f'Section {i}')} [{section_type}]
⚠️ **TARGET LENGTH: {section_word_count} WORDS**
"""
                # Add special instructions for AI transparency section
                if section_type == 'ai_transparency':
                    user_prompt += """
⚠️ **AI TRANSPARENCY SECTION - BE HONEST AND SPECIFIC:**
This section explains to readers how AI was used to create this newsletter.
Include:
- Which AI models were used (mention the specific models: fine-tuned gpt-4o-mini for style, gpt-4.1 for content)
- What the AI did vs what you (Paul) did (e.g., AI generated outline, you edited key points)
- What parts were human-written vs AI-assisted
- Be transparent - readers appreciate honesty about AI use
- Keep it brief and factual, not defensive

"""
                # Add special instructions for Letter+ development section
                elif section_type == 'letterplus_development':
                    user_prompt += """
⚠️ **LETTER+ DEVELOPMENT SECTION - ONLY INCLUDE REAL CHANGES:**
This section shares what improvements were made to the Letter+ app.
CRITICAL: Only include changes that the user has specified in their notes.
If no specific changes are mentioned, write about the general development process:
- What features are being worked on
- What bugs were fixed
- What the user learned about building AI apps
DO NOT invent specific features or changes - only use what the user provides.

"""
                user_prompt += "Points to cover:\n"
                for point in section.get('bullet_points', []):
                    user_prompt += f"- {point}\n"
                
                if section.get('user_notes'):
                    user_prompt += f"\n**USER'S INPUT:** {section['user_notes']}\n"
        
        # Fallback for old format with just 'sections'
        if not main_story and not additional_sections:
            user_prompt += "\n**SECTIONS TO WRITE:**\n"
            for i, section in enumerate(outline_data.get('sections', []), 1):
                user_prompt += f"""
### {section.get('heading', f'Section {i}')}
Points to cover:
"""
                for point in section.get('bullet_points', []):
                    user_prompt += f"- {point}\n"
                
                if section.get('user_notes'):
                    user_prompt += f"\n**USER'S SPECIFIC INPUT (USE THIS):** {section['user_notes']}\n"

        # Add sources if provided
        sources = outline_data.get('sources', [])
        
        user_prompt += """
---

# 🚨🚨🚨 CRITICAL: SOURCING REQUIREMENTS 🚨🚨🚨

## EVERY CLAIM MUST HAVE A WORKING LINK

You MUST follow these rules about information and sources:

### RULE 1: ONLY USE PROVIDED SOURCES
"""
        
        if sources:
            user_prompt += """
The user has provided these VERIFIED sources. ONLY reference information from these:

"""
            for source in sources:
                title = source.get('title', '')
                url = source.get('url', '')
                if title and url:
                    user_prompt += f"✅ **{title}**: [{url}]({url})\n"
                elif title:
                    user_prompt += f"⚠️ {title} (no URL - use carefully)\n"
                elif url:
                    user_prompt += f"✅ {url}\n"
        else:
            user_prompt += """
⚠️ NO SOURCES PROVIDED. You must:
- Only write about things YOU (Paul McNally) have personally experienced
- Only mention organizations YOU have actually worked with
- DO NOT cite any external reports, studies, or news articles
- DO NOT make claims that require external verification
"""
        
        user_prompt += """

### RULE 2: NO INVENTED INFORMATION
❌ NEVER invent statistics (e.g., "45% of newsrooms...")
❌ NEVER cite reports that weren't provided (e.g., "According to McKinsey...")
❌ NEVER reference articles you don't have the URL for
❌ NEVER make up dates for future events you don't know about
❌ NEVER create fake quotes from anyone

### RULE 3: WHAT YOU CAN WRITE ABOUT
✅ Your personal experiences (workshops you've run, places you've visited)
✅ Real organizations you've worked with (DW Akademie, etc.)
✅ Real tools you've used (ChatGPT, ElevenLabs, Cursor, Ollama, etc.)
✅ General observations that don't require citations
✅ Information from the PROVIDED SOURCES above (with links!)

### RULE 4: FORMAT FOR CITATIONS
When you cite something from the provided sources, include the link inline:
- "According to [TechCrunch](https://techcrunch.com/article), investors are..."
- "A recent [Reuters report](https://reuters.com/story) found that..."

### RULE 5: NEWS ROUNDUP MUST HAVE LINKS
Every item in "This Week in AI" or news roundup MUST have a working link OR be marked:
- ✅ "[Google launches new AI tool](https://actual-url.com)"
- ❌ "Google launches new AI tool (Search: 'google AI tool')" - NOT ACCEPTABLE

If you don't have a real link for a news item, DO NOT INCLUDE IT.

---
"""

        user_prompt += f"""
---

# ⚠️ STYLE CONTROLS FROM USER (APPLY THESE):

{additional_instructions}

---

# 🚨 CRITICAL: UNDERSTAND THE STRUCTURE 🚨

Your newsletter has a **MAIN STORY** and then **OTHER SECTIONS**.

## THE MAIN STORY IS NOT A NEWS ROUNDUP!

❌ WRONG: A "News Roundup" with 5 short news items is NOT a main story
❌ WRONG: Opening with 2 paragraphs then jumping to "This Week's News" 
❌ WRONG: Treating the news items AS the main content

✅ RIGHT: The MAIN STORY is a **DEEP DIVE into ONE topic** - at least 500 words
✅ RIGHT: News Roundup comes AFTER the main story as a separate section
✅ RIGHT: The main story has its own analysis, examples, and lessons

## MAIN STORY STRUCTURE (500+ WORDS):

The main story should read like a mini-essay or feature article:

**Opening hook** (50 words) - Set the scene, make it personal

**The core issue** (150 words) - What's happening and why it matters

**Deep analysis** (150 words) - Go beneath the surface. Question assumptions.

**Real examples** (100 words) - Specific tools, places, people with names

**Africa/Global South angle** (100 words) - How this affects the developing world

**Practical takeaway** (50 words) - What should the reader actually do?

## THE NEWS ROUNDUP IS SEPARATE

After the main story, you can have a "📋 News Roundup" or "This Week in AI" section.
This is SHORT bullet points of 3-5 news items, NOT the main content.

Example:
- Main Story: "Why Apple's On-Device AI Changes Everything for Newsrooms" (500 words)
- Then: "📋 This Week's Quick Hits" (150 words total, brief bullets)

---

# NOW WRITE THE FULL NEWSLETTER:

# {outline_data.get('headline', 'Headline')}

*{outline_data.get('preview', 'Preview')}*

[Opening hook - 2-3 sentences]

[MAIN STORY - 500+ WORDS with numbered sections/lessons, specific examples, blockquotes]

**What's Happening at Develop AI** (if included)
[Updates about your work]

**[Other sections]**

---

**How Letter+ helped write this newsletter**

This newsletter was created using Letter+, an app I built to streamline my writing process. Here's how it worked for this issue:

- **Outline generation**: Letter+ analyzed my past newsletters and suggested the structure for this piece
- **Style matching**: A fine-tuned AI model trained on my 43 previous newsletters helped maintain my voice
- **Fact checking**: The Knowledge Base automatically matched relevant facts and sources to my topic
- **Editing**: I reviewed and edited the outline, adding my own key points and notes
- **Generation**: The final newsletter was generated using my edits as the foundation

The AI doesn't replace my thinking - it handles the scaffolding so I can focus on the ideas. You can try Letter+ yourself at [link].

---

All the best,

Paul

---

# 🚨 FINAL CHECKLIST - VERIFY BEFORE RESPONDING 🚨

Before you finish, confirm you have:
✅ Used the EXACT headline the user specified (not your own)
✅ Used the EXACT preview the user specified (not your own)
✅ Included ALL the key points from the main story outline
✅ Included ALL the bullet points from each additional section
✅ Incorporated any user notes the user added
✅ Hit the target word counts specified for each section

DO NOT submit until all user edits are incorporated!

---

⚠️ BEFORE YOU SUBMIT:
1. Count the words in your main story section - must be 400+
2. Check for ANY [NEED:] placeholders - REMOVE THEM
3. Check for vague sources like "a tech editor" - REMOVE OR NAME THEM
4. Check for invented statistics - REMOVE IF NOT REAL

If you don't know something specific, write around it. Don't fake it.

Write now:
"""
    
    else:
        user_prompt = f"""Write content based on this idea:

**IDEA:** {idea}

{additional_instructions}
"""
    
    return system_prompt, user_prompt, facts_used


# ============================================================================
# Two-Stage Generation: Fine-tuned model writes the prompt, GPT-4.1 executes
# ============================================================================

def generate_style_prompt(
    idea: str,
    outline_data: dict,
    additional_instructions: str = ""
) -> str:
    """
    Use the fine-tuned model to generate a comprehensive, style-aware prompt
    that GPT-4.1 will use to write the actual newsletter.
    
    This captures YOUR unique writing approach and passes it to the powerful model.
    """
    fine_tuned_model = get_generation_model(task_type="short")
    
    # If no fine-tuned model, return None to skip this step
    if not fine_tuned_model or not fine_tuned_model.startswith('ft:'):
        return None
    
    headline = outline_data.get('headline', '')
    preview = outline_data.get('preview', '')
    opening_hook = outline_data.get('opening_hook', '')
    main_story = outline_data.get('main_story', {})
    additional_sections = outline_data.get('additional_sections', [])
    sources = outline_data.get('sources', [])
    
    # Format sources for the prompt
    sources_text = ""
    if sources:
        sources_text = "AVAILABLE SOURCES (ONLY use these for external claims):\n"
        for s in sources:
            if s.get('url'):
                sources_text += f"- {s.get('title', 'Source')}: {s.get('url')}\n"
            else:
                sources_text += f"- {s.get('title', 'Source')} (no URL - use carefully)\n"
    else:
        sources_text = """NO EXTERNAL SOURCES PROVIDED.
        
⚠️ CRITICAL: Without sources, you must NOT:
- Invent anecdotes or personal experiences
- Fabricate places, events, or dates
- Make up statistics or quotes
- Create fictional scenarios

You CAN write:
- General analysis and opinions
- Discussion of the user's key points (they wrote these, they are real)
- Information about well-known tools (ChatGPT, Cursor, etc.)
- The content from the user's outline (it came from them!)"""
    
    # Build main story details including user edits
    main_story_text = f"Topic: {main_story.get('heading', idea)}\n"
    if main_story.get('structure'):
        main_story_text += "Structure:\n"
        for s in main_story.get('structure', []):
            main_story_text += f"  - {s}\n"
    if main_story.get('key_points'):
        main_story_text += "Key Points (USER EDITED - MUST INCLUDE THESE):\n"
        for p in main_story.get('key_points', []):
            main_story_text += f"  - {p}\n"
    if main_story.get('user_notes'):
        main_story_text += f"USER NOTES: {main_story.get('user_notes')}\n"
    main_story_text += f"Target Word Count: {main_story.get('target_word_count', 500)}\n"
    
    # Build additional sections details
    sections_text = ""
    for i, section in enumerate(additional_sections, 1):
        sections_text += f"\nSection {i}: {section.get('heading', 'Untitled')}\n"
        if section.get('bullet_points'):
            sections_text += "Points (USER EDITED - MUST INCLUDE THESE):\n"
            for bp in section.get('bullet_points', []):
                sections_text += f"  - {bp}\n"
        if section.get('user_notes'):
            sections_text += f"USER NOTES: {section.get('user_notes')}\n"
        sections_text += f"Target Words: {section.get('target_word_count', 100)}\n"
    
    prompt = f"""You are Paul McNally writing a newsletter. Based on this outline, write a DETAILED PROMPT that another AI will use to write the full newsletter in YOUR EXACT STYLE.

# OUTLINE (USER HAS EDITED THIS - RESPECT ALL EDITS):

## HEADLINE (USE THIS EXACTLY):
{headline}

## PREVIEW (USE THIS EXACTLY):
{preview}

## OPENING HOOK:
{opening_hook[:300] if opening_hook else 'Not specified'}

## MAIN STORY:
{main_story_text}

## ADDITIONAL SECTIONS:
{sections_text if sections_text else 'None specified'}

## SOURCES:
{sources_text}

YOUR TASK:
Write a comprehensive prompt (500-800 words) that instructs another AI how to write this newsletter EXACTLY like you would. Include:

1. **VOICE INSTRUCTIONS**: How should sentences sound? What's the rhythm? Give 3-4 example sentence structures I use.

2. **OPENING APPROACH**: How should this specific newsletter open? What hook would I use? Be specific to this topic.

3. **MAIN STORY INSTRUCTIONS**: 
   - What angle would I take on this topic?
   - What personal anecdotes or "I" statements should be included?
   - What specific questions would I ask the reader?
   - How would I bring in the Africa/Global South angle?
   - What would my skeptical-but-curious take be?

4. **STRUCTURE GUIDANCE**: How would I pace this? Where would I put short punchy paragraphs vs longer analysis?

5. **SPECIFIC PHRASES**: What are 5-10 phrases or transitions I would actually use in this piece?

6. **WHAT TO AVOID**: What would make this NOT sound like me?

7. **CLOSING APPROACH**: How would I end this specific newsletter?

8. **SOURCING RULES** (CRITICAL):
   - ONLY cite sources from the provided list above
   - EVERY external claim must have a clickable [link](url) inline
   - If no sources are provided, ONLY write about personal experiences
   - NEVER invent statistics, reports, or quotes
   - News roundup items MUST have real URLs or be excluded
   - If you don't have a source, don't make the claim

Write this as if you're briefing a ghostwriter who needs to perfectly capture my voice. Be SPECIFIC to this topic, not generic.

{additional_instructions}

WRITE THE DETAILED STYLE PROMPT NOW:"""

    try:
        response = client.chat.completions.create(
            model=fine_tuned_model,
            messages=[
                {
                    "role": "system", 
                    "content": "You are Paul McNally. You write newsletters about AI for journalists and media professionals. Your style is punchy, personal, skeptical-but-curious, and grounded in African/Global South perspectives. Write a detailed prompt that captures exactly how you would write this specific newsletter."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500,
        )
        
        style_prompt = response.choices[0].message.content
        
        # Log the API call
        usage = response.usage
        if usage and USAGE_LOGGING_AVAILABLE:
            log_api_call(
                model=fine_tuned_model,
                feature="style_prompt_generation",
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens
            )
        
        return style_prompt
        
    except Exception as e:
        print(f"Style prompt generation failed: {e}")
        return None


# ============================================================================
# NEW: Comprehensive Blueprint Generation (GPT-4o Two-Stage)
# ============================================================================

def build_blueprint_instructions(
    outline_data: dict,
    bible: dict,
    kb_context: str = "",
    rag_context: str = "",
    performance_learnings: str = "",
    additional_instructions: str = ""
) -> str:
    """
    Build the instructions that will be sent to the fine-tuned GPT-4o
    to generate a comprehensive blueprint for the newsletter.
    
    This is STAGE 1 of the new two-stage process.
    Returns the full instruction text (for display in UI).
    
    additional_instructions includes STORY TYPE which affects tone and structure.
    """
    
    headline = outline_data.get('headline', '')
    preview = outline_data.get('preview', '')
    opening_hook = outline_data.get('opening_hook', '')
    main_story = outline_data.get('main_story', {})
    additional_sections = outline_data.get('additional_sections', [])
    sources = outline_data.get('sources', [])
    
    # Format the outline details
    main_story_text = f"""
TOPIC: {main_story.get('heading', 'Not specified')}
TARGET WORD COUNT: {main_story.get('target_word_count', 500)} words

KEY POINTS (User has written these - they are REAL and must be included):
"""
    for i, point in enumerate(main_story.get('key_points', []), 1):
        main_story_text += f"  {i}. {point}\n"
    
    if main_story.get('user_notes'):
        main_story_text += f"\nUSER'S NOTES: {main_story.get('user_notes')}\n"
    
    # Format additional sections
    sections_text = ""
    for i, section in enumerate(additional_sections, 1):
        sections_text += f"""
SECTION {i}: {section.get('heading', 'Untitled')}
Target: {section.get('target_word_count', 100)} words
Bullet points to include:
"""
        for bp in section.get('bullet_points', []):
            sections_text += f"  - {bp}\n"
        if section.get('user_notes'):
            sections_text += f"User notes: {section.get('user_notes')}\n"
    
    # Format sources
    if sources:
        sources_text = "VERIFIED SOURCES (use these for citations):\n"
        for s in sources:
            sources_text += f"  - {s.get('title', 'Source')}: {s.get('url', 'no URL')}\n"
    else:
        sources_text = "NO EXTERNAL SOURCES PROVIDED - only write about what the user has given you in their outline."
    
    # Build the full instruction
    instructions = f"""# BLUEPRINT GENERATION INSTRUCTIONS

You are Paul McNally. You're about to write a newsletter, but first you need to create a COMPREHENSIVE BLUEPRINT - a detailed, paragraph-by-paragraph plan that will guide the actual writing.

## YOUR NEWSLETTER OUTLINE

**HEADLINE (use exactly):** {headline}

**PREVIEW TEXT (use exactly):** {preview}

**OPENING HOOK:** {opening_hook[:500] if opening_hook else 'Not specified - you decide'}

## MAIN STORY
{main_story_text}

## ADDITIONAL SECTIONS
{sections_text if sections_text else 'None specified'}

## SOURCES
{sources_text}

---

## CONTEXT FROM YOUR KNOWLEDGE BASE
{kb_context[:2000] if kb_context else 'No relevant facts found in Knowledge Base.'}

---

## SIMILAR PASSAGES FROM YOUR PAST NEWSLETTERS
{rag_context[:2000] if rag_context else 'No similar passages found.'}

---

## WHAT HAS WORKED BEFORE (Performance Learnings)
{performance_learnings[:1000] if performance_learnings else 'No performance data available yet.'}

---

{f'''## STORY TYPE & STYLE INSTRUCTIONS
{additional_instructions}

---''' if additional_instructions else ''}

# YOUR TASK: CREATE A COMPREHENSIVE BLUEPRINT

Write a DETAILED BLUEPRINT (800-1200 words) that plans out this entire newsletter. This blueprint will be used to generate the final newsletter, so be EXTREMELY SPECIFIC.

## BLUEPRINT STRUCTURE:

### 1. OPENING (First 2-3 paragraphs)
- Write the EXACT opening sentence you want to use
- Describe the hook and how it connects to the main topic
- What question or tension are you setting up?

### 2. MAIN STORY ARC
For EACH paragraph of the main story:
- What's the core point of this paragraph?
- What transition leads into it?
- Any specific phrases or sentences to use?
- Where do the user's key points get woven in?

### 3. SECTION-BY-SECTION PLAN
For each additional section:
- How does it start?
- How are the bullet points presented?
- What's the connecting thread?

### 4. VOICE & STYLE NOTES
- Specific phrases you'll use
- Sentence rhythms (short punchy + longer analytical)
- Rhetorical questions to include
- Where to add "I" statements and personal perspective

### 5. SOURCING & CITATIONS
- Which facts from KB will you cite and where?
- How will you format the citations?
- What claims need sources vs. what's your opinion?

### 6. CLOSING
- How does the newsletter end?
- What's the call to action?
- What thought do you leave the reader with?

### 7. ANTI-FABRICATION CHECKLIST
- Confirm: No invented personal stories about places you didn't go
- Confirm: No made-up statistics or quotes
- Confirm: Every external claim has a source from the list above

---

WRITE YOUR COMPREHENSIVE BLUEPRINT NOW:"""

    return instructions


def generate_comprehensive_blueprint(
    outline_data: dict,
    bible: dict = None,
    idea: str = "",
    additional_instructions: str = ""
) -> dict:
    """
    STAGE 1: Generate a comprehensive blueprint using fine-tuned GPT-4o.
    
    This creates a detailed, paragraph-by-paragraph plan for the newsletter
    that will then be executed in Stage 2.
    
    additional_instructions includes STORY TYPE which affects tone and structure.
    
    Returns:
        dict with 'blueprint', 'instructions', 'model_used', etc.
    """
    
    # Get the fine-tuned model
    fine_tuned_model = get_generation_model(task_type="full")
    
    if not fine_tuned_model or not fine_tuned_model.startswith('ft:'):
        return {
            'error': 'No fine-tuned model available. Train a GPT-4o model first.',
            'blueprint': None,
            'instructions': None
        }
    
    # Load bible if not provided
    if bible is None:
        bible = load_bible() or {}
    
    # Get KB context
    kb_context = ""
    if KNOWLEDGE_BASE_AVAILABLE:
        try:
            topic = outline_data.get('headline', '') or idea
            kb_context = get_relevant_facts_context(topic, max_facts=8)
        except:
            pass
    
    # Get RAG context
    rag_context = ""
    if RAG_AVAILABLE:
        try:
            topic = outline_data.get('headline', '') or idea
            examples = get_writing_examples(topic, n_results=5)
            if examples:
                rag_context = "\\n\\n---\\n\\n".join([ex.get('text', '')[:500] for ex in examples])
        except:
            pass
    
    # Get performance learnings
    performance_learnings = ""
    if LEARNING_AVAILABLE:
        try:
            performance_learnings = get_performance_learnings()
        except:
            pass
    
    # Build the instructions
    instructions = build_blueprint_instructions(
        outline_data=outline_data,
        bible=bible,
        kb_context=kb_context,
        rag_context=rag_context,
        performance_learnings=performance_learnings,
        additional_instructions=additional_instructions
    )
    
    # System prompt for blueprint generation
    system_prompt = """You are Paul McNally, author of the Develop AI newsletter about AI for journalists and media professionals.

Your writing style:
- Punchy, personal, direct
- Skeptical-but-curious about AI hype
- Grounded in African/Global South perspectives
- Mix of short sentences and longer analytical passages
- Rhetorical questions to engage readers
- Personal "I" statements and real experiences

You're creating a BLUEPRINT - a detailed plan that will guide the actual writing. Be extremely specific and detailed. This isn't the newsletter itself, it's the comprehensive plan for writing it."""

    try:
        response = client.chat.completions.create(
            model=fine_tuned_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": instructions}
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        
        blueprint = response.choices[0].message.content
        
        # Log the API call
        usage = response.usage
        if usage and USAGE_LOGGING_AVAILABLE:
            log_api_call(
                model=fine_tuned_model,
                feature="blueprint_generation",
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens
            )
        
        return {
            'blueprint': blueprint,
            'instructions': instructions,
            'system_prompt': system_prompt,
            'model_used': fine_tuned_model,
            'kb_context': kb_context,
            'rag_context': rag_context,
            'performance_learnings': performance_learnings,
            'input_tokens': usage.prompt_tokens if usage else 0,
            'output_tokens': usage.completion_tokens if usage else 0,
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'blueprint': None,
            'instructions': instructions,
            'model_used': fine_tuned_model
        }


def execute_blueprint(
    blueprint: str,
    outline_data: dict,
    bible: dict = None
) -> dict:
    """
    STAGE 2: Execute the blueprint to generate the final newsletter.
    
    Uses the same fine-tuned GPT-4o model to write the newsletter
    following the detailed blueprint from Stage 1.
    
    Returns:
        dict with 'content', 'execution_prompt', 'model_used', etc.
    """
    
    # Get the fine-tuned model (same one that wrote the blueprint)
    fine_tuned_model = get_generation_model(task_type="full")
    
    if not fine_tuned_model or not fine_tuned_model.startswith('ft:'):
        return {
            'error': 'No fine-tuned model available.',
            'content': None
        }
    
    headline = outline_data.get('headline', '')
    preview = outline_data.get('preview', '')
    
    # Build the execution prompt
    execution_prompt = f"""# EXECUTE THIS BLUEPRINT

You previously created a detailed blueprint for a newsletter. Now WRITE THE ACTUAL NEWSLETTER following that blueprint exactly.

## THE BLUEPRINT YOU CREATED:

{blueprint}

---

## REMINDER OF KEY DETAILS:

**HEADLINE (use exactly):** {headline}

**PREVIEW (use exactly):** {preview}

---

## FINAL INSTRUCTIONS:

1. Follow the blueprint paragraph by paragraph
2. Use the exact opening sentence you planned
3. Include all the specific phrases you noted
4. Weave in the user's key points exactly as planned
5. End with the closing you designed
6. Format in clean Markdown with ## headers for sections

## CRITICAL RULES:
- DO NOT fabricate personal experiences, places, or events
- DO NOT invent statistics or quotes
- ONLY cite sources that were provided in the blueprint
- If the blueprint mentions something specific, include it
- If the blueprint says "don't do X", don't do it

---

WRITE THE FULL NEWSLETTER NOW (following your blueprint):

# {headline}

*{preview}*

"""

    # System prompt for execution
    system_prompt = """You are Paul McNally writing your newsletter. You have already created a detailed blueprint. Now execute it exactly, writing the full newsletter in your authentic voice.

Write in Markdown format. Be punchy, personal, and engaging. Follow the blueprint you created - it contains your specific plan for this newsletter."""

    try:
        response = client.chat.completions.create(
            model=fine_tuned_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": execution_prompt}
            ],
            temperature=0.7,
            max_tokens=4000,
        )
        
        content = response.choices[0].message.content
        
        # Log the API call
        usage = response.usage
        if usage and USAGE_LOGGING_AVAILABLE:
            log_api_call(
                model=fine_tuned_model,
                feature="blueprint_execution",
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens
            )
        
        return {
            'content': content,
            'execution_prompt': execution_prompt,
            'system_prompt': system_prompt,
            'model_used': fine_tuned_model,
            'input_tokens': usage.prompt_tokens if usage else 0,
            'output_tokens': usage.completion_tokens if usage else 0,
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'content': None,
            'execution_prompt': execution_prompt
        }


def generate_newsletter_direct(
    idea: str,
    outline_data: dict,
    additional_instructions: str = "",
    temperature: float = 0.7
) -> dict:
    """
    DIRECT GENERATION using fine-tuned GPT-4o.
    
    Pulls ALL details from the user-edited outline and passes them to the model.
    Also loads the Newsletter Bible for style reference.
    
    Returns dict with content and metadata.
    """
    
    # Check for fine-tuned model
    fine_tuned_model = get_active_fine_tuned_model() if FINE_TUNING_AVAILABLE else None
    
    if not fine_tuned_model:
        # Fall back to gpt-4o if no fine-tuned model
        fine_tuned_model = "gpt-4o"
    
    # =========================================================================
    # LOAD THE NEWSLETTER BIBLE (style reference)
    # =========================================================================
    
    bible = load_bible()
    bible_context = ""
    if bible:
        # Extract key style elements
        writing_voice = bible.get('writing_voice', {})
        rules = bible.get('rules_for_success', [])
        cliches = bible.get('cliches_to_avoid', [])
        learnings = bible.get('learnings_from_edits', {})
        
        bible_context = "\n## YOUR WRITING STYLE (from Newsletter Bible)\n\n"
        
        # Signature phrases
        signature_phrases = writing_voice.get('signature_phrases', [])
        if signature_phrases:
            bible_context += "**Your signature phrases:**\n"
            for phrase in signature_phrases[:5]:
                bible_context += f"- \"{phrase}\"\n"
            bible_context += "\n"
        
        # Tone markers
        tone_markers = writing_voice.get('tone_markers', [])
        if tone_markers:
            bible_context += f"**Your tone:** {', '.join(tone_markers[:5])}\n\n"
        
        # Rules
        if rules:
            bible_context += "**Rules for your writing:**\n"
            for rule in rules[:5]:
                bible_context += f"- {rule}\n"
            bible_context += "\n"
        
        # Cliches to avoid
        if cliches:
            bible_context += "**NEVER use these cliches:**\n"
            bible_context += f"{', '.join(cliches[:10])}\n\n"
        
        # Learnings from edits (what the user typically adds/prefers)
        if learnings:
            bible_context += "## LEARNINGS FROM YOUR PAST EDITS\n\n"
            
            # Frequently added content
            freq_added = learnings.get('frequently_added_content', [])
            if freq_added:
                bible_context += "**Content you often add (consider including):**\n"
                for item in freq_added[:5]:
                    bible_context += f"- {item.get('content', '')}\n"
                bible_context += "\n"
            
            # Tone adjustments
            tone_adj = learnings.get('tone_adjustments', [])
            if tone_adj:
                bible_context += "**Tone preferences you've expressed:**\n"
                for adj in tone_adj[-3:]:
                    bible_context += f"- {adj}\n"
                bible_context += "\n"
            
            # Headline preferences
            headline_prefs = learnings.get('headline_preferences', [])
            if headline_prefs:
                bible_context += "**Headlines you've written (your style):**\n"
                for pref in headline_prefs[-3:]:
                    bible_context += f"- \"{pref.get('preferred', '')}\"\n"
                bible_context += "\n"
        
        # Recent headlines (successful ones)
        recent_headlines = bible.get('headline_formulas', {}).get('recent_headlines', [])
        if recent_headlines:
            bible_context += "**Your recent successful headlines:**\n"
            for hl in recent_headlines[:5]:
                bible_context += f"- \"{hl}\"\n"
            bible_context += "\n"
    
    # =========================================================================
    # DEEP STYLE ANALYSIS (advanced linguistic fingerprint)
    # =========================================================================
    
    deep_style_context = ""
    if DEEP_STYLE_AVAILABLE:
        try:
            deep_style_context = get_deep_style_context(idea)
            if deep_style_context:
                bible_context += deep_style_context
        except Exception as e:
            print(f"Deep style context error: {e}")
    
    # =========================================================================
    # LOAD KNOWLEDGE BASE (AI facts, research, insights)
    # =========================================================================
    
    kb_context = ""
    if KNOWLEDGE_BASE_AVAILABLE:
        try:
            # Get the main topic from the idea or main story
            topic = main_story.get('heading', '') if main_story else idea
            
            # Get relevant facts from the knowledge base
            facts_result = get_relevant_facts_context(topic, max_facts=10)
            if isinstance(facts_result, tuple):
                facts_text, facts_used = facts_result
            else:
                facts_text = facts_result if facts_result else ""
                facts_used = []
            
            if facts_text:
                kb_context = "\n## KNOWLEDGE BASE - AI FACTS & INSIGHTS\n\n"
                kb_context += "*Use these facts to enrich your newsletter with specific, verifiable information:*\n\n"
                kb_context += facts_text
                kb_context += "\n"
            
            # Also get broader knowledge context
            knowledge = get_knowledge_context(topic=topic, max_articles=5, max_chars=2000)
            if knowledge:
                kb_context += "\n## RECENT AI NEWS & CONTEXT\n\n"
                kb_context += knowledge
                kb_context += "\n"
        except Exception as e:
            print(f"Error loading KB context: {e}")
            kb_context = ""
    
    # =========================================================================
    # EXTRACT ALL OUTLINE DATA (user edited this in Step 2)
    # =========================================================================
    
    headline = outline_data.get('headline', '')
    preview = outline_data.get('preview', '')
    opening_hook = outline_data.get('opening_hook', '')
    main_story = outline_data.get('main_story', {})
    additional_sections = outline_data.get('additional_sections', [])
    sources = outline_data.get('sources', [])
    closing_approach = outline_data.get('closing_approach', '')
    tone_notes = outline_data.get('tone_notes', '')
    
    # =========================================================================
    # FORMAT SOURCES (with URLs for inline citation) - MANDATORY
    # =========================================================================
    
    sources_text = ""
    source_urls = []
    if sources:
        sources_text = "\n## 🔗 MANDATORY SOURCES - YOU MUST USE ALL OF THESE\n\n"
        sources_text += "⚠️ **CRITICAL:** Every URL below MUST appear in your newsletter as a clickable link.\n"
        sources_text += "Format: [descriptive text](url) woven into sentences, not listed separately.\n\n"
        for i, s in enumerate(sources, 1):
            url = s.get('url', '')
            title = s.get('title', 'Source')
            note = s.get('note', '')
            if url:
                source_urls.append(url)
                sources_text += f"**Source {i}: {title}**\n"
                sources_text += f"URL: {url}\n"
                if note:
                    sources_text += f"Context: {note}\n"
                sources_text += f"Example usage: \"According to [{title}]({url}), ...\"\n\n"
        
        sources_text += f"**CHECKLIST:** You must include {len(source_urls)} clickable links in your newsletter.\n"
    
    # =========================================================================
    # FORMAT MAIN STORY (all user-edited content)
    # =========================================================================
    
    main_story_text = f"## MAIN STORY\n\n"
    main_story_text += f"**Topic:** {main_story.get('heading', idea)}\n"
    main_story_text += f"**Target Word Count:** {main_story.get('target_word_count', 500)} words\n\n"
    
    # Structure (how to organize the story)
    if main_story.get('structure'):
        main_story_text += "**Structure:**\n"
        for s in main_story.get('structure', []):
            main_story_text += f"- {s}\n"
        main_story_text += "\n"
    
    # Key points (USER EDITED - must include all of these)
    if main_story.get('key_points'):
        main_story_text += "**Key Points (MUST include all of these):**\n"
        for p in main_story.get('key_points', []):
            main_story_text += f"- {p}\n"
        main_story_text += "\n"
    
    # User notes (additional guidance from the user)
    if main_story.get('user_notes'):
        main_story_text += f"**User Notes:** {main_story.get('user_notes')}\n\n"
    
    # =========================================================================
    # FORMAT ADDITIONAL SECTIONS (all user-edited content)
    # =========================================================================
    
    sections_text = ""
    if additional_sections:
        sections_text = "\n## ADDITIONAL SECTIONS\n\n"
        for section in additional_sections:
            section_heading = section.get('heading', 'Section')
            section_type = section.get('type', '')
            target_words = section.get('target_word_count', 150)
            
            sections_text += f"### {section_heading}\n"
            sections_text += f"Type: {section_type} | Target: ~{target_words} words\n\n"
            
            # Bullets (USER EDITED - must include)
            if section.get('bullets'):
                sections_text += "**Include these points:**\n"
                for b in section.get('bullets', []):
                    sections_text += f"- {b}\n"
                sections_text += "\n"
            
            # User notes for this section
            if section.get('user_notes'):
                sections_text += f"**Notes:** {section.get('user_notes')}\n\n"
    
    # =========================================================================
    # FORMAT OPENING AND CLOSING - MANDATORY
    # =========================================================================
    
    opening_text = ""
    if opening_hook:
        opening_text = f"\n## 🎯 OPENING - USE THIS EXACT HOOK\n\n"
        opening_text += f"⚠️ **START YOUR NEWSLETTER WITH THIS:**\n\n"
        opening_text += f"\"{opening_hook}\"\n\n"
        opening_text += f"Use this hook as your opening. You can adjust wording slightly but keep the core idea and any personal elements.\n"
    
    closing_text = ""
    if closing_approach:
        closing_text = f"\n## CLOSING\n\n**End with this approach:** {closing_approach}\n"
    
    tone_text = ""
    if tone_notes:
        tone_text = f"\n## TONE\n\n{tone_notes}\n"
    
    # =========================================================================
    # BUILD THE PROMPT
    # =========================================================================
    
    # System prompt - simple, let the fine-tuning handle style
    system_prompt = """You are Paul McNally, writing your newsletter "Develop AI" for journalists and media professionals.

Write naturally in your voice:
- Punchy, personal, skeptical-but-curious about AI
- Short sentences mixed with longer analytical ones
- Personal observations where they fit naturally
- Africa/Global South perspective where relevant

When citing sources, use inline markdown links: [descriptive text](url)

Don't use cliches or corporate speak. Be specific and direct.
Don't invent personal memories or statistics - only use what's provided."""

    # User prompt - includes ALL the outline content, Bible, and Knowledge Base
    user_prompt = f"""Write a newsletter based on this outline:

# {headline}

*{preview}*

---

{opening_text}

{main_story_text}

{sections_text}

{closing_text}

{tone_text}

{sources_text}

{bible_context}

{kb_context}

{f"## ADDITIONAL INSTRUCTIONS{chr(10)}{additional_instructions}" if additional_instructions else ""}

---

## FINAL CHECKLIST - DO ALL OF THESE:

1. ✅ **START** with the opening hook provided above (if any)
2. ✅ **INCLUDE** all {len(source_urls) if source_urls else 0} source URLs as clickable [text](url) links
3. ✅ **COVER** all the key points from the main story
4. ✅ **INCLUDE** all bullets from additional sections
5. ✅ **FOLLOW** your writing style from the Newsletter Bible above
6. ✅ **USE** facts from the Knowledge Base to enrich the content
7. ✅ **AVOID** cliches listed above

Write the complete newsletter now. Natural and conversational, not formulaic. Weave in facts from the Knowledge Base where relevant."""

    try:
        response = client.chat.completions.create(
            model=fine_tuned_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=4000,
        )
        
        content = response.choices[0].message.content
        
        # Log usage
        usage = response.usage
        if usage and USAGE_LOGGING_AVAILABLE:
            log_api_call(
                model=fine_tuned_model,
                feature="direct_newsletter_generation",
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens
            )
        
        return {
            'content': content,
            'headline': headline,
            'preview': preview,
            'generation_mode': 'direct',
            'model_used': fine_tuned_model,
            'two_stage': False,
            'format_type': 'from_outline'
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'content': None
        }


def generate_newsletter_with_blueprint(
    idea: str,
    outline_data: dict,
    additional_instructions: str = "",
    temperature: float = 0.7
) -> dict:
    """
    Two-stage generation - but now defaults to DIRECT generation for better quality.
    
    The meticulous prompt approach was over-engineered and produced worse results.
    Now we use direct generation with the fine-tuned model.
    """
    
    # USE DIRECT GENERATION - simpler and produces better results
    return generate_newsletter_direct(
        idea=idea,
        outline_data=outline_data,
        additional_instructions=additional_instructions,
        temperature=temperature
    )


# ============================================================================
# Main Generation Function
# ============================================================================

def generate_newsletter(
    idea: str,
    format_type: str = "full",
    additional_instructions: str = "",
    temperature: float = 0.8,
    model: str = None,
    outline_data: dict = None
) -> dict:
    """
    Generate a newsletter from an idea using Paul's trained style.
    
    Args:
        idea: The newsletter topic/idea/angle
        format_type: "full", "headlines_only", or "outline"
        additional_instructions: Extra guidance for the AI
        temperature: Creativity level (0.0-1.0)
        model: OpenAI model to use
    
    Returns:
        dict with 'content', 'headline', 'preview', etc.
    """
    
    # Select appropriate model based on task
    if model is None:
        # Full newsletter needs a powerful model (gpt-4.1)
        # Outlines and short tasks can use fine-tuned
        if format_type in ["full", "from_outline"]:
            model = get_generation_model(task_type="full")
        else:
            model = get_generation_model(task_type="short")
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        return {
            'error': "OpenAI API key not configured. Set OPENAI_API_KEY in .env",
            'content': None
        }
    
    # Load the Bible
    bible = load_bible()
    if not bible:
        return {
            'error': "Newsletter Bible not found. Run: python style_analyzer.py",
            'content': None
        }
    
    # Load sample newsletters
    newsletters = load_all_newsletters()
    if not newsletters:
        return {
            'error': "No newsletters found. Run: python scrape_substack.py",
            'content': None
        }
    
    # =========================================================================
    # SMART GENERATION: Blueprint Two-Stage or Legacy Two-Stage
    # =========================================================================
    style_prompt_from_fine_tuned = None
    model_tier = get_fine_tuned_model_tier()
    use_legacy_two_stage = should_use_two_stage_generation()  # Only for gpt-4o-mini
    
    if format_type == "from_outline" and outline_data:
        
        # NEW: GPT-4o Blueprint Two-Stage (best quality)
        if model_tier == 'gpt-4o':
            # Use the new comprehensive blueprint approach
            # Both stages use YOUR fine-tuned GPT-4o model
            return generate_newsletter_with_blueprint(
                idea=idea,
                outline_data=outline_data,
                additional_instructions=additional_instructions,
                temperature=temperature
            )
        
        # LEGACY: gpt-4o-mini + GPT-4.1 two-stage
        elif use_legacy_two_stage:
            # Stage 1: Fine-tuned gpt-4o-mini writes a style prompt
            # Stage 2: GPT-4.1 executes it
            style_prompt_from_fine_tuned = generate_style_prompt(
                idea=idea,
                outline_data=outline_data,
                additional_instructions=additional_instructions
            )
            
            if style_prompt_from_fine_tuned:
                additional_instructions = f"""
# STYLE INSTRUCTIONS FROM YOUR FINE-TUNED MODEL
# (Written by a model trained on your newsletters)

{style_prompt_from_fine_tuned}

---

# ADDITIONAL USER INSTRUCTIONS:
{additional_instructions}
"""
    
    # Build prompts (now also returns facts_used for tracking)
    system_prompt, user_prompt, facts_used = build_generation_prompt(
        idea=idea,
        bible=bible,
        newsletters=newsletters,
        format_type=format_type,
        additional_instructions=additional_instructions,
        outline_data=outline_data
    )
    
    try:
        # Use JSON mode for outline format
        response_format = {"type": "json_object"} if format_type == "outline" else None
        
        create_kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": 4000,
        }
        
        if response_format:
            create_kwargs["response_format"] = response_format
        
        response = client.chat.completions.create(**create_kwargs)
        
        # Log API usage
        usage = response.usage
        if usage and USAGE_LOGGING_AVAILABLE:
            feature = "newsletter_outline" if format_type == "outline" else "newsletter_generation"
            log_api_call(
                model=model,
                feature=feature,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens
            )
        
        content = response.choices[0].message.content
        
        # Mark facts as used if we had any
        if facts_used and KNOWLEDGE_BASE_AVAILABLE:
            try:
                fact_ids = [f.get('id') for f in facts_used if f.get('id')]
                mark_facts_as_used(fact_ids)
            except:
                pass
        
        # Parse the response
        fine_tuned_model = get_active_fine_tuned_model() if FINE_TUNING_AVAILABLE else None
        
        result = {
            'content': content,
            'format_type': format_type,
            'model_used': model,
            'idea': idea,
            'two_stage': style_prompt_from_fine_tuned is not None,
            'style_prompt_used': bool(style_prompt_from_fine_tuned),
            'style_prompt': style_prompt_from_fine_tuned,  # The prompt from fine-tuned model
            'user_prompt': user_prompt,  # The full prompt sent to the AI
            'system_prompt_length': len(system_prompt),  # Don't store full system prompt (too long)
            'facts_injected': len(facts_used) if facts_used else 0,
            'facts_used': facts_used if facts_used else [],
            # New fields for model tier tracking
            'model_tier': model_tier,
            'generation_mode': 'single_stage' if model_tier == 'gpt-4o' else ('two_stage' if use_legacy_two_stage else 'base_model'),
            'models_used': {
                'style': fine_tuned_model if use_legacy_two_stage else None,
                'content': model
            }
        }
        
        # Parse JSON for outline format
        if format_type == "outline":
            try:
                result['outline'] = json.loads(content)
            except json.JSONDecodeError:
                result['outline'] = None
                result['error'] = "Failed to parse outline JSON"
        
        # Try to extract headline and preview if full format
        if format_type in ["full", "from_outline"]:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('## HEADLINE') or line.strip().startswith('# '):
                    if i + 1 < len(lines):
                        result['headline'] = lines[i + 1].strip().lstrip('#').strip()
                    elif line.strip().startswith('# '):
                        result['headline'] = line.strip().lstrip('#').strip()
                elif line.strip().startswith('## PREVIEW'):
                    if i + 1 < len(lines):
                        result['preview'] = lines[i + 1].strip()
        
        return result
        
    except Exception as e:
        return {
            'error': f"Generation failed: {str(e)}",
            'content': None
        }


def regenerate_section(
    current_content: str,
    section_to_improve: str,
    improvement_notes: str,
    model: str = None
) -> dict:
    """Regenerate a specific section of a newsletter."""
    
    # Section regeneration is a short task - fine-tuned model works well
    if model is None:
        model = get_generation_model(task_type="short")
    
    bible = load_bible()
    style_context = get_style_context(bible) if bible else ""
    
    system_prompt = f"""{style_context}

You are improving a section of a newsletter draft.
Maintain Paul's voice and style while implementing the requested improvements.
"""
    
    user_prompt = f"""Here is the current newsletter draft:

{current_content}

Please rewrite the following section with these improvements:

**SECTION TO IMPROVE:** {section_to_improve}

**REQUESTED CHANGES:** {improvement_notes}

Return ONLY the improved section, not the full newsletter.
"""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1500,
        )
        
        # Log API usage
        usage = response.usage
        if usage and USAGE_LOGGING_AVAILABLE:
            log_api_call(
                model=model,
                feature="section_regeneration",
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens
            )
        
        return {
            'improved_section': response.choices[0].message.content,
            'original_section': section_to_improve,
        }
        
    except Exception as e:
        return {'error': str(e)}


# ============================================================================
# NEW: Meticulous Prompt Generation (Fine-tuned model writes the prompt)
# ============================================================================

def generate_meticulous_prompt(
    idea: str,
    outline_data: dict,
    additional_instructions: str = "",
    style_metrics: dict = None,
    story_type_data: dict = None
) -> dict:
    """
    Use the fine-tuned model to generate a METICULOUS, COMPREHENSIVE prompt
    that will then be sent to GPT-4.1 to generate the actual newsletter.
    
    This pulls in EVERYTHING:
    - Newsletter Bible (writing patterns, formulas, voice)
    - Style Dials (doom, hope, practical, etc.)
    - Story Type characteristics
    - Outline with correct word counts
    - Sources and KB facts
    - Performance learnings
    
    Returns:
        dict with 'prompt', 'system_prompt', 'model_used', etc.
    """
    
    # Check for fine-tuned model (optional - we use GPT-4.1 for prompt generation)
    fine_tuned_model = get_active_fine_tuned_model() if FINE_TUNING_AVAILABLE else None
    
    # Load the Bible for style context (REQUIRED - this has the writing style)
    bible = load_bible()
    if not bible:
        return {
            'error': 'Newsletter Bible not found. Please analyze your newsletters first in the Settings tab.',
            'prompt': None
        }
    
    # =========================================================================
    # EXTRACT ALL OUTLINE DETAILS WITH CORRECT WORD COUNTS
    # =========================================================================
    
    headline = outline_data.get('headline', '')
    preview = outline_data.get('preview', '')
    opening_hook = outline_data.get('opening_hook', '')
    main_story = outline_data.get('main_story', {})
    additional_sections = outline_data.get('additional_sections', [])
    sources = outline_data.get('sources', [])
    
    # Calculate total word count
    main_word_count = main_story.get('target_word_count', 500)
    total_word_count = main_word_count
    
    # Format main story with EXACT word count
    main_story_text = f"""
## MAIN STORY
**HEADING:** {main_story.get('heading', 'Not specified')}
**TARGET WORD COUNT:** {main_word_count} words (THIS IS CRITICAL - aim for this length)

**KEY POINTS TO INCLUDE (User wrote these - they are REAL facts/opinions):**
"""
    for i, point in enumerate(main_story.get('key_points', []), 1):
        main_story_text += f"  {i}. {point}\n"
    
    if main_story.get('user_notes'):
        main_story_text += f"\n**USER'S ADDITIONAL NOTES:** {main_story.get('user_notes')}\n"
    
    # Format additional sections with EXACT word counts
    sections_text = ""
    if additional_sections:
        sections_text = "\n## ADDITIONAL SECTIONS\n"
        for i, section in enumerate(additional_sections, 1):
            section_words = section.get('target_word_count', 150)
            total_word_count += section_words
            sections_text += f"""
### SECTION {i}: {section.get('heading', 'Untitled')}
**TARGET WORD COUNT:** {section_words} words
**BULLET POINTS TO INCLUDE:**
"""
            for bp in section.get('bullet_points', []):
                if bp.strip():
                    sections_text += f"  - {bp}\n"
            if section.get('user_notes'):
                sections_text += f"**USER NOTES:** {section.get('user_notes')}\n"
    
    # Format sources
    sources_text = ""
    listed_urls = set()
    if sources:
        sources_text = "\n## VERIFIED SOURCES (REAL - use for citations)\n"
        for s in sources:
            url = s.get('url', '') or ''
            title = s.get('title', 'Source')
            note = s.get('note', '')
            sources_text += f"- **{title}**"
            if url:
                sources_text += f": {url}"
                listed_urls.add(url.strip())
            if note:
                sources_text += f" ({note})"
            sources_text += "\n"
    else:
        sources_text = "\n## SOURCES\nNO EXTERNAL SOURCES PROVIDED - only write about what the user has given you in their key points.\n"
    
    # =========================================================================
    # BUILD BIBLE CONTEXT (Writing Style Patterns) - COMPREHENSIVE
    # =========================================================================
    
    bible_context = "\n## YOUR WRITING STYLE (from Newsletter Bible - 44+ newsletters analyzed)\n\n"
    
    # Voice characteristics - EXPANDED
    voice = bible.get('voice_characteristics', {})
    writing_voice = bible.get('writing_voice', {})
    
    if voice or writing_voice:
        bible_context += "### Voice Characteristics\n"
        if voice:
            bible_context += f"- **Tone:** {voice.get('overall_tone', 'Informative and engaging')}\n"
            bible_context += f"- **Perspective:** {voice.get('perspective', 'First person, personal')}\n"
            
            signature_phrases = voice.get('signature_phrases', [])
            if signature_phrases:
                bible_context += f"- **Signature Phrases to USE:** {', '.join(signature_phrases[:10])}\n"
            
            rhetorical = voice.get('rhetorical_devices', [])
            if rhetorical:
                bible_context += f"- **Rhetorical Devices:** {', '.join(rhetorical[:10])}\n"
            
            sentence_patterns = voice.get('sentence_patterns', {})
            if sentence_patterns:
                bible_context += f"- **Sentence Patterns:** {sentence_patterns}\n"
        
        # Also include writing_voice characteristics
        if writing_voice:
            sentence_style = writing_voice.get('sentence_style', {})
            if sentence_style:
                bible_context += f"- **Average Sentence Length:** {sentence_style.get('avg_length', 'N/A')}\n"
                bible_context += f"- **Short Punchy Sentences:** {sentence_style.get('punchy_short_sentences', 'N/A')}\n"
            
            paragraph_style = writing_voice.get('paragraph_style', {})
            if paragraph_style:
                bible_context += f"- **Average Paragraph Length:** {paragraph_style.get('avg_length', 'N/A')}\n"
                bible_context += f"- **Keeps Paragraphs Short:** {paragraph_style.get('keeps_paragraphs_short', False)}\n"
    
    # Headline formulas - EXPANDED with examples
    headline_formulas = bible.get('headline_formulas', {})
    if headline_formulas:
        bible_context += "\n### Headline Patterns That Work (USE THESE)\n"
        patterns = headline_formulas.get('pattern_breakdown', {})
        for pattern, data in list(patterns.items())[:6]:
            examples = data.get('examples', [])
            if examples:
                bible_context += f"- **{pattern}:** \"{examples[0]}\" (and {len(examples)-1} more examples)\n"
    
    # Structure patterns - EXPANDED
    structure = bible.get('structure_patterns', {})
    if structure:
        bible_context += "\n### Structure Patterns\n"
        bible_context += f"- **Average Word Count:** {structure.get('avg_word_count', 800)} words\n"
        bible_context += f"- **Typical Sections:** {structure.get('common_sections', 3)}\n"
        
        opening_style = structure.get('opening_style', '')
        if opening_style:
            bible_context += f"- **Opening Style:** {opening_style}\n"
        
        closing_style = structure.get('closing_style', '')
        if closing_style:
            bible_context += f"- **Closing Style:** {closing_style}\n"
        
        paragraph_lengths = structure.get('paragraph_lengths', {})
        if paragraph_lengths:
            bible_context += f"- **Paragraph Lengths:** {paragraph_lengths}\n"
    
    # Rules for success - ALL of them
    rules = bible.get('rules_for_success', [])
    if rules:
        bible_context += "\n### Rules for Success (FOLLOW THESE)\n"
        for rule in rules:
            bible_context += f"- {rule}\n"
    
    # CLICHES TO AVOID - CRITICAL
    cliches = bible.get('cliches_to_avoid', [])
    if cliches:
        bible_context += "\n### CLICHES TO NEVER USE (CRITICAL - AVOID THESE PHRASES)\n"
        bible_context += "These generic phrases make your writing sound corporate and unoriginal. NEVER use them:\n\n"
        for cliche in cliches[:20]:  # Show first 20
            bible_context += f"- \"{cliche}\"\n"
        if len(cliches) > 20:
            bible_context += f"\n... and {len(cliches) - 20} more cliches to avoid\n"
        bible_context += "\n**Instead of cliches, be specific, direct, and authentic. Use your own voice, not generic corporate speak.**\n"
    
    # DEEP STYLE ANALYSIS - Extract writing DNA, not just phrases
    all_newsletters = load_all_newsletters()
    if all_newsletters:
        bible_context += "\n### DEEP STYLE ANALYSIS: Your Writing DNA from Past Newsletters\n"
        bible_context += "**CRITICAL:** Study these examples to understand the DEEP patterns of how you write - sentence structure, paragraph flow, rhythm, argumentation style, and voice. Don't just copy phrases - understand HOW to write in this style.\n\n"
        
        # Analyze structural patterns across newsletters
        all_sentences = []
        all_paragraphs = []
        sentence_lengths = []
        paragraph_structures = []
        transition_patterns = []
        argument_flows = []
        
        for i, nl in enumerate(all_newsletters[:10], 1):  # Analyze 10 newsletters
            content = nl.get('content', '')
            headline = nl.get('headline', 'Untitled')
            if not content:
                continue
                
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            all_paragraphs.extend(paragraphs[:15])  # First 15 paragraphs
            
            # Analyze sentence structure in each paragraph
            for para in paragraphs[:15]:
                # Split into sentences
                sentences = [s.strip() for s in para.replace('!', '.').replace('?', '.').split('. ') if s.strip()]
                all_sentences.extend(sentences)
                
                # Analyze sentence lengths
                for sent in sentences:
                    words = sent.split()
                    sentence_lengths.append(len(words))
                
                # Analyze paragraph structure
                if len(sentences) >= 2:
                    para_structure = {
                        'sentence_count': len(sentences),
                        'first_sentence_length': len(sentences[0].split()) if sentences else 0,
                        'last_sentence_length': len(sentences[-1].split()) if sentences else 0,
                        'has_question': any('?' in s for s in sentences),
                        'has_personal': any(' I ' in s or s.startswith('I ') for s in sentences),
                        'short_sentences': len([s for s in sentences if len(s.split()) <= 12]),
                    }
                    paragraph_structures.append(para_structure)
                
                # Extract transition patterns (how paragraphs connect)
                if i > 1 and paragraphs:  # Not first newsletter
                    # Look for transition words/phrases
                    first_words = para.split()[:5] if para else []
                    transition_words = ['but', 'however', 'the', 'this', 'that', 'these', 'now', 'then', 'so', 'and', 'or', 'if', 'when', 'while', 'though', 'although']
                    if first_words and any(word.lower() in transition_words for word in first_words):
                        transition_patterns.append(' '.join(first_words[:8]))
        
        # Only show analysis if we have data
        if sentence_lengths and paragraph_structures:
            # Calculate style statistics
            avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths)
            short_sentence_pct = (len([s for s in sentence_lengths if s <= 10]) / len(sentence_lengths)) * 100
            medium_sentence_pct = (len([s for s in sentence_lengths if 11 <= s <= 20]) / len(sentence_lengths)) * 100
            long_sentence_pct = (len([s for s in sentence_lengths if s > 20]) / len(sentence_lengths)) * 100
            
            # Analyze paragraph patterns
            avg_para_sentences = sum(p['sentence_count'] for p in paragraph_structures) / len(paragraph_structures)
            paragraphs_with_questions = len([p for p in paragraph_structures if p['has_question']])
            paragraphs_with_personal = len([p for p in paragraph_structures if p['has_personal']])
            
            # Build comprehensive style analysis
            bible_context += f"**SENTENCE RHYTHM PATTERNS:**\n"
            bible_context += f"- Average sentence length: {avg_sentence_length:.1f} words\n"
            bible_context += f"- Short sentences (≤10 words): {short_sentence_pct:.1f}% - Use these for emphasis and punch\n"
            bible_context += f"- Medium sentences (11-20 words): {medium_sentence_pct:.1f}% - Your primary sentence length\n"
            bible_context += f"- Long sentences (>20 words): {long_sentence_pct:.1f}% - Use sparingly for complex ideas\n"
            bible_context += f"- **Pattern:** You alternate short punchy sentences with longer analytical ones to create rhythm\n\n"
            
            bible_context += f"**PARAGRAPH STRUCTURE PATTERNS:**\n"
            bible_context += f"- Average sentences per paragraph: {avg_para_sentences:.1f}\n"
            questions_pct = (paragraphs_with_questions / len(paragraph_structures)) * 100
            personal_pct = (paragraphs_with_personal / len(paragraph_structures)) * 100
            bible_context += f"- Paragraphs with questions: {paragraphs_with_questions}/{len(paragraph_structures)} ({questions_pct:.1f}%)\n"
            bible_context += f"- Paragraphs with personal statements: {paragraphs_with_personal}/{len(paragraph_structures)} ({personal_pct:.1f}%)\n"
            bible_context += f"- **Pattern:** You often start paragraphs with personal observations or questions, then develop the idea\n\n"
        else:
            # Fallback if no data
            bible_context += "**Note:** Limited data available for style analysis. Use the examples below to understand the writing style.\n\n"
        
        # Show full examples with structural analysis
        bible_context += f"**FULL EXAMPLES WITH STRUCTURAL ANALYSIS:**\n\n"
        for i, nl in enumerate(all_newsletters[:5], 1):  # Show 5 full examples
            content = nl.get('content', '')
            headline = nl.get('headline', 'Untitled')
            if not content:
                continue
                
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            
            bible_context += f"---\n**NEWSLETTER {i}: \"{headline}\"**\n\n"
            
            # Show first 4 paragraphs with structural annotations
            for para_idx, para in enumerate(paragraphs[:4], 1):
                sentences = [s.strip() for s in para.replace('!', '.').replace('?', '.').split('. ') if s.strip()]
                
                bible_context += f"**Paragraph {para_idx}** ({len(sentences)} sentences):\n"
                bible_context += f"\"{para[:600]}...\"\n\n"
                
                # Annotate structure
                sentence_analysis = []
                for sent in sentences[:5]:  # Analyze first 5 sentences
                    words = sent.split()
                    word_count = len(words)
                    has_personal = ' I ' in sent or sent.startswith('I ')
                    has_question = '?' in sent
                    
                    style_note = []
                    if word_count <= 10:
                        style_note.append("SHORT/PUNCHY")
                    elif word_count > 20:
                        style_note.append("LONG/ANALYTICAL")
                    if has_personal:
                        style_note.append("PERSONAL")
                    if has_question:
                        style_note.append("QUESTION")
                    
                    sentence_analysis.append(f"Sentence {len(sentence_analysis)+1}: {word_count} words" + (f" [{', '.join(style_note)}]" if style_note else ""))
                
                if sentence_analysis:
                    bible_context += f"Structure: {' | '.join(sentence_analysis)}\n\n"
            
            bible_context += "\n"
    
    # Add sample openings from Bible if available
    writing_voice = bible.get('writing_voice', {})
    opening_techniques = writing_voice.get('opening_techniques', {})
    sample_openings = opening_techniques.get('sample_openings', [])
    if sample_openings:
        bible_context += "\n### Additional Sample Openings from Bible Analysis\n"
        bible_context += "**These are extracted opening paragraphs. Use these as style references:**\n\n"
        for i, opening in enumerate(sample_openings[:8], 1):  # Show 8 sample openings
            bible_context += f"{i}. \"{opening[:400]}...\"\n\n"
    
    # Add sample closings too
    closing_techniques = writing_voice.get('closing_techniques', {})
    sample_closings = closing_techniques.get('sample_closings', [])
    if sample_closings:
        bible_context += "\n### Sample Closings from Bible Analysis\n"
        bible_context += "**These are your typical closing patterns:**\n\n"
        for i, closing in enumerate(sample_closings[:5], 1):  # Show 5 sample closings
            bible_context += f"{i}. \"{closing}\"\n\n"
    
    # =========================================================================
    # BUILD STYLE DIALS CONTEXT - WITH EXPLICIT NUMBERS
    # =========================================================================
    
    style_dials_context = ""
    if style_metrics:
        style_dials_context = "\n## STYLE DIALS (User-Set Tone Controls - USE THESE EXACT VALUES)\n\n"
        style_dials_context += "**CRITICAL:** These are the EXACT tone settings. You MUST reference these numbers in your prompt:\n\n"
        
        dial_descriptions = {
            'doom_vs_hope': ('Doom', 'Hope', 'Overall emotional tone'),
            'practical_vs_philosophical': ('Practical/How-To', 'Philosophical/Conceptual', 'Actionable tips vs big ideas'),
            'serious_vs_playful': ('Serious/Formal', 'Playful/Casual', 'Writing tone and humor'),
            'mainstream_vs_niche': ('Mainstream/Accessible', 'Niche/Technical', 'Audience expertise'),
            'urgent_vs_evergreen': ('Urgent/Timely', 'Evergreen/Timeless', 'Time sensitivity'),
            'personal_vs_objective': ('Personal/Opinion', 'Objective/Balanced', 'How much "I" vs neutral'),
            'africa_focus': ('Global', 'Africa-Focused', 'Geographic emphasis'),
            'ai_skepticism': ('AI Enthusiast', 'AI Skeptic', 'Attitude toward AI hype'),
        }
        
        for dial_key, value in style_metrics.items():
            if dial_key in dial_descriptions:
                low_label, high_label, description = dial_descriptions[dial_key]
                # Value is 0-100, interpret it
                if value <= 30:
                    setting = f"**{low_label}** (Value: {value}/100)"
                elif value >= 70:
                    setting = f"**{high_label}** (Value: {value}/100)"
                else:
                    setting = f"**Balanced** (Value: {value}/100)"
                
                style_dials_context += f"- **{description}:** {setting}\n"
        
        style_dials_context += "\n**YOU MUST EXPLAIN IN YOUR PROMPT how each of these values should manifest in the writing.**\n"
    
    # =========================================================================
    # BUILD STORY TYPE CONTEXT
    # =========================================================================
    
    story_type_context = ""
    if story_type_data:
        story_type_context = "\n## STORY TYPE\n\n"
        story_type_context += f"**Type:** {story_type_data.get('name', 'General')}\n"
        story_type_context += f"**Description:** {story_type_data.get('description', '')}\n"
        story_type_context += f"**Tone:** {story_type_data.get('tone', 'Informative')}\n"
        
        patterns = story_type_data.get('headline_patterns', [])
        if patterns:
            story_type_context += f"**Headline Patterns:** {', '.join(patterns[:3])}\n"
        
        examples = story_type_data.get('examples', [])
        if examples:
            story_type_context += f"**Example Headlines:** {examples[0]}\n"
    
    # =========================================================================
    # GET KNOWLEDGE BASE FACTS (with URLs)
    # =========================================================================
    
    kb_context = ""
    kb_facts_list = []
    if KNOWLEDGE_BASE_AVAILABLE:
        try:
            topic = headline or idea
            # Get facts with full details including URLs
            from knowledge_base import get_relevant_facts
            facts = get_relevant_facts(topic, max_facts=10, min_confidence='medium')
            
            if facts:
                kb_context = "\n## FACTS FROM KNOWLEDGE BASE (USE THESE - with URLs)\n\n"
                for fact in facts:
                    fact_text = fact.get('text', '')
                    citation = fact.get('citation', '')
                    source_url = fact.get('source_url', '')
                    fact_type = fact.get('fact_type', 'fact')
                    
                    kb_context += f"**{fact_type.upper()}:** {fact_text}\n"
                    if citation:
                        kb_context += f"  Citation: {citation}\n"
                    if source_url:
                        kb_context += f"  Source URL: {source_url}\n"
                    kb_context += "\n"
                    
                    kb_facts_list.append(fact)
        except Exception as e:
            # Fallback to simpler method
            try:
                kb_facts = get_relevant_facts_context(topic, max_facts=8)
                if kb_facts:
                    kb_context = f"\n## FACTS FROM KNOWLEDGE BASE (Citable)\n\n{kb_facts}\n"
            except:
                pass
    
    # =========================================================================
    # GET RAG CONTEXT (Similar passages from past newsletters)
    # =========================================================================
    
    rag_context = ""
    if RAG_AVAILABLE:
        try:
            topic = headline or idea
            examples = get_writing_examples(topic, n_results=5)
            if examples:
                rag_context = "\n## SIMILAR PASSAGES FROM YOUR PAST NEWSLETTERS\n\n"
                rag_context += "Use these as style references - this is how you've written about similar topics:\n\n"
                for ex in examples[:3]:
                    rag_context += f"---\n{ex.get('text', '')[:600]}...\n\n"
        except:
            pass
    
    # =========================================================================
    # GET DEEP STYLE ANALYSIS (from advanced NLP)
    # =========================================================================
    
    deep_style_text = ""
    if DEEP_STYLE_AVAILABLE:
        try:
            deep_style_text = get_deep_style_context(headline or idea)
            if deep_style_text:
                deep_style_text = "\n## DEEP LINGUISTIC ANALYSIS (from NLP tools)\n" + deep_style_text
        except Exception as e:
            print(f"Deep style context error: {e}")
    
    # =========================================================================
    # GET PERFORMANCE LEARNINGS
    # =========================================================================
    
    performance_context = ""
    if PERFORMANCE_LEARNINGS_AVAILABLE:
        try:
            learnings = get_performance_learnings()
            if learnings:
                performance_context = f"\n## WHAT HAS WORKED BEFORE\n\n{learnings}\n"
        except:
            pass
    
    # =========================================================================
    # BUILD THE SYSTEM PROMPT FOR GPT-4.1 (Better at prompt engineering)
    # =========================================================================
    
    system_prompt_for_ft = """You are an expert prompt engineer helping Paul McNally write a COMPLETE, DETAILED prompt (2000-4000 words) that will instruct GPT-4.1 to write his newsletter in his exact voice and style.

You have been given:
- Paul's Newsletter Bible (his writing style, patterns, phrases from 44+ newsletters)
- His style dial settings (exact numbers)
- The newsletter outline with word counts
- Sources and Knowledge Base facts with URLs
- Story type characteristics

🚨 CRITICAL RULES:

1. **USE ONLY WHAT'S IN THE BIBLE:** When writing about voice & style, you MUST extract REAL phrases, patterns, and examples from the Newsletter Bible section provided. DO NOT invent generic phrases like "On the cusp of change" or "As we navigate these uncharted waters" - these are CLICHÉS that Paul explicitly avoids.

2. **NO CLICHÉS:** The Bible includes a list of clichés to avoid. NEVER suggest phrases from that list, even if they seem appropriate. Instead, use the actual signature phrases and sentence patterns from Paul's past newsletters.

3. **EXTRACT REAL EXAMPLES:** Look at the "Example Openings from Your Past Newsletters" in the Bible - extract REAL sentence patterns from those, not generic ones. Use the actual "Signature Phrases" listed, not made-up ones.

4. **FILL IN ALL DETAILS:** Do NOT just list sections or give an outline. You must WRITE OUT the actual detailed instructions for each part with specific content from the context provided.

For example, don't write:
"## 3. VOICE & STYLE SPECIFICS
- Use phrases like 'On the cusp of change' and 'As we navigate these uncharted waters'"

Instead, write:
"## 3. VOICE & STYLE SPECIFICS
Use the actual signature phrase from Paul's Bible: '[EXACT PHRASE FROM BIBLE]' in the opening paragraph. Follow the sentence pattern shown in the example opening: '[EXACT PATTERN FROM BIBLE EXAMPLE]'. Use short punchy sentences like '[REAL EXAMPLE FROM BIBLE]' to emphasize key points."

You must fill in ALL the blanks with actual content from the context provided below. Reference specific phrases from Paul's writing style (ONLY from the Bible), include all URLs, state exact word counts, and explain how each style dial value affects the writing."""

    # =========================================================================
    # BUILD THE USER PROMPT FOR FINE-TUNED MODEL
    # =========================================================================
    
    # Build additional sections word count string separately to avoid nested f-string issues
    additional_sections_words = ""
    if additional_sections:
        section_list = []
        for s in additional_sections:
            heading = s.get('heading', 'Section')
            words = s.get('target_word_count', 150)
            section_list.append(f"{heading}: {words} words")
        additional_sections_words = f"- Additional sections: {', '.join(section_list)}"
    
    user_prompt_for_ft = f"""# WRITE THE COMPLETE METICULOUS PROMPT

You are writing a detailed brief for GPT-4.1 to write your newsletter. This brief must be 2000-4000 words and include ALL specific details.

---

# CRITICAL NUMBERS - YOU MUST INCLUDE THESE IN YOUR PROMPT:

**WORD COUNTS:**
- Main story: **{main_word_count} words** (EXACT - not approximate)
- Total newsletter: **{total_word_count} words** (EXACT - not approximate)
{additional_sections_words}

**STYLE DIAL VALUES (Reference these numbers in your prompt):**
{f"- Doom vs Hope: {style_metrics.get('doom_vs_hope', 50)}/100" if style_metrics else ""}
{f"- Practical vs Philosophical: {style_metrics.get('practical_vs_philosophical', 50)}/100" if style_metrics else ""}
{f"- Personal vs Objective: {style_metrics.get('personal_vs_objective', 50)}/100" if style_metrics else ""}
{f"- Africa Focus: {style_metrics.get('africa_focus', 50)}/100" if style_metrics else ""}
{f"- AI Skepticism: {style_metrics.get('ai_skepticism', 50)}/100" if style_metrics else ""}

**SOURCES & LINKS (MANDATORY - ALL MUST BE USED):**
- Number of sources: {len(sources)}
- Number of KB facts: {len(kb_facts_list)}
- **🚨 CRITICAL: YOU MUST LIST EVERY SINGLE URL FROM BOTH SOURCES AND KB FACTS BELOW**
- **🚨 CRITICAL: EVERY URL LISTED MUST APPEAR IN THE FINAL NEWSLETTER - NO EXCEPTIONS**
- **🚨 CRITICAL: In Section 6, you MUST specify WHERE each URL will be used in the newsletter**

---

# THE NEWSLETTER TO WRITE

**HEADLINE:** {headline}
**PREVIEW:** {preview}

{main_story_text}

{sections_text}

{sources_text}

---

{bible_context}

{style_dials_context}

{story_type_context}

{kb_context}

{rag_context}

{deep_style_text}

{performance_context}

{f"## ADDITIONAL INSTRUCTIONS{chr(10)}{additional_instructions}" if additional_instructions else ""}

---

# YOUR TASK: WRITE THE COMPLETE PROMPT

Write a FULL, DETAILED prompt (2000-4000 words) that GPT-4.1 will use. DO NOT just list sections - WRITE OUT all the specific instructions.

For each section below, you must WRITE the actual detailed content, not just describe what should be there.

## 1. OPENING INSTRUCTIONS

🚨 **CRITICAL:** If an opening hook is provided above, use it EXACTLY as written. DO NOT invent personal memories or childhood stories.

**Opening hook provided:** "{opening_hook[:200] if opening_hook else 'No opening hook provided - start with the topic directly'}"

**Your task:**
- If an opening hook IS provided: Use it EXACTLY as written - don't invent variations or additional personal memories
- If NO opening hook is provided: Start with the topic directly (e.g., "AMD announced new AI-powered PC chips. Here's what that means.") - DO NOT invent a personal memory hook
- Write the EXACT opening 2-3 sentences
- Include the specific words, the hook, and how to connect to the reader
- **NEVER invent childhood memories, personal anecdotes, or specific experiences** unless they're in the opening hook above

## 2. PARAGRAPH-BY-PARAGRAPH PLAN FOR MAIN STORY

For EACH paragraph of the {main_word_count}-word main story, write:
- The exact core point of this paragraph
- The specific transition sentence to lead into it
- Where each of the user's key points gets woven in (list them specifically)
- Specific phrases or sentences to use
- The tone and voice for this paragraph

The user's key points are:
{chr(10).join([f"  - {point}" for point in main_story.get('key_points', [])]) if main_story.get('key_points') else "  - (No specific key points provided)"}

## 3. VOICE & STYLE SPECIFICS (CRITICAL - DEEP STYLE IMITATION)

🚨 **CRITICAL:** Your task is NOT to copy phrases. Your task is to understand the DEEP WRITING STYLE and write NEW content in that same style. Study the structural patterns, rhythm, flow, and voice - then apply those patterns to create original content that FEELS like it was written by the same person.

**YOUR TASK - UNDERSTAND THE WRITING DNA:**

Look at the "DEEP STYLE ANALYSIS" section above. Study the patterns, then write instructions for HOW to write in this style:

1. **SENTENCE RHYTHM & STRUCTURE:**
   - Study the sentence length patterns (short/medium/long percentages)
   - Understand WHEN to use short punchy sentences vs longer analytical ones
   - Write instructions like: "Use short sentences (≤10 words) to emphasize key points, especially after longer analytical sentences. Follow this pattern: [long sentence explaining concept] → [short punchy sentence driving the point home]"
   - Reference the actual percentages from the analysis

2. **PARAGRAPH FLOW & STRUCTURE:**
   - Study how paragraphs are structured (sentence count, question usage, personal statements)
   - Understand the pattern of how ideas are introduced and developed
   - Write instructions like: "Start paragraphs with personal observations or questions [X]% of the time. Then develop the idea over [Y] sentences, mixing short and medium-length sentences. End with a takeaway or transition."
   - Reference the actual patterns from the examples

3. **VOICE & TONE:**
   - Study how personal statements are woven in (not just "I" but HOW "I" is used)
   - Understand the conversational tone - how formal vs casual
   - Write instructions like: "Use first-person observations naturally, not forced. When making a point, connect it to personal experience [X]% of the time. The tone should feel like talking to a colleague, not giving a presentation."
   - Study the examples to understand the voice

4. **ARGUMENTATION STYLE:**
   - Study how ideas are introduced, developed, and connected
   - Understand how evidence is presented and how conclusions are drawn
   - Write instructions like: "Introduce ideas with context or personal observation. Develop with specific examples or data. Connect ideas using transitions like [study the transition patterns]. Build arguments progressively, not all at once."
   - Reference the paragraph structure patterns

5. **TRANSITION & FLOW:**
   - Study how paragraphs connect to each other
   - Understand the rhythm of moving from one idea to the next
   - Write instructions like: "Use questions to transition between sections [X]% of the time. Use short sentences to create breaks before new ideas. Connect related concepts with [study the transition words used]."
   - Reference the transition patterns from the analysis

6. **SPECIFIC STYLE PATTERNS:**
   - Study the structural annotations in the examples
   - Understand patterns like: "SHORT/PUNCHY → LONG/ANALYTICAL → PERSONAL → QUESTION"
   - Write instructions that capture these patterns: "Follow this sentence rhythm pattern: [describe the pattern you see in the examples]. Use personal statements to ground abstract concepts. Use questions to engage readers and transition to new ideas."
   - Reference specific examples with their structural annotations

**REQUIRED FORMAT FOR YOUR RESPONSE:**

Write comprehensive style instructions that teach GPT-4.1 HOW to write in this style:

**A. SENTENCE RHYTHM INSTRUCTIONS:**
- Specify the target sentence length distribution (based on the percentages)
- Explain when to use short vs medium vs long sentences
- Give examples of the rhythm pattern from the newsletters analyzed

**B. PARAGRAPH STRUCTURE INSTRUCTIONS:**
- Specify how many sentences per paragraph (based on average)
- Explain how to start paragraphs (personal/question/statement - based on patterns)
- Explain how to develop ideas within paragraphs
- Explain how to end paragraphs (transition/takeaway/question)

**C. VOICE & TONE INSTRUCTIONS:**
- Explain how to use first-person naturally (not forced)
- Specify the conversational tone level
- Explain when to be personal vs objective (based on patterns)
- Give examples of the voice from the newsletters

**D. ARGUMENTATION STYLE INSTRUCTIONS:**
- Explain how to introduce ideas (pattern from examples)
- Explain how to develop ideas (pattern from examples)
- Explain how to present evidence (pattern from examples)
- Explain how to draw conclusions (pattern from examples)

**E. TRANSITION & FLOW INSTRUCTIONS:**
- Explain how paragraphs should connect (study the examples)
- Specify transition techniques (questions, short sentences, connecting phrases)
- Explain the rhythm of moving between ideas

**F. SPECIFIC PATTERNS TO FOLLOW:**
- Reference the structural annotations from the examples
- Explain patterns like "SHORT → LONG → PERSONAL → QUESTION"
- Give specific examples from the newsletters with their annotations

**DO NOT DO THIS:**
- ❌ DO NOT just list phrases to copy
- ❌ DO NOT invent generic style advice
- ❌ DO NOT focus on specific words - focus on STRUCTURE and PATTERNS
- ❌ DO NOT create corporate-style instructions

**DO THIS:**
- ✅ Study the DEEP patterns (sentence length, paragraph structure, flow, rhythm)
- ✅ Write instructions that teach HOW to write in this style
- ✅ Reference the actual percentages and patterns from the analysis
- ✅ Give examples from the newsletters to illustrate each pattern
- ✅ Focus on STRUCTURE, RHYTHM, FLOW, and VOICE - not just phrases

**Remember:** You're teaching GPT-4.1 to WRITE LIKE this person, not to COPY their phrases. Focus on the underlying writing DNA - the patterns, structures, rhythms, and voice that make the writing distinctive.

## 4. STYLE DIAL IMPLEMENTATION (CRITICAL - USE THE EXACT NUMBERS)

The style dials are set to these EXACT values. You MUST reference these numbers and explain how they affect the writing:

{f"- **Doom vs Hope:** {style_metrics.get('doom_vs_hope', 50)}/100 - " + ("Emphasize concerns and risks" if style_metrics.get('doom_vs_hope', 50) <= 30 else "Emphasize opportunities and optimism" if style_metrics.get('doom_vs_hope', 50) >= 70 else "Balanced approach") if style_metrics else "- **Doom vs Hope:** 50/100 - Balanced"}
{f"- **Practical vs Philosophical:** {style_metrics.get('practical_vs_philosophical', 50)}/100 - " + ("Focus on actionable how-to content" if style_metrics.get('practical_vs_philosophical', 50) <= 30 else "Focus on big ideas and concepts" if style_metrics.get('practical_vs_philosophical', 50) >= 70 else "Mix of both") if style_metrics else "- **Practical vs Philosophical:** 50/100 - Balanced"}
{f"- **Personal vs Objective:** {style_metrics.get('personal_vs_objective', 50)}/100 - " + ("More objective reporting tone" if style_metrics.get('personal_vs_objective', 50) <= 30 else "More personal 'I' statements and opinions" if style_metrics.get('personal_vs_objective', 50) >= 70 else "Balanced") if style_metrics else "- **Personal vs Objective:** 50/100 - Balanced"}
{f"- **Africa Focus:** {style_metrics.get('africa_focus', 50)}/100 - " + ("Global perspective" if style_metrics.get('africa_focus', 50) <= 30 else "Emphasize Africa/Global South angles" if style_metrics.get('africa_focus', 50) >= 70 else "Some Africa context") if style_metrics else "- **Africa Focus:** 50/100 - Balanced"}
{f"- **AI Skepticism:** {style_metrics.get('ai_skepticism', 50)}/100 - " + ("More skeptical of AI hype" if style_metrics.get('ai_skepticism', 50) <= 30 else "More enthusiastic about AI" if style_metrics.get('ai_skepticism', 50) >= 70 else "Balanced") if style_metrics else "- **AI Skepticism:** 50/100 - Balanced"}

Write SPECIFIC instructions for how each of these values should manifest in the writing, with examples of language to use.

## 5. SECTION-BY-SECTION INSTRUCTIONS

{sections_text if sections_text else "No additional sections - focus entirely on the main story."}

For each section above, write:
- The exact opening sentence or phrase
- How to present each bullet point (format, tone)
- The specific tone to use
- The exact word count target

## 6. SOURCING & CITATIONS (MANDATORY - ALL SOURCES MUST BE USED)

🚨 **CRITICAL - THIS IS MANDATORY:** Every single source URL listed below MUST appear in the final newsletter. This is non-negotiable.

**SOURCES PROVIDED (YOU MUST USE ALL OF THESE):**
{sources_text}

{"## KNOWLEDGE BASE FACTS (with URLs - YOU MUST USE ALL OF THESE):" if kb_facts_list else ""}
{chr(10).join([f"- **Fact {i+1}:** {fact.get('text', '')[:150]}... | **MANDATORY URL: {fact.get('source_url', 'No URL')}**" for i, fact in enumerate(kb_facts_list)]) if kb_facts_list else ""}

**YOUR TASK - MANDATORY SOURCE USAGE:**

For EACH source and KB fact above, you MUST write:

1. **List EVERY URL** - Go through the sources and KB facts above and list each URL
2. **Specify WHERE each URL should appear** - Be specific: "Use [source title] URL in paragraph [X] when discussing [topic]"
3. **Specify HOW to integrate it** - "Integrate as: 'According to [TechCrunch](url), AMD announced...'"
4. **Create a checklist** - List each URL and confirm it will be used

**REQUIRED FORMAT:**

**Source 1: [Title] - [URL]**
- Use in: [Specific location in newsletter]
- Integration: "[Exact sentence structure showing how to use it]"
- Example: "According to [TechCrunch](url), AMD announced new chips..."

**Source 2: [Title] - [URL]**
- Use in: [Specific location in newsletter]
- Integration: "[Exact sentence structure showing how to use it]"

[Continue for ALL sources and KB facts]

**CRITICAL RULES:**
- **EVERY URL must be used** - No exceptions. If there are 3 sources, all 3 URLs must appear in the newsletter
- **Integrate links naturally** - use [link text](url) format inline where relevant
- **Links should be part of the narrative** - not listed separately or at the end
- **Example format:** "A [TechCrunch report](url) found that..." NOT "TechCrunch found that... [See: url]"
- **Be specific about placement** - Don't just say "use in the newsletter" - say "use in paragraph 2 when discussing AMD's announcement"
- **DO NOT create a separate "Sources" or "Links" section** - all links must be woven into the narrative

## 7. CLOSING INSTRUCTIONS

Write the EXACT closing you want:
- The final 2-3 sentences
- The call to action (if any)
- The final thought to leave readers with
- The tone for the ending

## 8. ANTI-FABRICATION RULES (CRITICAL - ABSOLUTELY NO INVENTED MEMORIES)

🚨 **CRITICAL - THIS IS THE MOST IMPORTANT RULE:** GPT-4.1 must NEVER invent personal memories, childhood stories, or specific personal anecdotes. This is UNFORGIVABLE.

**ABSOLUTELY FORBIDDEN - NEVER INVENT:**
- ❌ **Personal childhood memories** - "I remember when I was 14 and bought a Cyrix processor..." - NEVER invent these
- ❌ **Specific personal experiences** - "I had saved all my pocket money..." - NEVER invent these
- ❌ **Personal anecdotes** - "I remember being told to buy..." - NEVER invent these
- ❌ **Specific dates from personal life** - "In 1996, I..." - NEVER invent these
- ❌ **Places visited** - "I visited [place] last week" - NEVER invent these
- ❌ **Conversations had** - "I was told..." - NEVER invent these
- ❌ **Personal purchases or decisions** - "I bought X because..." - NEVER invent these
- ❌ **Statistics without sources** - "75% of journalists" - NEVER invent these
- ❌ **Quotes from people** - NEVER fabricate quotes
- ❌ **Events attended** - NEVER invent events you attended

**WHAT TO DO INSTEAD:**
- ✅ Use general observations: "Many people remember when..." (not "I remember when...")
- ✅ Use the idea/angle provided by the user - that's REAL
- ✅ Use facts from sources and KB - those are REAL
- ✅ Use general statements: "The shift to AI-powered chips means..." (not personal memories)
- ✅ If you need to reference the past, use general statements: "In the 1990s, processors..." (not "I remember in 1996...")
- ✅ Start with the actual idea/topic, not invented personal memories
- ✅ Use the opening hook provided in the outline if available - that's what the user wants

**CRITICAL INSTRUCTION FOR GPT-4.1:**
Write explicit instructions that GPT-4.1 must:
- **NEVER start with "I remember when..." unless that exact memory is in the user's idea/outline**
- **NEVER invent childhood stories or personal anecdotes**
- **NEVER fabricate specific personal experiences, dates, or events**
- **ONLY use the idea, angle, and sources provided - those are REAL**
- **If the opening hook in the outline mentions a personal memory, use that EXACTLY - don't invent variations**
- **If no personal memory is provided, start with the topic directly or use general observations**

**Example of FORBIDDEN (inventing):**
- ❌ "I remember when Cyrix released their 133MHz processor in 1996. I had saved all my pocket money..." - COMPLETELY INVENTED
- ❌ "I was 14 when I bought my first computer..." - COMPLETELY INVENTED
- ❌ "I remember being told to buy a Cyrix..." - COMPLETELY INVENTED

**Example of CORRECT (using real information):**
- ✅ Start with the actual topic: "AMD announced new AI-powered PC chips. Here's what that means."
- ✅ Use the user's idea/angle if it contains personal info: "[Use the EXACT idea/angle provided]"
- ✅ Use general observations: "The latest chip announcements from AMD signal a shift in computing requirements."
- ✅ Reference the opening hook from the outline if provided: "[Use the EXACT opening hook from the outline]"

## 8b. ANTI-CLICHE RULES (CRITICAL - NEVER USE THESE)

🚨 **CRITICAL:** The clichés list in the Bible above shows phrases that make your writing sound generic and corporate. You MUST write explicit instructions to NEVER use these.

**EXAMPLES OF CLICHÉS TO AVOID (from the Bible's clichés list):**
- Generic corporate phrases: "change is coming fast", "land on your feet", "this is your moment"
- Motivational speak: "double down", "what makes you human", "let's get ready together"
- Overused phrases: "game changer", "paradigm shift", "think outside the box"
- Corporate jargon: "leverage", "synergy", "move the needle", "circle back"
- **Generic transition phrases:** "On the cusp of change", "As we navigate these uncharted waters", "In this ever-changing landscape"
- **Vague motivational language:** "embrace the future", "seize the opportunity", "chart a new course"

**CRITICAL INSTRUCTION FOR GPT-4.1:**
Write explicit instructions that GPT-4.1 must:
- **NEVER use any phrase from the clichés list** - even if it seems appropriate
- **Be specific and direct** - say exactly what you mean, not generic platitudes
- **Use authentic, personal language** - your real voice from the Bible, not corporate speak
- **Replace clichés with concrete examples** - real observations, not vague statements
- **Write as if talking to a colleague** - conversational and direct, not a corporate presentation
- **If a phrase sounds like it could be in a corporate email, don't use it** - use your actual voice from the Bible instead

**Example of what NOT to write:**
- ❌ "On the cusp of change, we must navigate these uncharted waters"
- ❌ "As we embrace the future, this is your moment to double down"
- ❌ "This game changer will help you land on your feet"

**Example of what TO write (based on Bible style):**
- ✅ Use the actual signature phrases and sentence patterns from the Bible examples above
- ✅ Be direct: "AMD announced new chips. Here's what that means."
- ✅ Use personal observations: "I was recently told I need to upgrade my computer..."
- ✅ Be specific: "Twelve AI cores. Eighty-one teraflops. Power redefined." (if this pattern appears in Bible)

## 9. FORMAT REQUIREMENTS

- Markdown format with ## headers for sections
- How to structure the newsletter (exact header hierarchy)
- Any specific formatting rules (bold, italics, lists, etc.)
- **CRITICAL:** DO NOT use horizontal rules (dashes like "---" or "***") to separate sections - remove all section dividers
- **CRITICAL:** Integrate links naturally into the text using [link text](url) format - links should be part of the narrative flow, not listed separately
- Links should appear inline where they're relevant, not at the end or in a separate section
- Example: "According to [TechCrunch](url), AI is transforming..." NOT "AI is transforming... [1] See: url"

---

# CRITICAL CHECKLIST - YOUR PROMPT MUST INCLUDE:

Before you write, verify you will include:

✅ **Word Counts:** Main story {main_word_count} words, Total {total_word_count} words - STATE THESE EXPLICITLY
✅ **Style Dial Numbers:** Reference each dial value (e.g., "doom_vs_hope is {style_metrics.get('doom_vs_hope', 50) if style_metrics else 50}/100, so...")
✅ **Bible Writing Style:** Include specific phrases, sentence patterns, and examples from your past newsletters
✅ **MANDATORY - Source URLs:** List EVERY source URL from the sources section above and specify WHERE each one will be used in the newsletter. This is non-negotiable - ALL sources must appear.
✅ **MANDATORY - Knowledge Base Links:** List EVERY KB fact URL and specify WHERE each one will be used. ALL KB URLs must appear in the newsletter.
✅ **User's Key Points:** Reference each key point specifically and where it goes
✅ **Story Type:** Reference the story type characteristics and how they affect the writing
✅ **RAG Examples:** Reference the similar passages and how to match that style
✅ **Anti-Cliche Rules:** Explicitly list cliches to avoid from the Bible and instruct GPT-4.1 to replace them with specific, authentic language

---

NOW WRITE THE COMPLETE PROMPT (2000-4000 words). 

**DO NOT** just list sections. **DO** write out the actual detailed instructions with:
- Specific word counts stated clearly
- Style dial numbers referenced with explanations
- Actual phrases from your writing style
- All URLs from KB and sources listed
- Specific instructions for each paragraph
- Exact opening and closing sentences

Fill in ALL the details above with specific content from the context provided."""

    # Check prompt length - if too long, truncate some context sections
    user_prompt_length = len(user_prompt_for_ft)
    if user_prompt_length > 100000:  # ~100k chars is getting very long
        # Truncate some context sections if needed (already done in the f-string above)
        pass
    
    try:
        # Validate API key
        if not os.getenv("OPENAI_API_KEY"):
            return {
                'error': 'OpenAI API key not found. Please set OPENAI_API_KEY in your environment.',
                'prompt': None,
                'model_used': None
            }
        
        # Check prompt lengths - truncate if needed
        system_len = len(system_prompt_for_ft)
        user_len = len(user_prompt_for_ft)
        
        if system_len > 50000:
            system_prompt_for_ft = system_prompt_for_ft[:50000] + "\n... [truncated - too long]"
        
        if user_len > 150000:  # Very long prompts can cause issues
            # Truncate context sections more aggressively
            user_prompt_for_ft = user_prompt_for_ft[:150000] + "\n\n... [context truncated due to length]"
        
        # Use GPT-4o for prompt generation (better at following complex instructions)
        # The fine-tuned model is trained to write newsletters, not prompts
        prompt_model = "gpt-4o"
        
        # Try the API call with better error handling
        try:
            response = client.chat.completions.create(
                model=prompt_model,
                messages=[
                    {"role": "system", "content": system_prompt_for_ft},
                    {"role": "user", "content": user_prompt_for_ft}
                ],
                temperature=0.7,  # Lower for more precise, detailed instructions
                max_tokens=6000,  # Increased to allow for full detailed prompt
            )
        except Exception as api_error:
            # If gpt-4o fails, try gpt-4o-mini as fallback
            try:
                prompt_model = "gpt-4o-mini"
                response = client.chat.completions.create(
                    model=prompt_model,
                    messages=[
                        {"role": "system", "content": system_prompt_for_ft},
                        {"role": "user", "content": user_prompt_for_ft}
                    ],
                    temperature=0.7,
                    max_tokens=6000,
                )
            except Exception as fallback_error:
                return {
                    'error': f'API call failed. gpt-4o error: {str(api_error)[:200]}. Fallback error: {str(fallback_error)[:200]}',
                    'prompt': None,
                    'model_used': 'gpt-4o (failed)'
                }
        
        if not response or not response.choices or not response.choices[0].message:
            return {
                'error': 'Invalid response from API - no content returned',
                'prompt': None,
                'model_used': prompt_model
            }
        
        meticulous_prompt = response.choices[0].message.content
        
        if not meticulous_prompt or len(meticulous_prompt.strip()) < 100:
            return {
                'error': f'Generated prompt is too short ({len(meticulous_prompt) if meticulous_prompt else 0} chars). Expected 2000-4000 words.',
                'prompt': None,
                'model_used': prompt_model
            }
        
        # Log the API call
        usage = response.usage
        if usage and USAGE_LOGGING_AVAILABLE:
            log_api_call(
                model=prompt_model,
                feature="meticulous_prompt_generation",
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens
            )
        
        # Build a SIMPLE system prompt - let the fine-tuned model's training do the work
        system_prompt_for_gpt4 = f"""You are Paul McNally, writing your newsletter "Develop AI".

Write naturally in your voice - punchy, personal, skeptical-but-curious about AI.

Key requirements:
- Word counts: Main story ~{main_word_count} words, Total ~{total_word_count} words
- Use ALL source URLs as inline links: [text](url)
- Don't fabricate personal memories or statistics
- Avoid cliches like "game changer", "paradigm shift", "this is your moment"
- Markdown format, no horizontal rules (---)

The detailed prompt below has everything you need. Write a natural, conversational newsletter."""
        
        return {
            'prompt': meticulous_prompt,
            'system_prompt': system_prompt_for_gpt4,
            'model_used': prompt_model,  # GPT-4.1 for prompt generation
            'fine_tuned_model_available': fine_tuned_model is not None,  # Track if FT model exists
            'input_tokens': usage.prompt_tokens if usage else 0,
            'output_tokens': usage.completion_tokens if usage else 0,
            'total_word_count': total_word_count,
            'main_word_count': main_word_count,
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'prompt': None,
            'model_used': 'gpt-4.1'
        }


def execute_approved_prompt(
    approved_prompt: str,
    system_prompt: str,
    outline_data: dict,
    temperature: float = 0.7
) -> dict:
    """
    Execute the user-approved prompt with GPT-4.1 to generate the final newsletter.
    
    This is the second stage: the fine-tuned model wrote the prompt,
    the user approved/edited it, now GPT-4.1 executes it.
    
    Returns:
        dict with 'content', 'model_used', etc.
    """
    
    if not approved_prompt:
        return {
            'error': 'No prompt provided',
            'content': None
        }
    
    # Use GPT-4o for execution (powerful, follows instructions well)
    execution_model = "gpt-4o"
    
    # Add the headline and preview to ensure they're used
    headline = outline_data.get('headline', '')
    preview = outline_data.get('preview', '')
    
    # Extract sources from the approved prompt to list them explicitly
    # Look for URLs in the prompt
    import re
    urls_in_prompt = re.findall(r'https?://[^\s\)\]\"\'<>]+', approved_prompt)
    
    # Build explicit source reminder
    source_reminder = ""
    if urls_in_prompt:
        source_reminder = f"\n\n🚨 **YOU MUST USE THESE {len(urls_in_prompt)} URLs IN YOUR NEWSLETTER:**\n"
        for i, url in enumerate(urls_in_prompt[:10], 1):  # Show up to 10
            source_reminder += f"{i}. {url[:80]}...\n" if len(url) > 80 else f"{i}. {url}\n"
        source_reminder += "\nEach URL above must appear as a clickable [link text](url) in your newsletter.\n"
    
    # Build the final prompt - simpler and more focused
    final_prompt = f"""# {headline}

*{preview}*

---

## YOUR INSTRUCTIONS:

{approved_prompt}
{source_reminder}

---

## CHECKLIST BEFORE YOU WRITE:
✅ Headline: "{headline}"
✅ Preview: "{preview}"  
✅ Word count: Follow the word counts in the instructions above
✅ Sources: Use ALL URLs listed above as [link text](url) inline
✅ Voice: Write as Paul McNally - punchy, personal, skeptical-but-curious
✅ No cliches: Avoid generic corporate phrases
✅ No fabrication: Don't invent personal memories or statistics
✅ Format: Markdown, no horizontal rules (---), links inline

BEGIN:"""

    try:
        response = client.chat.completions.create(
            model=execution_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": final_prompt}
            ],
            temperature=temperature,
            max_tokens=4000,
        )
        
        content = response.choices[0].message.content
        
        # Post-process: Remove horizontal rules (dashes) that might have been added
        if content:
            import re
            # Remove lines that are just dashes (---, ***, etc.)
            content = re.sub(r'^[-*_]{3,}\s*$', '', content, flags=re.MULTILINE)
            # Remove standalone dash lines between paragraphs
            content = re.sub(r'\n\s*[-]{3,}\s*\n', '\n\n', content)
            # Clean up multiple blank lines
            content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Log the API call
        usage = response.usage
        if usage and USAGE_LOGGING_AVAILABLE:
            log_api_call(
                model=execution_model,
                feature="newsletter_execution",
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens
            )
        
        return {
            'content': content,
            'model_used': execution_model,
            'input_tokens': usage.prompt_tokens if usage else 0,
            'output_tokens': usage.completion_tokens if usage else 0,
            'prompt_used': final_prompt,
            'system_prompt_used': system_prompt,
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'content': None,
            'model_used': execution_model
        }


# ============================================================================
# Quick Generation Functions
# ============================================================================

def quick_headlines(idea: str, count: int = 10) -> list[str]:
    """Generate multiple headline options quickly."""
    result = generate_newsletter(idea, format_type="headlines_only")
    if result.get('error'):
        return [result['error']]
    
    # Parse numbered headlines from content
    content = result.get('content', '')
    lines = content.split('\n')
    headlines = []
    for line in lines:
        # Match lines starting with numbers
        if line.strip() and line.strip()[0].isdigit():
            # Remove the number prefix
            headline = line.strip()
            headline = headline.lstrip('0123456789.):- ')
            if headline:
                headlines.append(headline)
    
    return headlines[:count]


def quick_outline(idea: str) -> str:
    """Generate a quick outline for a newsletter idea."""
    result = generate_newsletter(idea, format_type="outline")
    return result.get('content', result.get('error', 'Generation failed'))


# ============================================================================
# Test / CLI
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("NEWSLETTER GENERATOR")
    print("Trained on Paul McNally's Develop AI style")
    print("=" * 60)
    
    # Check if Bible exists
    if not BIBLE_FILE.exists():
        print("\n⚠️  Newsletter Bible not found!")
        print("Run this first: python style_analyzer.py")
        sys.exit(1)
    
    # Test generation
    test_idea = "The rise of AI-generated news anchors in Africa and what it means for journalism jobs"
    
    print(f"\n📝 Test idea: {test_idea}")
    print("\n" + "-" * 40)
    
    # Generate headlines
    print("\n🎯 Generating headlines...")
    headlines = quick_headlines(test_idea)
    
    if headlines:
        print("\nHEADLINE OPTIONS:")
        for i, h in enumerate(headlines, 1):
            print(f"  {i}. {h}")
    
    # Generate outline
    print("\n📋 Generating outline...")
    outline = quick_outline(test_idea)
    print("\nOUTLINE:")
    print(outline[:2000] if len(outline) > 2000 else outline)
    
    print("\n" + "=" * 60)
    print("To generate a full newsletter, use:")
    print("  from newsletter_generator import generate_newsletter")
    print("  result = generate_newsletter('your idea here')")
    print("=" * 60)

