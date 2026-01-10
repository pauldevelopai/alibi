"""
Letter+ - Newsletter Creation Studio

A professional tool to analyze, optimize, and generate Substack newsletters 
trained on your unique writing style.

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

# ============================================================================
# Page Configuration
# ============================================================================
st.set_page_config(
    page_title="Letter+",
    page_icon="L",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern CSS Theme
MODERN_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary: #2563eb;
        --primary-dark: #1d4ed8;
        --secondary: #64748b;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --bg-primary: #ffffff;
        --bg-secondary: #f8fafc;
        --bg-tertiary: #f1f5f9;
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-muted: #94a3b8;
        --border: #e2e8f0;
        --radius: 8px;
    }
    
    html, body, [class*="st-"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }
    
    h1 { font-weight: 700 !important; font-size: 1.75rem !important; color: var(--text-primary) !important; }
    h2 { font-weight: 600 !important; font-size: 1.125rem !important; color: var(--text-primary) !important; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }
    h3 { font-weight: 600 !important; font-size: 0.875rem !important; color: var(--text-secondary) !important; text-transform: uppercase; letter-spacing: 0.05em; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--bg-secondary);
        border-radius: var(--radius);
        padding: 4px;
        border: 1px solid var(--border);
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1rem;
        font-weight: 500;
        font-size: 0.875rem;
        color: var(--text-secondary);
        background: transparent;
        border-radius: calc(var(--radius) - 2px);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--bg-primary) !important;
        color: var(--primary) !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .stButton > button {
        font-weight: 500;
        font-size: 0.875rem;
        border-radius: var(--radius);
        border: 1px solid var(--border);
        transition: all 0.15s ease;
    }
    
    .stButton > button[kind="primary"] {
        background: var(--primary);
        border-color: var(--primary);
        color: white;
    }
    
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; font-weight: 600 !important; }
    [data-testid="stMetricLabel"] { font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted) !important; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .letter-header { margin-bottom: 1.5rem; }
    .letter-logo { font-size: 1.25rem; font-weight: 700; color: var(--primary); background: var(--bg-secondary); padding: 0.4rem 0.6rem; border-radius: var(--radius); border: 1px solid var(--border); display: inline-block; margin-right: 0.75rem; }
    .letter-title { font-size: 1.75rem; font-weight: 700; color: var(--text-primary); display: inline; }
    .letter-tagline { color: var(--text-muted); font-size: 0.875rem; margin-top: 0.25rem; }
</style>
"""

st.markdown(MODERN_CSS, unsafe_allow_html=True)

# Import our modules
from analysis import (
    get_merged_data,
    compute_all_features,
    get_top_n_by_open_rate,
    describe_feature_correlations,
    compute_headline_features,
    compute_body_features,
    compute_reach_score,
    classify_topics,
    DATA_DIR,
    RAW_DATA_FILE,
    STATS_FILE,
)
from openai_utils import (
    suggest_newsletter_improvements,
    prepare_best_examples,
    check_api_connection,
)
from scrape_substack import run_scraper
from style_analyzer import load_bible, run_analysis as regenerate_bible, load_all_newsletters

# Deep style analyzer for enhanced writing style extraction
try:
    from deep_style_analyzer import (
        run_deep_analysis, 
        load_deep_bible, 
        get_deep_style_context,
        save_custom_writing_sample,
        load_custom_writing_samples,
        clear_custom_writing_samples,
        merge_deep_into_bible,
        TEXTSTAT_AVAILABLE,
        SPACY_AVAILABLE,
        TEXTBLOB_AVAILABLE,
        SENTENCE_TRANSFORMERS_AVAILABLE
    )
    DEEP_ANALYZER_AVAILABLE = True
except ImportError:
    DEEP_ANALYZER_AVAILABLE = False
    TEXTSTAT_AVAILABLE = False
    SPACY_AVAILABLE = False
    TEXTBLOB_AVAILABLE = False
    SENTENCE_TRANSFORMERS_AVAILABLE = False
from newsletter_generator import generate_newsletter, quick_headlines

# Newsletter Engine - Self-improving generation system
try:
    from newsletter_engine import NewsletterEngine
    NEWSLETTER_ENGINE_AVAILABLE = True
except ImportError:
    NEWSLETTER_ENGINE_AVAILABLE = False
from advanced_metrics import load_analysis, get_metric_definitions, run_analysis as run_metrics_analysis
from section_analyzer import load_analysis as load_section_analysis, get_section_templates, run_analysis as run_section_analysis
from story_types import get_story_types, get_story_type_list
from image_service import (
    generate_image_dalle,
    suggest_image_prompts,
    search_images,
    get_search_suggestions,
    check_image_services,
)
from content_inbox import (
    load_inbox,
    add_to_inbox,
    remove_from_inbox,
    clear_inbox,
    get_inbox_stats,
    summarize_content,
    generate_ideas_from_inbox,
    parse_forwarded_email,
)
try:
    from news_fetcher import (
        fetch_all_news,
        get_recent_ai_news,
        get_africa_news,
        search_news,
        get_news_for_topic,
        format_for_newsletter,
        fetch_last_two_days,
        get_selectable_news,
    )
    HAS_NEWS_FETCHER = True
except ImportError:
    HAS_NEWS_FETCHER = False

# Try to import RAG system
try:
    from rag_system import get_writing_examples, build_embeddings_database
    RAG_AVAILABLE = True
except Exception:
    RAG_AVAILABLE = False

try:
    from knowledge_base import (
        load_knowledge_base,
        add_article,
        add_articles_batch,
        remove_article,
        get_articles,
        get_knowledge_context,
        get_stats as get_kb_stats,
        get_kb_metadata,
        search_articles,
        clear_old_articles,
        add_from_url,
        add_from_pdf,
        # NEW: Structured facts functions
        get_all_facts,
        get_facts_stats,
        get_relevant_facts,
        clear_old_facts,
        process_all_articles_for_facts,
        get_articles_without_facts,
        # NEW: URL validation and usage tracking
        validate_url,
        validate_all_articles,
        remove_fake_articles,
        record_article_usage,
        record_article_usage_by_url,
        get_article_usage,
        get_most_used_articles,
        is_url_fake,
    )
    HAS_KNOWLEDGE_BASE = True
except ImportError:
    HAS_KNOWLEDGE_BASE = False
from learning_system import (
    record_outline_edit,
    get_learning_context,
    get_edit_stats,
)
from newsletter_database import (
    create_newsletter,
    save_version,
    get_newsletter,
    get_version,
    update_newsletter_metadata,
    update_newsletter_stats,
    get_all_newsletter_stats,
    get_performance_learnings,
    delete_newsletter,
    list_newsletters,
    get_recent_newsletters,
    get_drafts,
    get_stats as get_db_stats,
    export_newsletter_markdown,
)
from session_persistence import (
    sync_to_streamlit,
    sync_from_streamlit,
    clear_and_reset_streamlit,
    has_work_in_progress,
    get_work_summary,
)

# Publishing Analytics
try:
    from publishing_analytics import (
        analyze_best_publishing_day,
        analyze_performance_trends,
        get_publishing_recommendation,
        generate_social_posts,
        generate_thread_content,
        get_publishing_checklist,
        get_module_status as get_publishing_status,
    )
    HAS_PUBLISHING = True
except ImportError:
    HAS_PUBLISHING = False

# Published newsletters for training
try:
    from published_newsletters import (
        publish_newsletter,
        get_published_newsletters,
        get_unpublished_for_training,
        export_for_fine_tuning as export_published_for_training,
        get_stats as get_published_stats,
    )
    HAS_PUBLISHED = True
except ImportError:
    HAS_PUBLISHED = False

try:
    from fine_tuning import (
        export_training_data,
        upload_training_file,
        create_fine_tuning_job,
        check_job_status,
        list_fine_tuning_jobs,
        list_fine_tuned_models,
        get_active_fine_tuned_model,
        set_active_model,
        load_fine_tuning_status,
        get_job_events,
        get_training_metrics,
        get_current_job_id,
        compare_models,
        add_to_training_data,
        get_incremental_training_count,
        trigger_incremental_training,
        should_auto_train,
        FINE_TUNABLE_MODELS,
        DEFAULT_BASE_MODEL,
    )
    HAS_FINE_TUNING = True
except ImportError:
    HAS_FINE_TUNING = False

# Try to import OpenAI usage dashboard
try:
    from openai_dashboard import (
        get_usage_summary,
        get_recent_calls,
        reset_usage_log,
        get_fine_tuned_model_stats,
        get_openai_models,
        check_api_health,
        log_api_call,
    )
    HAS_USAGE_DASHBOARD = True
except ImportError:
    HAS_USAGE_DASHBOARD = False

import json

# ============================================================================
# Saved Ideas Storage
# ============================================================================
SAVED_IDEAS_FILE = DATA_DIR / "saved_ideas.json"

def load_saved_ideas() -> list[dict]:
    """Load all saved ideas from disk."""
    if not SAVED_IDEAS_FILE.exists():
        return []
    try:
        with open(SAVED_IDEAS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_idea(idea: dict) -> dict:
    """Save an idea to the ideas bank."""
    ideas = load_saved_ideas()
    
    # Add metadata
    idea['id'] = f"idea_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(ideas)}"
    idea['saved_at'] = datetime.now().isoformat()
    idea['used'] = False
    
    ideas.insert(0, idea)  # Add to front
    
    # Keep max 50 ideas
    ideas = ideas[:50]
    
    with open(SAVED_IDEAS_FILE, 'w') as f:
        json.dump(ideas, f, indent=2)
    
    return idea

def mark_idea_used(idea_id: str):
    """Mark an idea as used."""
    ideas = load_saved_ideas()
    for idea in ideas:
        if idea.get('id') == idea_id:
            idea['used'] = True
            idea['used_at'] = datetime.now().isoformat()
            break
    
    with open(SAVED_IDEAS_FILE, 'w') as f:
        json.dump(ideas, f, indent=2)

def delete_saved_idea(idea_id: str):
    """Delete a saved idea."""
    ideas = load_saved_ideas()
    ideas = [i for i in ideas if i.get('id') != idea_id]
    
    with open(SAVED_IDEAS_FILE, 'w') as f:
        json.dump(ideas, f, indent=2)

def get_unused_ideas() -> list[dict]:
    """Get ideas that haven't been used yet."""
    ideas = load_saved_ideas()
    return [i for i in ideas if not i.get('used')]

# Custom CSS for a clean, professional look
st.markdown("""
<style>
    /* Main app styling */
    .main {
        background-color: #fafafa;
    }
    
    /* Headers */
    h1 {
        color: #1a1a2e;
        font-family: 'Georgia', serif;
        border-bottom: 3px solid #e94560;
        padding-bottom: 0.5rem;
    }
    
    h2, h3 {
        color: #16213e;
        font-family: 'Georgia', serif;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Score display */
    .score-high {
        color: #10b981;
        font-weight: bold;
    }
    
    .score-medium {
        color: #f59e0b;
        font-weight: bold;
    }
    
    .score-low {
        color: #ef4444;
        font-weight: bold;
    }
    
    /* Suggestion cards */
    .suggestion-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 24px;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0 0;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
    
    /* Feedback items */
    .feedback-positive {
        color: #10b981;
    }
    
    .feedback-warning {
        color: #f59e0b;
    }
    
    .feedback-negative {
        color: #ef4444;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Session State Initialization
# ============================================================================

if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.df = None
    st.session_state.df_with_features = None

if 'draft_title' not in st.session_state:
    st.session_state.draft_title = ""
    st.session_state.draft_preview = ""
    st.session_state.draft_body = ""

if 'generated_ideas' not in st.session_state:
    st.session_state.generated_ideas = []

if 'generated_content' not in st.session_state:
    st.session_state.generated_content = None
    st.session_state.generated_headlines = []

# Load persisted session (ideas, outlines, newsletters in progress)
sync_to_streamlit(st)


# ============================================================================
# Data Loading
# ============================================================================

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    """Load and process newsletter data."""
    df = get_merged_data()
    if not df.empty:
        df = compute_all_features(df)
    return df


def refresh_data():
    """Force refresh the data cache."""
    st.cache_data.clear()
    st.session_state.data_loaded = False


# ============================================================================
# Tab 1: Idea Generator
# ============================================================================

def render_idea_generator_tab():
    """Render the Idea Generator tab - generate newsletter ideas from collected content."""
    st.header("Idea Generator")
    st.markdown("*Generate newsletter ideas using your Knowledge Base and Newsletter Bible*")
    
    # Source indicator - shows what powers this feature
    render_source_indicator("Idea Generation", show_model=True, show_kb=True, show_bible=True, compact=False)
    
    # Check if Newsletter Bible exists
    bible_exists = (DATA_DIR / "newsletter_bible.json").exists()
    
    # Get Knowledge Base stats
    kb_stats = get_kb_stats() if HAS_KNOWLEDGE_BASE else {'total_articles': 0}
    
    # Stats bar
    col1, col2 = st.columns(2)
    with col1:
        if kb_stats.get('total_articles', 0) > 0:
            st.success(f"Knowledge Base: {kb_stats['total_articles']} articles")
        else:
            st.warning("Knowledge Base: Empty")
    with col2:
        if bible_exists:
            st.success("Newsletter Bible: Loaded")
        else:
            st.warning("Newsletter Bible: Not found")
    
    if kb_stats.get('total_articles', 0) == 0 and not bible_exists:
        st.warning("No content sources found!")
        st.markdown("""
        **To generate ideas, you need at least one of:**
        
        1. **Knowledge Base** - Go to Knowledge Base tab and add articles
        2. **Newsletter Bible** - Go to Settings and run the style analyzer
        
        The more sources, the better the ideas!
        """)
        return
    
    st.divider()
    
    # =====================
    # IDEA BANK - Show saved ideas that can be reused
    # =====================
    saved_ideas = load_saved_ideas()
    unused_saved_ideas = get_unused_ideas()
    used_ideas = [i for i in saved_ideas if i.get('used')]
    
    if saved_ideas:
        ideas_label = f"Your Ideas Bank ({len(unused_saved_ideas)} unused / {len(saved_ideas)} total)"
        with st.expander(ideas_label, expanded=len(unused_saved_ideas) > 0):
            if unused_saved_ideas:
                st.markdown("**Ready to use:**")
                for idx, saved in enumerate(unused_saved_ideas[:10]):  # Show max 10
                    with st.container():
                        col_idea, col_actions = st.columns([4, 1])
                        
                        with col_idea:
                            st.markdown(f"**{saved.get('title', 'Untitled')}**")
                            story_type = saved.get('story_type', 'general')
                            saved_date = saved.get('saved_at', '')[:10] if saved.get('saved_at') else ''
                            st.caption(f"{story_type.replace('_', ' ').title()} | Saved: {saved_date}")
                            
                            if saved.get('summary'):
                                st.markdown(f"*{saved.get('summary', '')[:200]}...*" if len(saved.get('summary', '')) > 200 else f"*{saved.get('summary', '')}*")
                            
                            if saved.get('angle'):
                                st.markdown(f"**Angle:** {saved.get('angle')}")
                            
                            # Show sources count
                            sources = saved.get('sources', [])
                            if sources:
                                st.caption(f"{len(sources)} sources attached")
                        
                        with col_actions:
                            if st.button("Use This", key=f"ideas_tab_use_saved_{saved.get('id', idx)}", use_container_width=True, type="primary"):
                                # Load into generator and switch to Write tab
                                st.session_state.generator_idea = saved.get('title', '') + "\n\n" + saved.get('summary', '')
                                if saved.get('angle'):
                                    st.session_state.generator_idea += f"\n\nAngle: {saved['angle']}"
                                st.session_state.generator_story_type = saved.get('story_type', 'news_analysis')
                                st.session_state.generator_idea_sources = saved.get('sources', [])
                                st.session_state.current_idea_id = saved.get('id')
                                
                                # Clear old outline data when loading a new idea
                                st.session_state.generator_outline = None
                                st.session_state.generator_edited_outline = None
                                st.session_state.generator_step = 1  # Reset to step 1
                                
                                # Mark as used
                                mark_idea_used(saved.get('id'))
                                
                                # Add sources to knowledge base
                                sources = saved.get('sources', [])
                                if sources and HAS_KNOWLEDGE_BASE:
                                    for source in sources:
                                        if isinstance(source, dict) and source.get('url'):
                                            try:
                                                add_article(
                                                    title=source.get('title', 'Untitled'),
                                                    url=source.get('url'),
                                                    source=source.get('publication', 'Unknown'),
                                                    published=source.get('date', ''),
                                                    category='idea_source'
                                                )
                                            except:
                                                pass
                                st.success("Idea loaded! Switch to the **Write** tab to use it.")
                                st.rerun()
                            
                            if st.button("Delete", key=f"ideas_tab_del_saved_{saved.get('id', idx)}", use_container_width=True):
                                delete_saved_idea(saved.get('id'))
                                st.rerun()
                        
                        st.divider()
            
            # Show used ideas - allow reusing them
            if used_ideas:
                st.markdown("---")
                st.markdown(f"**Previously used ({len(used_ideas)}) - You can reuse these:**")
                for idx, used in enumerate(used_ideas[:10]):  # Show max 10
                    with st.container():
                        col_idea, col_actions = st.columns([4, 1])
                        
                        with col_idea:
                            st.markdown(f"**{used.get('title', 'Untitled')}**")
                            story_type = used.get('story_type', 'general')
                            saved_date = used.get('saved_at', '')[:10] if used.get('saved_at') else ''
                            used_date = used.get('used_at', '')[:10] if used.get('used_at') else ''
                            date_info = f"Saved: {saved_date}"
                            if used_date:
                                date_info += f" | Used: {used_date}"
                            st.caption(f"{story_type.replace('_', ' ').title()} | {date_info}")
                            
                            if used.get('summary'):
                                st.markdown(f"*{used.get('summary', '')[:200]}...*" if len(used.get('summary', '')) > 200 else f"*{used.get('summary', '')}*")
                            
                            if used.get('angle'):
                                st.markdown(f"**Angle:** {used.get('angle')}")
                            
                            # Show sources count
                            sources = used.get('sources', [])
                            if sources:
                                st.caption(f"{len(sources)} sources attached")
                        
                        with col_actions:
                            if st.button("Use This", key=f"ideas_tab_use_used_{used.get('id', idx)}", use_container_width=True, type="secondary"):
                                # Load into generator and switch to Write tab
                                st.session_state.generator_idea = used.get('title', '') + "\n\n" + used.get('summary', '')
                                if used.get('angle'):
                                    st.session_state.generator_idea += f"\n\nAngle: {used['angle']}"
                                st.session_state.generator_story_type = used.get('story_type', 'news_analysis')
                                st.session_state.generator_idea_sources = used.get('sources', [])
                                st.session_state.current_idea_id = used.get('id')
                                
                                # Clear old outline data when loading a new idea
                                st.session_state.generator_outline = None
                                st.session_state.generator_edited_outline = None
                                st.session_state.generator_step = 1  # Reset to step 1
                                
                                # Update the used_at timestamp (idea is already marked as used)
                                mark_idea_used(used.get('id'))
                                
                                # Add sources to knowledge base (if not already added)
                                sources = used.get('sources', [])
                                if sources and HAS_KNOWLEDGE_BASE:
                                    for source in sources:
                                        if isinstance(source, dict) and source.get('url'):
                                            try:
                                                add_article(
                                                    title=source.get('title', 'Untitled'),
                                                    url=source.get('url'),
                                                    source=source.get('publication', 'Unknown'),
                                                    published=source.get('date', ''),
                                                    category='idea_source'
                                                )
                                            except:
                                                pass
                                st.success("Idea loaded! Switch to the **Write** tab to use it.")
                                st.rerun()
                            
                            if st.button("Delete", key=f"ideas_tab_del_used_{used.get('id', idx)}", use_container_width=True):
                                delete_saved_idea(used.get('id'))
                                st.rerun()
                        
                        st.divider()
    else:
        st.info("No saved ideas yet. Generate ideas below and save them to build your idea bank!")
    
    st.divider()
    
    # Generation options
    st.subheader("Generation Options")
    
    opt_col1, opt_col2 = st.columns(2)
    
    with opt_col1:
        # Story type preference
        story_type_options = [
            ("any", "Any type"),
            ("how_to", "How-To / Tutorial"),
            ("news_analysis", "News Analysis"),
            ("opinion", "Opinion / Take"),
            ("africa_focused", "Africa-Focused"),
            ("warning", "Warning / Concern"),
            ("future", "Future / Prediction"),
        ]
        selected_type = st.selectbox(
            "Preferred story type",
            options=[k for k, v in story_type_options],
            format_func=lambda x: next(v for k, v in story_type_options if k == x),
            key="idea_gen_type"
        )
    
    with opt_col2:
        additional_context = st.text_input(
            "Additional focus or context (optional)",
            placeholder="e.g., 'Focus on tools journalists can use this week'",
            key="idea_gen_context"
        )
    
    st.divider()
    
    # Generate button - show which model will be used
    style_model, is_fine_tuned = get_active_model_display()
    model_display = style_model if is_fine_tuned else "gpt-4o-mini"
    
    if st.button("Generate Newsletter Ideas", type="primary", use_container_width=True):
        with st.spinner(f"Generating ideas with `{model_display}`... (30-60 seconds)"):
            result = generate_ideas_from_inbox(
                story_type=selected_type if selected_type != "any" else "",
                additional_context=additional_context,
                max_items=15
            )
        
        if result.get('error'):
            st.error(f"Error: {result['error']}")
            return
        
        ideas = result.get('ideas', [])
        
        if not ideas:
            st.warning("No ideas generated. Try adding more content to your inbox.")
            return
        
        sources_used = []
        if result.get('used_knowledge_base'):
            sources_used.append("Knowledge Base")
        if result.get('used_inbox'):
            sources_used.append(f"{result.get('source_count', 0)} inbox items")
        if result.get('used_bible'):
            sources_used.append("Newsletter Bible")
        
        # Show ACTUAL model used from result
        model_used = result.get('model_used', 'gpt-4o-mini')
        st.success(f"Generated {len(ideas)} ideas | Model: `{model_used}`")
        st.caption(f"Sources: {', '.join(sources_used) if sources_used else 'Auto-fetched news'}")
        
        # Store ideas in session state
        st.session_state.generated_ideas = ideas
    
    # Display generated ideas
    if st.session_state.get('generated_ideas'):
        st.subheader("Newsletter Ideas")
        
        for i, idea in enumerate(st.session_state.generated_ideas, 1):
            with st.container():
                # Idea card
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"### {i}. {idea.get('title', 'Untitled')}")
                    
                    # Story type badge
                    story_type = idea.get('story_type', 'general')
                    type_colors = {
                        'how_to': '🔧',
                        'news_analysis': '',
                        'opinion': '💭',
                        'africa_focused': '',
                        'warning': '',
                        'future': '🔮',
                    }
                    type_emoji = type_colors.get(story_type, '')
                    st.caption(f"**{type_emoji} {story_type.replace('_', ' ').title()}**")
                    
                    # Summary
                    st.markdown(idea.get('summary', ''))
                    
                    # Angle
                    if idea.get('angle'):
                        st.markdown(f"**Angle:** *{idea['angle']}*")
                    
                    # SOURCES - Display prominently with clickable links
                    sources = idea.get('sources', [])
                    if sources:
                        st.markdown("**Sources (click to verify):**")
                        for source in sources:
                            if isinstance(source, dict):
                                url = source.get('url', '')
                                title = source.get('title', 'Source')
                                pub = source.get('publication', '')
                                date = source.get('date', '')
                                if url and url.startswith('http'):
                                    link_text = f"[{title}]({url})"
                                    if pub:
                                        link_text += f" - *{pub}*"
                                    if date:
                                        link_text += f" ({date})"
                                    st.markdown(f"  • {link_text}")
                                else:
                                    st.markdown(f"  • {title} - {pub} ({date})")
                            elif isinstance(source, str):
                                if source.startswith('http'):
                                    st.markdown(f"  • [{source}]({source})")
                                else:
                                    st.markdown(f"  • {source}")
                    
                    # Search query if no direct sources
                    search_query = idea.get('search_query', '')
                    if search_query:
                        google_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
                        st.markdown(f"**Find sources:** [Google: \"{search_query}\"]({google_url})")
                    
                    # Why it works (from Bible patterns)
                    if idea.get('why_it_works'):
                        st.info(f"**Why this works:** {idea['why_it_works']}")
                    
                    # Suggested sections
                    if idea.get('sections'):
                        st.caption(f"**Sections:** {', '.join(idea['sections'])}")
                
                with col2:
                    # Save to Ideas Bank button
                    if st.button("Save to Ideas Bank", key=f"save_idea_bank_{i}", use_container_width=True):
                        saved_idea = save_idea({
                            'title': idea.get('title', ''),
                            'summary': idea.get('summary', ''),
                            'angle': idea.get('angle', ''),
                            'story_type': idea.get('story_type', 'news_analysis'),
                            'sources': idea.get('sources', []),
                            'why_it_works': idea.get('why_it_works', ''),
                            'sections': idea.get('sections', []),
                            'search_query': idea.get('search_query', ''),
                        })
                        st.success(f"Saved to Ideas Bank!")
                        st.info("Go to **Write** tab > Step 1 to use saved ideas")
                    
                    if st.button("Use Now", key=f"use_idea_{i}", use_container_width=True, type="primary"):
                        # Save to ideas bank first
                        saved_idea = save_idea({
                            'title': idea.get('title', ''),
                            'summary': idea.get('summary', ''),
                            'angle': idea.get('angle', ''),
                            'story_type': idea.get('story_type', 'news_analysis'),
                            'sources': idea.get('sources', []),
                            'why_it_works': idea.get('why_it_works', ''),
                            'sections': idea.get('sections', []),
                            'search_query': idea.get('search_query', ''),
                        })
                        
                        # Load into generator with full context
                        st.session_state.generator_idea = idea.get('title', '') + "\n\n" + idea.get('summary', '')
                        if idea.get('angle'):
                            st.session_state.generator_idea += f"\n\nAngle: {idea['angle']}"
                        st.session_state.generator_story_type = idea.get('story_type', 'news_analysis')
                        st.session_state.current_idea_id = saved_idea.get('id')
                        
                        # Clear old outline data when loading a new idea
                        st.session_state.generator_outline = None
                        st.session_state.generator_edited_outline = None
                        st.session_state.generator_step = 1  # Reset to step 1
                        
                        # Store sources for the generator to use
                        st.session_state.generator_idea_sources = idea.get('sources', [])
                        
                        # Add sources to knowledge base
                        sources = idea.get('sources', [])
                        if sources and HAS_KNOWLEDGE_BASE:
                            added_count = 0
                            for source in sources:
                                if isinstance(source, dict) and source.get('url'):
                                    try:
                                        add_article(
                                            title=source.get('title', 'Untitled'),
                                            url=source.get('url'),
                                            source=source.get('publication', 'Unknown'),
                                            published=source.get('date', ''),
                                            category='idea_source'
                                        )
                                        added_count += 1
                                    except:
                                        pass
                        
                        st.success(f"Ready! Go to Write tab")
                
                st.divider()
        
        # Clear ideas button
        if st.button("Clear Ideas", key="clear_ideas"):
            st.session_state.generated_ideas = []
            st.rerun()


# ============================================================================
# Model/Source Indicator Component
# ============================================================================

def render_source_indicator(
    feature_name: str,
    show_model: bool = True,
    show_kb: bool = True,
    show_bible: bool = False,
    compact: bool = False
):
    """
    Render a simple, accurate indicator showing which AI model is used.
    Shows REAL model names - no fluff.
    """
    # Get the ACTUAL model being used
    style_model, is_fine_tuned = get_active_model_display()
    
    # Build indicator parts
    parts = []
    
    # Model info - ACCURATE
    if show_model:
        if is_fine_tuned:
            # Show actual fine-tuned model ID
            parts.append(f"Style: `{style_model}`")
            parts.append("Content: `gpt-4.1`")
        else:
            parts.append("Model: `gpt-4o-mini`")
    
    # KB info
    if show_kb and HAS_KNOWLEDGE_BASE:
        kb_stats = get_kb_stats()
        kb_count = kb_stats.get('total_articles', 0)
        if kb_count > 0:
            parts.append(f"KB: {kb_count} articles")
    
    # Bible info
    if show_bible:
        bible = load_bible()
        if bible:
            count = bible.get('meta', {}).get('newsletters_analyzed', 0)
            parts.append(f"Bible: {count} newsletters")
    
    # Display as simple caption
    if parts:
        st.caption(" | ".join(parts))


def get_source_status_text() -> str:
    """Get a simple text status showing ACTUAL models used."""
    style_model, is_fine_tuned = get_active_model_display()
    
    parts = []
    
    # Show actual model
    if is_fine_tuned:
        parts.append(f"Style: {style_model}")
        parts.append("Content: gpt-4.1")
    else:
        parts.append("Model: gpt-4o-mini")
    
    # KB count
    if HAS_KNOWLEDGE_BASE:
        kb_stats = get_kb_stats()
        kb_count = kb_stats.get('total_articles', 0)
        if kb_count > 0:
            parts.append(f"KB: {kb_count}")
    
    return " | ".join(parts)


# ============================================================================
# Tab 3: Knowledge Base
# ============================================================================

def render_knowledge_base_tab():
    """Render the unified Knowledge Base tab (includes news scraping)."""
    st.header("Knowledge Base")
    st.markdown("*Scrape AI news, add articles/reports, and build your research library for newsletters*")
    
    # Source indicator
    render_source_indicator("Knowledge Base", show_model=False, show_kb=True, show_bible=False, compact=True)
    
    st.divider()
    
    if not HAS_KNOWLEDGE_BASE:
        st.error("Knowledge base module not available. Please check your installation.")
        return
    
    # Get stats
    kb_stats = get_kb_stats()
    kb_metadata = get_kb_metadata()
    
    # Get facts stats too
    try:
        facts_stats = get_facts_stats()
    except:
        facts_stats = {'total_facts': 0, 'by_type': {}, 'by_confidence': {}}
    
    # Stats row - Articles
    st.markdown("### Articles")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Articles", kb_stats.get('total_articles', 0))
    with col2:
        st.metric("Recent (7 days)", kb_stats.get('recent_articles', 0))
    with col3:
        st.metric("📂 Categories", len(kb_stats.get('by_category', {})))
    with col4:
        st.metric("Sources", len(kb_stats.get('by_source', {})))
    with col5:
        by_type = kb_metadata.get('by_type', {})
        pdfs = by_type.get('pdf', 0)
        st.metric("PDFs", pdfs)
    
    # Stats row - Extracted Facts (NEW)
    st.markdown("### Extracted Facts")
    st.caption("*Facts are automatically extracted when you add articles. They're matched to your newsletter topics and injected as citations.*")
    
    fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns(5)
    with fcol1:
        st.metric("Total Facts", facts_stats.get('total_facts', 0))
    with fcol2:
        by_conf = facts_stats.get('by_confidence', {})
        st.metric("High Confidence", by_conf.get('high', 0))
    with fcol3:
        st.metric("Medium Confidence", by_conf.get('medium', 0))
    with fcol4:
        st.metric("Used in Newsletters", facts_stats.get('used_facts', 0))
    with fcol5:
        by_type_facts = facts_stats.get('by_type', {})
        st.metric("Statistics", by_type_facts.get('statistic', 0))
    
    # Last updated info
    if kb_stats.get('last_updated'):
        try:
            dt = datetime.fromisoformat(kb_stats['last_updated'].replace('Z', '+00:00'))
            st.caption(f"*Last updated: {dt.strftime('%B %d, %Y at %H:%M')}*")
        except:
            pass
    
    st.divider()
    
    # ===========================================================================
    # MAIN TABS: Scrape News | Add Content | Browse Articles | Browse Facts | Manage
    # ===========================================================================
    scrape_tab, add_tab, browse_tab, facts_tab, manage_tab = st.tabs([
        "Scrape News",
        "Add Content",
        "Browse Articles",
        "Browse Facts",
        "Manage"
    ])
    
    # ===========================================================================
    # TAB 0: SCRAPE NEWS (moved from Content Inbox)
    # ===========================================================================
    with scrape_tab:
        st.subheader("Scrape Recent AI News")
        st.markdown("*Fetch AI news from RSS feeds. Select articles to add to your Knowledge Base.*")
        
        if not HAS_NEWS_FETCHER:
            st.warning("News fetcher not available. Install feedparser: `pip install feedparser`")
        else:
            # Fetch and Clear buttons
            fetch_col, clear_col, checkbox_col = st.columns([2, 1, 1])
            with fetch_col:
                if st.button("Scrape Latest AI News", type="primary", use_container_width=True, key="kb_scrape_news"):
                    with st.spinner("Fetching news from RSS feeds (last 2 days)..."):
                        news = get_selectable_news()
                        st.session_state['scraped_news'] = news
                        st.success(f"Found {len(news)} articles from the last 2 days")
            
            with clear_col:
                if st.button("Clear Scraped News", use_container_width=True, key="kb_clear_scraped"):
                    st.session_state['scraped_news'] = []
                    st.rerun()
            
            with checkbox_col:
                include_africa = st.checkbox("Include Africa tech", value=True, key="kb_include_africa")
            
            # Display scraped news with selection (persisted in session state)
            if 'scraped_news' in st.session_state and st.session_state['scraped_news']:
                news = st.session_state['scraped_news']
                
                st.markdown(f"**{len(news)} articles available** - select the ones you want to add to your knowledge base:")
                
                # Select all / none
                sel_col1, sel_col2, sel_col3 = st.columns([1, 1, 2])
                with sel_col1:
                    if st.button("Select All", key="kb_select_all"):
                        for article in news:
                            article['selected'] = True
                        st.rerun()
                with sel_col2:
                    if st.button("Select None", key="kb_select_none"):
                        for article in news:
                            article['selected'] = False
                        st.rerun()
                with sel_col3:
                    selected_count = sum(1 for a in news if a.get('selected', False))
                    st.markdown(f"**{selected_count}** selected")
                
                st.divider()
                
                # Display articles in a scrollable container
                for i, article in enumerate(news):
                    with st.container():
                        chk_col, info_col = st.columns([1, 10])
                        
                        with chk_col:
                            selected = st.checkbox(
                                "",
                                value=article.get('selected', False),
                                key=f"kb_select_article_{i}"
                            )
                            article['selected'] = selected
                        
                        with info_col:
                            # Source badge
                            source = article.get('source', 'Unknown')
                            category = article.get('category', 'tech')
                            badge = "" if category == 'africa' else ""
                            
                            st.markdown(f"**{article.get('title', 'Untitled')}**")
                            st.markdown(f"{badge} {source} | [Link]({article.get('url', '#')})")
                            
                            if article.get('summary'):
                                st.caption(article['summary'][:150] + "...")
                        
                        st.divider()
                
                # Add selected to knowledge base
                st.markdown("### Add Selected to Knowledge Base")
                selected_articles = [a for a in news if a.get('selected', False)]
                
                if selected_articles:
                    add_col1, add_col2 = st.columns([2, 1])
                    with add_col1:
                        if st.button(f"Add {len(selected_articles)} Articles to Knowledge Base", type="primary", key="kb_add_selected"):
                            added = add_articles_batch(selected_articles)
                            st.success(f"Added {added} articles to knowledge base!")
                            # Clear selection but keep the news list
                            for article in news:
                                article['selected'] = False
                            st.rerun()
                    with add_col2:
                        st.caption("Articles will be added with automatic fact extraction")
                else:
                    st.info("Select articles above to add them to your knowledge base")
            else:
                st.info("Click 'Scrape Latest AI News' to fetch recent articles from RSS feeds")
    
    # ===========================================================================
    # TAB 1: ADD CONTENT
    # ===========================================================================
    with add_tab:
        st.subheader("Add to Knowledge Base")
        
        add_method = st.radio(
            "How would you like to add content?",
            ["From URL", "Upload PDF", "✍️ Manual Entry"],
            horizontal=True,
            key="kb_add_method"
        )
        
        st.divider()
        
        # ----- ADD FROM URL -----
        if add_method == "From URL":
            st.markdown("### Add Article from URL")
            st.markdown("*Paste a URL and we'll automatically extract the article content.*")
            
            url_input = st.text_input(
                "Article URL:",
                placeholder="https://example.com/article-about-ai...",
                key="kb_url_input"
            )
            
            # Category selection
            url_category = st.selectbox(
                "Category:",
                ["ai", "africa", "tech", "policy", "research", "tools", "media", "other"],
                index=0,
                key="kb_url_category"
            )
            
            if st.button("Fetch & Add Article", type="primary", disabled=not url_input):
                if url_input:
                    with st.spinner("Fetching article content and extracting facts..."):
                        result = add_from_url(url_input)
                        
                        if result.get('success'):
                            article = result.get('article', {})
                            facts_count = result.get('facts_extracted', 0)
                            st.success(f"Added: **{article.get('title', 'Article')}**")
                            st.markdown(f"*Source: {article.get('source', 'Unknown')} | Published: {article.get('published', 'Unknown')}*")
                            if facts_count > 0:
                                st.info(f"Extracted **{facts_count} citable facts** (statistics, quotes, claims)")
                            if article.get('summary'):
                                st.caption(f"{article['summary'][:200]}...")
                            st.rerun()
                        else:
                            st.error(f"{result.get('error', 'Failed to fetch article')}")
            
            # Bulk URL input
            st.divider()
            st.markdown("#### Add Multiple URLs")
            bulk_urls = st.text_area(
                "Paste multiple URLs (one per line):",
                height=100,
                key="kb_bulk_urls",
                placeholder="https://example1.com/article\nhttps://example2.com/article"
            )
            
            if st.button("Add All URLs", disabled=not bulk_urls):
                urls = [u.strip() for u in bulk_urls.split('\n') if u.strip().startswith('http')]
                if urls:
                    progress = st.progress(0)
                    success_count = 0
                    
                    for i, url in enumerate(urls):
                        result = add_from_url(url)
                        if result.get('success'):
                            success_count += 1
                        progress.progress((i + 1) / len(urls))
                    
                    st.success(f"Added {success_count} of {len(urls)} articles")
                    st.rerun()
        
        # ----- UPLOAD PDF -----
        elif add_method == "Upload PDF":
            st.markdown("### Upload PDF Report or Document")
            st.markdown("*Upload research papers, reports, or whitepapers to add to your knowledge base.*")
            
            uploaded_file = st.file_uploader(
                "Choose a PDF file:",
                type=['pdf'],
                key="kb_pdf_upload"
            )
            
            if uploaded_file:
                st.info(f"**{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
                
                # Optional metadata
                col1, col2 = st.columns(2)
                with col1:
                    pdf_title = st.text_input(
                        "Title (optional - will extract from PDF):",
                        key="kb_pdf_title"
                    )
                    pdf_source = st.text_input(
                        "Source/Publisher:",
                        key="kb_pdf_source",
                        placeholder="e.g., McKinsey, Stanford, WHO"
                    )
                
                with col2:
                    pdf_category = st.selectbox(
                        "Category:",
                        ["report", "research", "whitepaper", "policy", "analysis", "other"],
                        key="kb_pdf_category"
                    )
                    pdf_date = st.date_input(
                        "Publication Date:",
                        value=datetime.now(),
                        key="kb_pdf_date"
                    )
                
                if st.button("Upload & Process PDF", type="primary"):
                    with st.spinner("Extracting text from PDF and analyzing for citable facts..."):
                        pdf_bytes = uploaded_file.read()
                        result = add_from_pdf(
                            pdf_content=pdf_bytes,
                            filename=uploaded_file.name,
                            title=pdf_title,
                            source=pdf_source,
                            category=pdf_category,
                            published=pdf_date.strftime('%Y-%m-%d')
                        )
                        
                        if result.get('success'):
                            article = result.get('article', {})
                            facts_count = result.get('facts_extracted', 0)
                            st.success(f"Added PDF: **{article.get('title', uploaded_file.name)}**")
                            
                            if facts_count > 0:
                                st.info(f"Extracted **{facts_count} citable facts** (statistics, quotes, claims)")
                            
                            if article.get('key_points'):
                                st.markdown("**Key Points Extracted:**")
                                for point in article['key_points'][:3]:
                                    st.markdown(f"• {point[:100]}...")
                            
                            if result.get('message'):
                                st.caption(result['message'])
                            st.rerun()
                        else:
                            st.error(f"{result.get('error', 'Failed to process PDF')}")
                            st.markdown("""
                            **Troubleshooting:**
                            - Make sure the PDF contains selectable text (not scanned images)
                            - Install pypdf: `pip install pypdf`
                            - For scanned PDFs, you may need OCR support
                            """)
        
        # ----- MANUAL ENTRY -----
        elif add_method == "✍️ Manual Entry":
            st.markdown("### ✍️ Add Article Manually")
            st.markdown("*Manually enter article details when URL extraction doesn't work.*")
            
            with st.form("manual_kb_entry"):
                manual_title = st.text_input("Title: *", placeholder="Article headline or report title")
                manual_url = st.text_input("URL: *", placeholder="https://...")
                
                col1, col2 = st.columns(2)
                with col1:
                    manual_source = st.text_input("Source/Publication:", placeholder="e.g., TechCrunch, Reuters")
                    manual_category = st.selectbox(
                        "Category:",
                        ["ai", "africa", "tech", "policy", "research", "tools", "media", "report", "other"]
                    )
                with col2:
                    manual_date = st.date_input("Publication Date:", value=datetime.now())
                
                manual_summary = st.text_area(
                    "Summary/Description:",
                    height=100,
                    placeholder="Brief summary of the article..."
                )
                
                manual_key_points = st.text_area(
                    "Key Points (one per line):",
                    height=80,
                    placeholder="Main finding or insight\nAnother key point\n..."
                )
                
                submitted = st.form_submit_button("Add to Knowledge Base", type="primary")
                
                if submitted:
                    if not manual_title or not manual_url:
                        st.error("Title and URL are required")
                    else:
                        key_points = [kp.strip() for kp in manual_key_points.split('\n') if kp.strip()]
                        
                        article = add_article(
                            title=manual_title,
                            url=manual_url,
                            source=manual_source or "Manual Entry",
                            summary=manual_summary,
                            published=manual_date.strftime('%Y-%m-%d'),
                            category=manual_category,
                            key_points=key_points
                        )
                        
                        st.success(f"Added: **{article.get('title')}**")
                        st.rerun()
    
    # ===========================================================================
    # TAB 2: BROWSE ARTICLES
    # ===========================================================================
    with browse_tab:
        st.subheader("Browse Knowledge Base")
        
        articles = get_articles(limit=100)
        
        if not articles:
            st.info("📭 No articles in knowledge base yet. Use the **Add Content** tab to add articles.")
        else:
            # Search and filter
            search_col, filter_col = st.columns([2, 1])
            
            with search_col:
                kb_search = st.text_input(
                    "Search:",
                    placeholder="Search by title, source, or keyword...",
                    key="kb_browse_search"
                )
            
            with filter_col:
                categories = list(set(a.get('category', 'general') for a in articles))
                category_filter = st.selectbox(
                    "Filter by category:",
                    ["All"] + sorted(categories),
                    key="kb_category_filter"
                )
            
            # Apply filters
            filtered_articles = articles
            if kb_search:
                kb_search_lower = kb_search.lower()
                filtered_articles = [
                    a for a in filtered_articles
                    if kb_search_lower in a.get('title', '').lower()
                    or kb_search_lower in a.get('source', '').lower()
                    or kb_search_lower in a.get('summary', '').lower()
                ]
            
            if category_filter != "All":
                filtered_articles = [a for a in filtered_articles if a.get('category') == category_filter]
            
            st.markdown(f"**Showing {len(filtered_articles)} articles** (sorted by date added)")
            
            # Display articles
            for i, article in enumerate(filtered_articles):
                article_type = article.get('type', 'article')
                type_icon = "" if article_type == 'pdf' else ""
                
                with st.container():
                    col1, col2, col3 = st.columns([5, 1, 0.5])
                    
                    with col1:
                        title = article.get('title', 'Untitled')
                        url = article.get('url', '')
                        
                        # Title with link if URL
                        if url and not url.startswith('pdf://'):
                            st.markdown(f"**{type_icon} [{title[:70]}{'...' if len(title) > 70 else ''}]({url})**")
                        else:
                            st.markdown(f"**{type_icon} {title[:70]}{'...' if len(title) > 70 else ''}**")
                        
                        # Metadata line
                        source = article.get('source', 'Unknown')
                        date = article.get('published', article.get('added_at', ''))[:10]
                        category = article.get('category', 'general')
                        
                        st.caption(f"{source} | {date} | {category}")
                        
                        # Summary preview
                        if article.get('summary'):
                            st.caption(f"*{article['summary'][:120]}...*")
                    
                    with col2:
                        used = article.get('used_count', 0)
                        if used > 0:
                            st.caption(f"Used {used}x")
                    
                    with col3:
                        if st.button("", key=f"kb_del_{article.get('id', i)}", help="Remove"):
                            remove_article(article.get('id'))
                            st.rerun()
                
                if i < len(filtered_articles) - 1:
                    st.markdown("---")
    
    # ===========================================================================
    # TAB 3: BROWSE FACTS
    # ===========================================================================
    with facts_tab:
        st.subheader("Browse Extracted Facts")
        st.markdown("*These facts were automatically extracted from your articles. They're matched to your newsletter topics and injected as citations.*")
        
        try:
            all_facts = get_all_facts(limit=100)
        except:
            all_facts = []
        
        if not all_facts:
            st.info("No facts extracted yet. Add articles to your Knowledge Base and facts will be automatically extracted.")
        else:
            # Filters
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                fact_type_filter = st.selectbox(
                    "Filter by Type:",
                    ["All", "statistic", "quote", "announcement", "claim", "date"],
                    key="fact_type_filter"
                )
            
            with filter_col2:
                confidence_filter = st.selectbox(
                    "Filter by Confidence:",
                    ["All", "high", "medium", "low"],
                    key="confidence_filter"
                )
            
            with filter_col3:
                # Test relevance matching
                topic_test = st.text_input(
                    "Test topic relevance:",
                    placeholder="e.g., AI agents in healthcare",
                    key="fact_topic_test"
                )
            
            st.divider()
            
            # Filter facts
            filtered_facts = all_facts
            if fact_type_filter != "All":
                filtered_facts = [f for f in filtered_facts if f.get('fact_type') == fact_type_filter]
            if confidence_filter != "All":
                filtered_facts = [f for f in filtered_facts if f.get('confidence') == confidence_filter]
            
            # If topic test, show relevance scores
            if topic_test:
                st.markdown(f"### Facts Relevant to: *{topic_test}*")
                try:
                    relevant_facts = get_relevant_facts(topic_test, max_facts=20)
                    filtered_facts = relevant_facts
                    st.info(f"Found {len(relevant_facts)} relevant facts")
                except Exception as e:
                    st.error(f"Relevance matching error: {e}")
            
            st.caption(f"Showing {len(filtered_facts)} facts")
            
            # Display facts
            for i, fact in enumerate(filtered_facts):
                confidence_emoji = {'high': '', 'medium': '', 'low': ''}.get(fact.get('confidence', 'medium'), '')
                fact_type = fact.get('fact_type', 'fact').upper()
                
                with st.container():
                    st.markdown(f"**{confidence_emoji} [{fact_type}]** {fact.get('text', '')}")
                    
                    if fact.get('speaker'):
                        st.caption(f"Speaker: *{fact.get('speaker')}*")
                    
                    # Metadata
                    meta_cols = st.columns([2, 2, 1, 1])
                    with meta_cols[0]:
                        st.caption(f"{fact.get('citation', 'No URL')}")
                    with meta_cols[1]:
                        st.caption(f"{fact.get('source_name', 'Unknown')}")
                    with meta_cols[2]:
                        st.caption(f"{fact.get('source_date', 'Unknown')[:10] if fact.get('source_date') else 'Unknown'}")
                    with meta_cols[3]:
                        if fact.get('relevance_score'):
                            st.caption(f"{fact.get('relevance_score', 0):.1f}")
                        elif fact.get('used_count', 0) > 0:
                            st.caption(f"Used {fact['used_count']}x")
                    
                    if fact.get('keywords'):
                        st.caption(f"{', '.join(fact['keywords'][:5])}")
                    
                    if i < len(filtered_facts) - 1:
                        st.markdown("---")
    
    # ===========================================================================
    # TAB 4: MANAGE
    # ===========================================================================
    with manage_tab:
        st.subheader("Manage Knowledge Base")
        
        # Stats breakdown
        st.markdown("### Statistics")
        
        by_category = kb_stats.get('by_category', {})
        by_source = kb_stats.get('by_source', {})
        by_type = kb_metadata.get('by_type', {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**By Category:**")
            if by_category:
                for cat, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
                    st.markdown(f"• {cat}: {count}")
            else:
                st.caption("No articles yet")
        
        with col2:
            st.markdown("**By Source:**")
            if by_source:
                for source, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True)[:10]:
                    st.markdown(f"• {source}: {count}")
            else:
                st.caption("No articles yet")
        
        with col3:
            st.markdown("**By Type:**")
            if by_type:
                for t, count in by_type.items():
                    icon = "" if t == 'pdf' else ""
                    st.markdown(f"• {icon} {t}: {count}")
            else:
                st.caption("No articles yet")
        
        st.divider()
        
        # Maintenance actions
        st.markdown("### Maintenance")
        
        action_col1, action_col2, action_col3 = st.columns(3)
        
        with action_col1:
            if st.button("Clear Old (30+ days)", use_container_width=True):
                removed = clear_old_articles(days=30)
                st.success(f"Removed {removed} old articles")
                st.rerun()
        
        with action_col2:
            if st.button("Clear Old (7+ days)", use_container_width=True):
                removed = clear_old_articles(days=7)
                st.success(f"Removed {removed} old articles")
                st.rerun()
        
        with action_col3:
            if st.button("Clear ALL Articles", type="secondary", use_container_width=True):
                if st.session_state.get('confirm_clear_kb'):
                    articles = get_articles(limit=1000)
                    for article in articles:
                        remove_article(article.get('id'))
                    st.session_state.confirm_clear_kb = False
                    st.success("Cleared all articles")
                    st.rerun()
                else:
                    st.session_state.confirm_clear_kb = True
                    st.warning("Click again to confirm clearing ALL articles")
        
        # Facts maintenance
        st.markdown("### Facts Extraction & Maintenance")
        
        # Check for articles without facts
        try:
            articles_without_facts = get_articles_without_facts()
            num_without = len(articles_without_facts)
        except:
            articles_without_facts = []
            num_without = 0
        
        if num_without > 0:
            st.info(f"**{num_without} articles** don't have extracted facts yet")
        
        fact_col1, fact_col2, fact_col3 = st.columns(3)
        
        with fact_col1:
            # Process all articles button
            if st.button("Extract Facts from All Articles", type="primary", use_container_width=True):
                with st.spinner("Processing all articles... This may take a few minutes."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def update_progress(message, progress):
                        progress_bar.progress(progress)
                        status_text.caption(message)
                    
                    try:
                        result = process_all_articles_for_facts(
                            fetch_missing_content=True,
                            progress_callback=update_progress
                        )
                        
                        progress_bar.progress(1.0)
                        status_text.empty()
                        
                        st.success(f"""
                        **Processing Complete!**
                        - Articles processed: {result['articles_processed']}
                        - Content fetched: {result['content_fetched']}
                        - Facts extracted: {result['facts_extracted']}
                        - New facts added: {result['facts_added']}
                        """)
                        
                        if result['errors']:
                            with st.expander(f"{len(result['errors'])} errors"):
                                for err in result['errors'][:10]:
                                    st.caption(f"• {err}")
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Processing failed: {e}")
        
        with fact_col2:
            if st.button("Clear Old Facts (60+ days)", use_container_width=True):
                try:
                    removed = clear_old_facts(days=60)
                    st.success(f"Removed {removed} old facts")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with fact_col3:
            st.caption("*Facts are automatically extracted when you add articles. Use the button to process existing articles.*")
        
        st.divider()
        
        # URL Validation & Integrity
        st.markdown("### URL Validation & Integrity")
        st.caption("*Verify all article URLs are real and accessible. Remove fake/placeholder URLs.*")
        
        url_col1, url_col2, url_col3 = st.columns(3)
        
        with url_col1:
            if st.button("Validate All URLs", type="primary", use_container_width=True, key="validate_all_urls"):
                with st.spinner("Validating URLs... This may take a minute."):
                    try:
                        results = validate_all_articles(update_status=True)
                        
                        st.success(f"""
                        **Validation Complete!**
                        - Total articles: {results['total']}
                        - Valid URLs: {results['valid']}
                        - Invalid URLs: {results['invalid']}
                        - Fake/Placeholder URLs: {results['fake']}
                        """)
                        
                        if results['fake_articles']:
                            st.error(f"**{len(results['fake_articles'])} FAKE URLs DETECTED:**")
                            for fake in results['fake_articles'][:5]:
                                st.markdown(f"• **{fake['title'][:50]}...** - `{fake['url'][:50]}...`")
                            if len(results['fake_articles']) > 5:
                                st.caption(f"...and {len(results['fake_articles']) - 5} more")
                        
                        if results['invalid_articles']:
                            with st.expander(f"{len(results['invalid_articles'])} Invalid URLs (may be temporary)"):
                                for inv in results['invalid_articles'][:10]:
                                    st.markdown(f"• **{inv['title'][:40]}...** - {inv['error']}")
                        
                    except Exception as e:
                        st.error(f"Validation failed: {e}")
        
        with url_col2:
            if st.button("Remove Fake URLs", type="secondary", use_container_width=True, key="remove_fake_urls"):
                try:
                    removed = remove_fake_articles()
                    if removed > 0:
                        st.success(f"Removed {removed} articles with fake/placeholder URLs")
                        st.rerun()
                    else:
                        st.info("No fake URLs found")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with url_col3:
            st.caption("*Fake URLs include: example.com, placeholder, dummy, test.com, etc.*")
        
        st.divider()
        
        # Article Usage Tracking
        st.markdown("### Article Usage Tracking")
        st.caption("*See which articles have been used in newsletters*")
        
        try:
            most_used = get_most_used_articles(limit=5)
            used_articles = [a for a in most_used if a.get('used_count', 0) > 0]
            
            if used_articles:
                for article in used_articles:
                    usage_col1, usage_col2 = st.columns([4, 1])
                    with usage_col1:
                        st.markdown(f"**{article.get('title', 'Untitled')[:60]}...**")
                        st.caption(f"Source: {article.get('source', 'Unknown')}")
                    with usage_col2:
                        st.metric("Used", article.get('used_count', 0))
                    
                    # Show usage history if available
                    history = article.get('usage_history', [])
                    if history:
                        with st.expander(f"Usage history ({len(history)} times)"):
                            for use in history[-5:]:  # Last 5 uses
                                st.caption(f"• {use.get('newsletter_headline', 'Unknown')} ({use.get('usage_type', 'unknown')}) - {use.get('date', '')[:10]}")
            else:
                st.info("No articles have been used in newsletters yet. Usage is tracked when you generate newsletters.")
        except Exception as e:
            st.caption(f"Usage tracking not available: {e}")
        
        st.divider()
        
        # How it works
        st.markdown("### How Knowledge Base Works")
        st.markdown("""
        The **Knowledge Base** provides factual context for newsletter generation:
        
        1. **Add articles** from URLs, PDFs, or manual entry
        2. **Automatic Fact Extraction:** AI extracts statistics, quotes, and key claims
        3. When generating newsletters, the system:
           - Matches relevant facts to your topic
           - Injects citable facts with ready-to-use links
           - Tracks which facts have been used
        4. The AI uses these for:
           - Accurate facts and statistics with citations
           - Source links for verification
           - Current news and trends
        3. The KB is **separate from your style model** - it provides WHAT to write about, not HOW to write
        
        **Best Practices:**
        - Add recent articles (last 2-7 days) for timely newsletters
        - Include diverse sources for balanced coverage
        - Add PDFs of reports/research for deep-dive topics
        - Remove old articles periodically to keep context relevant
        """)


# ============================================================================
# Tab 4: Settings / Data
# ============================================================================

def render_settings_tab():
    """Render the Settings / Data tab - includes Newsletter Bible, data management, and fine-tuning."""
    st.header("Settings & Data")
    
    # ===========================================================================
    # NEWSLETTER BIBLE SECTION (moved from separate tab)
    # ===========================================================================
    render_bible_section()
    
    st.divider()
    
    # ===========================================================================
    # DATA FILES SECTION
    # ===========================================================================
    st.subheader("📁 Data Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Raw Newsletter Data:**")
        st.code(str(RAW_DATA_FILE))
        if RAW_DATA_FILE.exists():
            st.success("✓ File exists")
            # Count entries
            with open(RAW_DATA_FILE, 'r') as f:
                count = sum(1 for line in f if line.strip())
            st.markdown(f"Contains **{count}** newsletters")
        else:
            st.warning("✗ File not found - run the scraper")
    
    with col2:
        st.markdown("**Performance Stats:**")
        st.code(str(STATS_FILE))
        if STATS_FILE.exists():
            st.success("✓ File exists")
            df = pd.read_csv(STATS_FILE)
            st.markdown(f"Contains **{len(df)}** entries")
        else:
            st.warning("✗ File not found")
            st.markdown("Create a CSV with columns:")
            st.code("title,date,views,open_rate,url")
    
    st.divider()
    
    # Instructions
    st.subheader("How to Update Data")
    
    st.markdown("""
    **To update performance stats:**
    1. Go to your Substack dashboard
    2. Navigate to Stats > Posts
    3. Export or manually note: title, date, views, open rate
    4. Add/update entries in `data/newsletters_with_stats.csv`
    5. Click 'Refresh Data' below
    
    **CSV Format Example:**
    ```csv
    title,date,views,open_rate,url
    "AI Lessons for 2025","2025-12-19",1200,0.22,"https://developai.substack.com/p/..."
    "EU AI Act Update","2025-11-19",1160,0.24,"https://developai.substack.com/p/..."
    ```
    
    Note: `open_rate` should be a decimal (0.22 = 22%)
    """)
    
    st.divider()
    
    # Actions
    st.subheader("Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Refresh Data", use_container_width=True):
            refresh_data()
            st.success("Data cache cleared!")
            st.rerun()
    
    with col2:
        if st.button("Re-scrape Archive", use_container_width=True):
            with st.spinner("Scraping Substack archive..."):
                posts = run_scraper(fetch_content=True)
                if posts:
                    st.success(f"Scraped {len(posts)} posts!")
                    refresh_data()
                else:
                    st.error("No posts scraped. Check console for errors.")
    
    with col3:
        connected, msg = check_api_connection()
        if st.button("Test API Connection", use_container_width=True):
            if connected:
                st.success(msg)
            else:
                st.error(msg)
    
    st.divider()
    
    # API Status
    st.subheader("OpenAI API Status")
    
    connected, msg = check_api_connection()
    if connected:
        st.success(f"✓ {msg}")
    else:
        st.error(f"✗ {msg}")
        st.markdown("""
        To set up the API:
        1. Copy `.env.example` to `.env`
        2. Add your OpenAI API key
        3. Restart the app
        """)
    
    # Config file info
    st.divider()
    st.subheader("Configuration")
    
    config_file = Path(__file__).parent / "config" / "topics_keywords.yml"
    st.markdown(f"**Topics & Keywords Config:** `{config_file}`")
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            st.code(f.read()[:1000] + "...", language='yaml')
    
    st.markdown("Edit this file to customize topic detection and keyword lists.")
    
    # ===========================================================================
    # NEWSLETTER ENGINE SECTION - Self-improving AI
    # ===========================================================================
    st.divider()
    st.subheader("🚀 Newsletter Engine (Self-Improving AI)")
    
    if NEWSLETTER_ENGINE_AVAILABLE:
        engine = NewsletterEngine()
        status = engine.get_status()
        
        # Component Status
        st.markdown("**System Components:**")
        col_e1, col_e2, col_e3, col_e4 = st.columns(4)
        
        with col_e1:
            if status['embeddings']['sentence_transformers']:
                st.success("✅ Local Embeddings")
                st.caption("FREE semantic search")
            else:
                st.warning("⚠️ Embeddings")
                st.caption("Using OpenAI API")
        
        with col_e2:
            if status['rag']['available']:
                st.success("✅ RAG System")
                st.caption("Past examples")
            else:
                st.error("❌ RAG")
        
        with col_e3:
            if status['knowledge_base']['available']:
                st.success("✅ Knowledge Base")
                st.caption("Facts & articles")
            else:
                st.warning("⚠️ KB")
        
        with col_e4:
            if status['fine_tuning']['model']:
                st.success("✅ Fine-tuned")
                st.caption(status['fine_tuning']['model'][:20] + "...")
            else:
                st.info("ℹ️ Base GPT-4o")
        
        # Learning Progress
        st.markdown("---")
        st.markdown("**📈 Learning Progress:**")
        
        learning = status['learning']
        if 'message' in learning:
            st.info(f"🎓 {learning['message']} - The system learns from your edits to improve over time.")
            st.caption("After generating a newsletter, edit it, then use 'Track Edit' to teach the system.")
        else:
            col_l1, col_l2, col_l3, col_l4 = st.columns(4)
            
            with col_l1:
                st.metric("Edits Tracked", learning.get('total_edits_tracked', 0))
            
            with col_l2:
                st.metric("Avoid Patterns", learning.get('avoid_patterns_learned', 0))
            
            with col_l3:
                st.metric("Include Patterns", learning.get('include_patterns_learned', 0))
            
            with col_l4:
                improvement = learning.get('improvement_percentage', 0)
                if improvement > 0:
                    st.metric("Improvement", f"{improvement:.1f}%", delta=f"+{improvement:.1f}%")
                else:
                    st.metric("Improvement", "Measuring...")
            
            # Show learned patterns
            with st.expander("View Learned Patterns", expanded=False):
                learnings_data = engine.learning_loop.learnings
                
                avoid = learnings_data.get('avoid_patterns', [])
                if avoid:
                    st.markdown("**❌ Things to AVOID (from your edits):**")
                    for pattern in avoid[:5]:
                        st.markdown(f"- {pattern.get('pattern', '')}")
                
                include = learnings_data.get('include_patterns', [])
                if include:
                    st.markdown("**✅ Things to INCLUDE (from your edits):**")
                    for pattern in include[:5]:
                        st.markdown(f"- {pattern.get('instruction', '')}")
        
        # Auto-Learning Info
        st.markdown("---")
        st.markdown("**🎓 Automatic Learning:**")
        st.success("✅ **Learning is automatic!** When you edit a generated newsletter in the Write tab and click 'Save Edits', the AI automatically learns from your changes.")
        st.caption("The system extracts patterns from what you add, remove, and change - then applies those learnings to future generations.")
        
        # Quick Generate with Engine
        st.markdown("---")
        st.markdown("**⚡ Quick Generate with Engine:**")
        
        with st.expander("Quick Generation", expanded=False):
            quick_outline = st.text_area(
                "Enter your outline:",
                height=200,
                key="engine_quick_outline",
                placeholder="""# Newsletter Title

## Opening
- Hook about...
- What this means...

## Main Section
- Key point 1
- Key point 2

## Closing
- Call to action
"""
            )
            
            col_gen1, col_gen2 = st.columns(2)
            with col_gen1:
                target_words = st.slider("Target words:", 400, 1500, 800, 50, key="engine_target_words")
            with col_gen2:
                use_ft = st.checkbox("Use fine-tuned model", value=False, key="engine_use_ft")
            
            if st.button("Generate with Engine", type="primary", key="engine_generate_btn"):
                if quick_outline:
                    with st.spinner("Generating with intelligent prompt construction..."):
                        result = engine.generate(
                            outline=quick_outline,
                            target_length=target_words,
                            use_fine_tuned=use_ft
                        )
                    
                    st.success(f"✅ Generated {result.metadata['output_words']} words")
                    
                    # Show metadata
                    with st.expander("Generation Details", expanded=False):
                        st.json({
                            'model': result.model,
                            'facts_used': result.prompt_components.get('facts_count', 0),
                            'rag_examples': result.prompt_components.get('rag_examples_count', 0),
                            'learnings_applied': result.prompt_components.get('learnings_applied', 0),
                            'tokens': result.metadata.get('total_tokens', 0),
                        })
                    
                    # Show content
                    st.markdown("### Generated Content:")
                    st.markdown(result.content)
                    
                    # Store for potential edit tracking
                    st.session_state.engine_last_generation = result
                    st.session_state.engine_last_content = result.content
                    
                    st.info(f"💡 Generation ID: `{result.id}` - Edit this content, then use 'Track Edit' above to teach the AI!")
                else:
                    st.warning("Please enter an outline first.")
    
    else:
        st.warning("Newsletter Engine not available. Check that `newsletter_engine.py` exists.")
        st.code("pip install sentence-transformers", language="bash")
    
    # Quick links to other tabs
    st.divider()
    st.info("**Training & Fine-Tuning** has moved to its own tab! Go to the **Training** tab for AI learning, fine-tuning, and model management.")
    st.info("**Knowledge Base** has its own tab! Go to the **Knowledge Base** tab to add articles, upload PDFs, and manage your content sources.")


# ============================================================================
# Tab 6: Training
# ============================================================================

def render_newsletter_bible_tab():
    """Render the Newsletter Bible tab - view and edit your writing style guide."""
    st.subheader("Newsletter Bible")
    st.markdown("*Your complete writing style guide - everything that makes your newsletters unique*")
    
    bible = load_bible()
    
    if not bible:
        st.error("Newsletter Bible not found. Run the style analyzer to generate it.")
        if st.button("Generate Newsletter Bible", type="primary"):
            st.info("Go to Settings > Analyze Style to generate your Bible from past newsletters.")
        return
    
    # Stats bar
    meta = bible.get('meta', {})
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Newsletters Analyzed", meta.get('newsletters_analyzed', 0))
    with col2:
        st.metric("Source", meta.get('generated_from', 'Unknown'))
    with col3:
        st.metric("Author", meta.get('author', 'Unknown'))
    
    st.divider()
    
    # =========================================================================
    # SECTION 1: Writing Voice
    # =========================================================================
    with st.expander("📝 Writing Voice", expanded=True):
        writing_voice = bible.get('writing_voice', {})
        
        # Signature Phrases
        st.markdown("### Signature Phrases")
        st.markdown("*Phrases that define your unique voice*")
        signature_phrases = writing_voice.get('signature_phrases', [])
        if signature_phrases:
            for i, phrase in enumerate(signature_phrases):
                st.markdown(f"- \"{phrase}\"")
        else:
            st.info("No signature phrases found yet.")
        
        # Add new phrase
        new_phrase = st.text_input("Add a signature phrase:", key="new_sig_phrase")
        if st.button("Add Phrase", key="add_sig_phrase"):
            if new_phrase:
                add_to_bible('writing_voice.signature_phrases', new_phrase)
                st.success(f"Added: \"{new_phrase}\"")
                st.rerun()
        
        st.divider()
        
        # Tone Markers
        st.markdown("### Tone Markers")
        tone_markers = writing_voice.get('tone_markers', [])
        if tone_markers:
            st.markdown(", ".join(tone_markers))
        
        # First Person Usage
        st.markdown("### First Person Usage")
        first_person = writing_voice.get('first_person_usage', {})
        if first_person:
            st.markdown(f"- Frequency: {first_person.get('frequency', 'N/A')}")
            st.markdown(f"- Style: {first_person.get('style', 'N/A')}")
    
    # =========================================================================
    # SECTION 2: Headline Formulas
    # =========================================================================
    with st.expander("📰 Headline Formulas", expanded=False):
        headlines = bible.get('headline_formulas', {})
        
        st.markdown(f"**Optimal Length:** {headlines.get('optimal_length', 'N/A')}")
        
        # Pattern breakdown
        patterns = headlines.get('pattern_breakdown', {})
        if patterns:
            st.markdown("### Headline Patterns")
            for pattern_name, data in patterns.items():
                count = data.get('count', 0)
                pct = data.get('percentage', 0)
                examples = data.get('examples', [])
                
                st.markdown(f"**{pattern_name.replace('_', ' ').title()}** ({count} headlines, {pct:.1f}%)")
                for ex in examples[:3]:
                    st.markdown(f"- \"{ex}\"")
        
        # Opening words
        opening_words = headlines.get('opening_words_that_work', {})
        if opening_words:
            st.markdown("### Opening Words That Work")
            top_words = sorted(opening_words.items(), key=lambda x: x[1], reverse=True)[:10]
            st.markdown(", ".join([f"**{w}** ({c})" for w, c in top_words]))
    
    # =========================================================================
    # SECTION 3: Structure Patterns
    # =========================================================================
    with st.expander("🏗️ Structure Patterns", expanded=False):
        structure = bible.get('structure_patterns', {})
        
        if structure:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Avg Word Count:** {structure.get('avg_word_count', 'N/A')}")
                st.markdown(f"**Common Sections:** {structure.get('common_sections', 'N/A')}")
            with col2:
                st.markdown(f"**Opening Style:** {structure.get('opening_style', 'N/A')}")
                st.markdown(f"**Closing Style:** {structure.get('closing_style', 'N/A')}")
            
            para_lengths = structure.get('paragraph_lengths', {})
            if para_lengths:
                st.markdown("**Paragraph Lengths:**")
                st.json(para_lengths)
    
    # =========================================================================
    # SECTION 4: Rules for Success
    # =========================================================================
    with st.expander("✅ Rules for Success", expanded=True):
        rules = bible.get('rules_for_success', [])
        
        if rules:
            for rule in rules:
                st.markdown(f"- {rule}")
        else:
            st.info("No rules defined yet.")
        
        # Add new rule
        new_rule = st.text_input("Add a new rule:", key="new_rule")
        if st.button("Add Rule", key="add_rule"):
            if new_rule:
                add_to_bible('rules_for_success', new_rule)
                st.success(f"Added rule: \"{new_rule}\"")
                st.rerun()
    
    # =========================================================================
    # SECTION 5: Cliches to Avoid
    # =========================================================================
    with st.expander("🚫 Cliches to Avoid", expanded=True):
        cliches = bible.get('cliches_to_avoid', [])
        
        if cliches:
            # Display in columns
            cols = st.columns(3)
            for i, cliche in enumerate(cliches):
                with cols[i % 3]:
                    st.markdown(f"- \"{cliche}\"")
        else:
            st.info("No cliches defined yet.")
        
        # Add new cliche
        new_cliche = st.text_input("Add a cliche to avoid:", key="new_cliche")
        if st.button("Add Cliche", key="add_cliche"):
            if new_cliche:
                add_to_bible('cliches_to_avoid', new_cliche)
                st.success(f"Added cliche to avoid: \"{new_cliche}\"")
                st.rerun()
    
    # =========================================================================
    # SECTION 6: Sample Openings
    # =========================================================================
    with st.expander("🎬 Sample Openings", expanded=False):
        openings = bible.get('sample_openings', [])
        
        if openings:
            for i, opening in enumerate(openings[:10], 1):
                st.markdown(f"**Opening {i}:**")
                st.markdown(f"> {opening[:300]}..." if len(opening) > 300 else f"> {opening}")
                st.divider()
        else:
            st.info("No sample openings found.")
    
    # =========================================================================
    # SECTION 7: Recent Headlines (from published newsletters)
    # =========================================================================
    with st.expander("📰 Recent Headlines (from your published newsletters)", expanded=False):
        recent_headlines = bible.get('headline_formulas', {}).get('recent_headlines', [])
        
        if recent_headlines:
            for headline in recent_headlines[:10]:
                st.markdown(f"- {headline}")
        else:
            st.info("No recent headlines yet. Publish newsletters to add them here.")
    
    # =========================================================================
    # SECTION 8: Learnings from Edits (auto-captured)
    # =========================================================================
    with st.expander("🧠 Learnings from Your Edits", expanded=True):
        learnings = bible.get('learnings_from_edits', {})
        
        if learnings:
            st.markdown("*These patterns were automatically learned from your edits to AI-generated content*")
            
            # Stats
            total_edits = learnings.get('total_edits_recorded', 0)
            last_edit = learnings.get('last_edit', '')[:10] if learnings.get('last_edit') else 'Never'
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Edits Recorded", total_edits)
            with col2:
                st.metric("Last Edit", last_edit)
            
            st.divider()
            
            # Headline preferences
            headline_prefs = learnings.get('headline_preferences', [])
            if headline_prefs:
                st.markdown("### Headline Preferences")
                st.markdown("*Headlines you wrote instead of using AI suggestions:*")
                for pref in headline_prefs[-5:]:
                    st.markdown(f"- **You wrote:** \"{pref.get('preferred', '')}\"")
                    rejected = pref.get('rejected', [])
                    if rejected:
                        st.caption(f"  Rejected: {', '.join(rejected[:2])}...")
            
            # Frequently added content
            freq_added = learnings.get('frequently_added_content', [])
            if freq_added:
                st.markdown("### Content You Frequently Add")
                st.markdown("*Bullets/content you often add that the AI missed:*")
                for item in freq_added[:10]:
                    st.markdown(f"- \"{item.get('content', '')}\" (added {item.get('times_added', 0)}x)")
            
            # Tone adjustments
            tone_adj = learnings.get('tone_adjustments', [])
            if tone_adj:
                st.markdown("### Tone Adjustments")
                st.markdown("*How you typically adjust the AI's tone:*")
                for adj in tone_adj[-5:]:
                    st.markdown(f"- \"{adj}\"")
            
            # Edit type frequency
            edit_types = learnings.get('edit_type_frequency', {})
            if edit_types:
                st.markdown("### Edit Patterns")
                st.markdown("*What types of edits you make most:*")
                sorted_types = sorted(edit_types.items(), key=lambda x: x[1], reverse=True)
                for edit_type, count in sorted_types[:5]:
                    st.markdown(f"- **{edit_type.replace('_', ' ').title()}:** {count} times")
        else:
            st.info("No learnings captured yet. Edit AI-generated outlines and publish newsletters to build your learning history.")
            
            # Button to sync learnings now
            if st.button("Sync Learnings Now", key="sync_learnings"):
                try:
                    from pathlib import Path
                    bible_path = Path(__file__).parent / "data" / "newsletter_bible.json"
                    with open(bible_path, 'r', encoding='utf-8') as f:
                        current_bible = json.load(f)
                    sync_learnings_to_bible(current_bible)
                    with open(bible_path, 'w', encoding='utf-8') as f:
                        json.dump(current_bible, f, indent=2, ensure_ascii=False)
                    st.success("Learnings synced to Bible!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error syncing: {e}")
    
    # =========================================================================
    # SECTION 9: Raw JSON View
    # =========================================================================
    with st.expander("🔧 Raw Bible (JSON)", expanded=False):
        st.json(bible)
    
    st.divider()
    
    # Actions
    st.markdown("### Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Regenerate Bible", help="Re-analyze all newsletters to update the Bible"):
            st.info("Go to Settings > Analyze Style to regenerate the Bible.")
    
    with col2:
        # Download Bible
        bible_json = json.dumps(bible, indent=2)
        st.download_button(
            "Download Bible (JSON)",
            data=bible_json,
            file_name="newsletter_bible.json",
            mime="application/json"
        )
    
    with col3:
        if st.button("Clear Custom Additions", type="secondary"):
            st.warning("This would clear manually added rules, phrases, and cliches. Not implemented yet.")


def render_deep_style_analysis_tab():
    """Render the Deep Style Analysis tab - advanced linguistic analysis of your writing."""
    st.subheader("Deep Style Analysis")
    st.markdown("*Advanced linguistic fingerprinting using NLP libraries for more accurate style imitation*")
    
    if not DEEP_ANALYZER_AVAILABLE:
        st.warning("Deep Style Analyzer module not available. Please check imports.")
        return
    
    # Show library status
    st.markdown("#### Required Libraries")
    
    lib_col1, lib_col2, lib_col3, lib_col4 = st.columns(4)
    
    with lib_col1:
        if TEXTSTAT_AVAILABLE:
            st.success("✅ textstat")
        else:
            st.error("❌ textstat")
            st.caption("`pip install textstat`")
    
    with lib_col2:
        if SPACY_AVAILABLE:
            st.success("✅ spaCy")
        else:
            st.error("❌ spaCy")
            st.caption("`pip install spacy`")
            st.caption("`python -m spacy download en_core_web_sm`")
    
    with lib_col3:
        if TEXTBLOB_AVAILABLE:
            st.success("✅ TextBlob")
        else:
            st.error("❌ TextBlob")
            st.caption("`pip install textblob`")
    
    with lib_col4:
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            st.success("✅ sentence-transformers")
        else:
            st.info("⚪ sentence-transformers")
            st.caption("Optional for embeddings")
    
    st.divider()
    
    # Run analysis button
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("🔬 Run Deep Analysis", type="primary", use_container_width=True):
            newsletters = load_all_newsletters()
            if newsletters:
                with st.spinner("Running deep linguistic analysis... This may take 30-60 seconds."):
                    try:
                        result = run_deep_analysis(newsletters)
                        st.session_state['deep_analysis_result'] = result
                        st.success(f"✅ Analysis complete! Analyzed {len(newsletters)} newsletters.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
            else:
                st.error("No newsletters found. Scrape your Substack first in Settings.")
    
    with col2:
        st.markdown("""
        **What this analyzes:**
        - Vocabulary patterns (richness, signature words)
        - Sentence structure (length, variety, questions)
        - Paragraph flow and transitions
        - Punctuation habits (dashes, contractions)
        - Personal voice (I statements, reader address)
        - Readability metrics (Flesch-Kincaid, etc.)
        - Sentiment and subjectivity patterns
        """)
    
    st.divider()
    
    # Display existing analysis
    deep_bible = load_deep_bible()
    
    if not deep_bible:
        st.info("No deep analysis found. Click 'Run Deep Analysis' above to generate one.")
        return
    
    # Meta info
    meta = deep_bible.get('meta', {})
    newsletters_count = meta.get('newsletters_analyzed', meta.get('total_texts_analyzed', 0))
    custom_count = meta.get('custom_samples_analyzed', 0)
    total_texts = meta.get('total_texts_analyzed', newsletters_count)
    
    st.markdown(f"""
    **Last analyzed:** {meta.get('analysis_date', 'Unknown')[:10] if meta.get('analysis_date') else 'Unknown'}  
    **Total texts analyzed:** {total_texts} ({newsletters_count} newsletters{f' + {custom_count} custom samples' if custom_count > 0 else ''})  
    **Total characters:** {meta.get('total_characters', 0):,}
    """)
    
    # Display each analysis section
    
    # 1. Vocabulary Analysis
    with st.expander("📚 Vocabulary Analysis", expanded=True):
        vocab = deep_bible.get('vocabulary', {})
        if vocab:
            v_col1, v_col2, v_col3 = st.columns(3)
            with v_col1:
                st.metric("Vocabulary Richness", f"{vocab.get('type_token_ratio', 0):.2%}")
                st.caption("Higher = more varied word choice")
            with v_col2:
                st.metric("Avg Word Length", f"{vocab.get('average_word_length', 0)} chars")
            with v_col3:
                st.metric("Unique Words", f"{vocab.get('unique_words', 0):,}")
            
            st.markdown("**Your Signature Words:**")
            sig_words = vocab.get('signature_words', [])
            if sig_words:
                st.markdown(" | ".join([f"`{w}`" for w in sig_words[:15]]))
            
            st.markdown("**Most Frequent Content Words:**")
            freq_words = vocab.get('most_frequent_content_words', {})
            if freq_words:
                word_items = list(freq_words.items())[:20]
                st.markdown(" | ".join([f"`{w}` ({c})" for w, c in word_items]))
    
    # 2. Sentence Analysis
    with st.expander("📝 Sentence Structure", expanded=True):
        sent = deep_bible.get('sentences', {})
        if sent:
            s_col1, s_col2, s_col3, s_col4 = st.columns(4)
            with s_col1:
                st.metric("Avg Sentence Length", f"{sent.get('average_sentence_length', 0):.0f} words")
            with s_col2:
                st.metric("Length Variation", f"±{sent.get('sentence_length_std_dev', 0):.0f}")
            with s_col3:
                st.metric("Questions", f"{sent.get('question_frequency', 0):.1f}%")
            with s_col4:
                st.metric("Short Sentences", f"{sent.get('short_sentence_frequency', 0):.1f}%")
            
            st.markdown("**Sample Questions You Ask:**")
            questions = sent.get('sample_questions', [])
            for q in questions[:5]:
                st.markdown(f"- *\"{q[:100]}...\"*" if len(q) > 100 else f"- *\"{q}\"*")
            
            st.markdown("**Sample Short Punchy Sentences:**")
            short = sent.get('sample_short_sentences', [])
            for s in short[:5]:
                st.markdown(f"- *\"{s}\"*")
    
    # 3. Paragraph Analysis
    with st.expander("📄 Paragraph Patterns"):
        para = deep_bible.get('paragraphs', {})
        if para:
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                st.metric("Avg Paragraph Length", f"{para.get('average_paragraph_length', 0):.0f} words")
            with p_col2:
                rng = para.get('paragraph_length_range', {})
                st.metric("Paragraph Range", f"{rng.get('min', 0)}-{rng.get('max', 0)} words")
            
            st.markdown("**Common Paragraph Starters:**")
            starters = para.get('common_paragraph_starters', {})
            if starters:
                starter_items = list(starters.items())[:10]
                st.markdown(" | ".join([f"`{s}` ({c})" for s, c in starter_items]))
            
            st.markdown("**Sample First Sentences:**")
            firsts = para.get('sample_first_sentences', [])
            for f in firsts[:5]:
                st.markdown(f"- *\"{f[:80]}...\"*" if len(f) > 80 else f"- *\"{f}\"*")
    
    # 4. Punctuation Analysis
    with st.expander("✏️ Punctuation Habits"):
        punct = deep_bible.get('punctuation', {})
        if punct:
            pu_col1, pu_col2, pu_col3, pu_col4 = st.columns(4)
            with pu_col1:
                st.metric("Dashes", f"{punct.get('dash_frequency', 0):.1f}/1000 words")
            with pu_col2:
                st.metric("Colons", f"{punct.get('colon_frequency', 0):.1f}/1000 words")
            with pu_col3:
                st.metric("Parentheses", f"{punct.get('parentheses_frequency', 0):.1f}/1000 words")
            with pu_col4:
                st.metric("Contractions", f"{punct.get('contraction_frequency', 0):.1f}%")
            
            st.markdown("**Common Contractions:**")
            contr = punct.get('common_contractions', {})
            if contr:
                contr_items = list(contr.items())[:10]
                st.markdown(" | ".join([f"`{c}` ({n})" for c, n in contr_items]))
    
    # 5. Personal Voice
    with st.expander("🎤 Personal Voice", expanded=True):
        voice = deep_bible.get('personal_voice', {})
        if voice:
            vo_col1, vo_col2, vo_col3 = st.columns(3)
            with vo_col1:
                st.metric("First Person (I/me/my)", f"{voice.get('first_person_singular_frequency', 0):.2f}%")
            with vo_col2:
                st.metric("First Person (we/us/our)", f"{voice.get('first_person_plural_frequency', 0):.2f}%")
            with vo_col3:
                st.metric("Second Person (you/your)", f"{voice.get('second_person_frequency', 0):.2f}%")
            
            st.markdown("**Common 'I' Statement Patterns:**")
            i_statements = voice.get('common_i_statements', {})
            if i_statements:
                i_items = list(i_statements.items())[:10]
                st.markdown(" | ".join([f"`{s}` ({c})" for s, c in i_items]))
            
            st.markdown("**Questions Directed at Reader:**")
            reader_q = voice.get('sample_reader_questions', [])
            for q in reader_q[:5]:
                st.markdown(f"- *\"{q[:100]}...\"*" if len(q) > 100 else f"- *\"{q}\"*")
    
    # 6. Readability
    with st.expander("📊 Readability Metrics"):
        read = deep_bible.get('readability', {})
        if read and 'error' not in read:
            r_col1, r_col2, r_col3 = st.columns(3)
            with r_col1:
                st.metric("Flesch Reading Ease", f"{read.get('flesch_reading_ease', 0):.1f}")
                st.caption("Higher = easier to read")
            with r_col2:
                st.metric("Flesch-Kincaid Grade", f"{read.get('flesch_kincaid_grade', 0):.1f}")
                st.caption("US school grade level")
            with r_col3:
                st.metric("Text Standard", read.get('text_standard', 'N/A'))
            
            r_col4, r_col5, r_col6 = st.columns(3)
            with r_col4:
                st.metric("Gunning Fog", f"{read.get('gunning_fog_index', 0):.1f}")
            with r_col5:
                st.metric("Coleman-Liau", f"{read.get('coleman_liau_index', 0):.1f}")
            with r_col6:
                st.metric("Reading Time", f"{read.get('reading_time_minutes', 0):.1f} min avg")
        else:
            st.info("Install textstat for readability metrics: `pip install textstat`")
    
    # 7. Sentiment
    with st.expander("💭 Sentiment & Tone"):
        sentiment = deep_bible.get('sentiment', {})
        if sentiment and 'error' not in sentiment:
            se_col1, se_col2 = st.columns(2)
            with se_col1:
                st.metric("Overall Tone", sentiment.get('sentiment_interpretation', 'unknown').title())
                st.caption(f"Polarity: {sentiment.get('average_polarity', 0):.2f} (-1 to +1)")
            with se_col2:
                st.metric("Style", sentiment.get('subjectivity_interpretation', 'unknown').title())
                st.caption(f"Subjectivity: {sentiment.get('average_subjectivity', 0):.2f} (0-1)")
        else:
            st.info("Install textblob for sentiment analysis: `pip install textblob`")
    
    # 8. Signature Patterns
    with st.expander("🔑 Signature Phrases & Patterns", expanded=True):
        patterns = deep_bible.get('signature_patterns', {})
        if patterns:
            st.markdown("**Your Signature Two-Word Phrases:**")
            bigrams = patterns.get('signature_bigrams', {})
            if bigrams:
                bigram_items = list(bigrams.items())[:15]
                st.markdown(" | ".join([f"`{b}` ({c})" for b, c in bigram_items]))
            
            st.markdown("**Your Signature Three-Word Phrases:**")
            trigrams = patterns.get('signature_trigrams', {})
            if trigrams:
                trigram_items = list(trigrams.items())[:10]
                st.markdown(" | ".join([f"`{t}` ({c})" for t, c in trigram_items]))
    
    # 9. Linguistic Features (if spaCy available)
    with st.expander("🔤 Linguistic Features (spaCy)"):
        ling = deep_bible.get('linguistics', {})
        if ling and 'error' not in ling:
            li_col1, li_col2, li_col3, li_col4 = st.columns(4)
            with li_col1:
                st.metric("Noun %", f"{ling.get('noun_frequency', 0):.1f}%")
            with li_col2:
                st.metric("Verb %", f"{ling.get('verb_frequency', 0):.1f}%")
            with li_col3:
                st.metric("Adjective %", f"{ling.get('adjective_frequency', 0):.1f}%")
            with li_col4:
                st.metric("Adverb %", f"{ling.get('adverb_frequency', 0):.1f}%")
            
            st.markdown("**Named Entity Types Found:**")
            entities = ling.get('named_entity_types', {})
            if entities:
                ent_items = list(entities.items())[:10]
                st.markdown(" | ".join([f"`{e}` ({c})" for e, c in ent_items]))
        else:
            st.info("Install spaCy for linguistic analysis: `pip install spacy && python -m spacy download en_core_web_sm`")
    
    st.divider()
    
    # =========================================================================
    # ADD CUSTOM WRITING SAMPLES
    # =========================================================================
    
    st.markdown("### ➕ Add More Writing Samples")
    st.markdown("*Add articles, blog posts, or other writing you've done to improve the style analysis*")
    
    # Show existing custom samples
    custom_samples = load_custom_writing_samples() if DEEP_ANALYZER_AVAILABLE else []
    if custom_samples:
        st.success(f"**{len(custom_samples)} custom writing samples** already added")
        with st.expander("View Custom Samples"):
            for i, sample in enumerate(custom_samples):
                text = sample.get('text', '') if isinstance(sample, dict) else sample
                source = sample.get('source', 'manual') if isinstance(sample, dict) else 'manual'
                added = sample.get('added_at', 'Unknown')[:10] if isinstance(sample, dict) else 'Unknown'
                st.markdown(f"**Sample {i+1}** ({source}) - Added {added}")
                st.text_area(f"sample_{i}", text[:500] + "..." if len(text) > 500 else text, 
                           height=100, disabled=True, key=f"view_sample_{i}")
            
            if st.button("🗑️ Clear All Custom Samples", type="secondary"):
                clear_custom_writing_samples()
                st.success("Custom samples cleared!")
                st.rerun()
    
    # Add new sample
    new_sample = st.text_area(
        "Paste your writing sample here:",
        height=200,
        placeholder="Paste an article, blog post, or any writing you've done that represents your style. Minimum 100 characters.",
        key="new_custom_sample"
    )
    
    sample_source = st.text_input("Source (optional):", placeholder="e.g., 'Blog post about AI', 'LinkedIn article'", key="sample_source")
    
    if st.button("➕ Add Writing Sample", type="primary"):
        if new_sample and len(new_sample.strip()) >= 100:
            if save_custom_writing_sample(new_sample, sample_source or "manual"):
                st.success("✅ Writing sample added! Click 'Run Deep Analysis' to include it.")
                st.rerun()
            else:
                st.error("Failed to save sample")
        else:
            st.warning("Please enter at least 100 characters of text")
    
    st.divider()
    
    # =========================================================================
    # MERGE INTO NEWSLETTER BIBLE
    # =========================================================================
    
    st.markdown("### 🔗 Merge into Newsletter Bible")
    st.markdown("*Copy the deep style insights into your main Newsletter Bible for use in generation*")
    
    merge_col1, merge_col2 = st.columns([1, 2])
    
    with merge_col1:
        if st.button("🔗 Merge Deep Analysis → Bible", type="primary", use_container_width=True):
            if DEEP_ANALYZER_AVAILABLE:
                result = merge_deep_into_bible()
                if result.get('success'):
                    st.success(f"✅ Merged! Added sections: {', '.join(result.get('sections_added', []))}")
                else:
                    st.error(f"Merge failed: {result.get('error', 'Unknown error')}")
            else:
                st.error("Deep analyzer not available")
    
    with merge_col2:
        st.markdown("""
        **What this does:**
        - Adds all deep analysis data to your Newsletter Bible
        - Updates `writing_voice` with signature words, sentence style, etc.
        - Makes insights available in the Training → Newsletter Bible tab
        """)
    
    st.divider()
    
    # Raw JSON view
    with st.expander("🔧 Raw Analysis Data"):
        st.json(deep_bible)


def add_to_bible(path: str, value: str):
    """Add a value to the Newsletter Bible at the specified path."""
    from pathlib import Path
    import json
    
    bible_path = Path(__file__).parent / "data" / "newsletter_bible.json"
    
    try:
        with open(bible_path, 'r', encoding='utf-8') as f:
            bible = json.load(f)
        
        # Navigate to the path and add the value
        parts = path.split('.')
        current = bible
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        last_part = parts[-1]
        if last_part not in current:
            current[last_part] = []
        
        if isinstance(current[last_part], list):
            if value not in current[last_part]:
                current[last_part].append(value)
        
        with open(bible_path, 'w', encoding='utf-8') as f:
            json.dump(bible, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        st.error(f"Error updating Bible: {e}")
        return False


def update_bible_from_newsletter(headline: str, content: str, opening_hook: str = ""):
    """Update the Newsletter Bible when a newsletter is successfully published."""
    from pathlib import Path
    import json
    
    bible_path = Path(__file__).parent / "data" / "newsletter_bible.json"
    
    try:
        with open(bible_path, 'r', encoding='utf-8') as f:
            bible = json.load(f)
        
        # Update meta
        if 'meta' not in bible:
            bible['meta'] = {}
        bible['meta']['newsletters_analyzed'] = bible['meta'].get('newsletters_analyzed', 0) + 1
        bible['meta']['last_updated'] = datetime.now().isoformat()
        
        # Add opening to sample_openings if it's good
        if opening_hook and len(opening_hook) > 50:
            if 'sample_openings' not in bible:
                bible['sample_openings'] = []
            # Only keep last 20 openings
            if opening_hook not in bible['sample_openings']:
                bible['sample_openings'].insert(0, opening_hook)
                bible['sample_openings'] = bible['sample_openings'][:20]
        
        # Add headline to examples
        if headline:
            if 'headline_formulas' not in bible:
                bible['headline_formulas'] = {}
            if 'recent_headlines' not in bible['headline_formulas']:
                bible['headline_formulas']['recent_headlines'] = []
            if headline not in bible['headline_formulas']['recent_headlines']:
                bible['headline_formulas']['recent_headlines'].insert(0, headline)
                bible['headline_formulas']['recent_headlines'] = bible['headline_formulas']['recent_headlines'][:20]
        
        # Sync learnings from the learning system into the Bible
        sync_learnings_to_bible(bible)
        
        with open(bible_path, 'w', encoding='utf-8') as f:
            json.dump(bible, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error updating Bible from newsletter: {e}")
        return False


def sync_learnings_to_bible(bible: dict):
    """Sync learnings from the learning system into the Bible dict."""
    from learning_system import load_learnings, load_edit_history
    
    learnings = load_learnings()
    edit_history = load_edit_history()
    
    # Add learnings section to Bible
    if 'learnings_from_edits' not in bible:
        bible['learnings_from_edits'] = {}
    
    # Headline preferences (what headlines the user prefers)
    headline_prefs = learnings.get('headline_preferences', [])
    if headline_prefs:
        bible['learnings_from_edits']['headline_preferences'] = headline_prefs[-10:]  # Last 10
    
    # Common additions (bullets/content the user frequently adds)
    common_additions = learnings.get('common_additions', [])
    if common_additions:
        # Count frequency
        from collections import Counter
        addition_counts = Counter(common_additions)
        top_additions = addition_counts.most_common(20)
        bible['learnings_from_edits']['frequently_added_content'] = [
            {'content': content, 'times_added': count} 
            for content, count in top_additions
        ]
    
    # Tone adjustments (how the user adjusts tone)
    tone_adjustments = learnings.get('tone_adjustments', [])
    if tone_adjustments:
        bible['learnings_from_edits']['tone_adjustments'] = tone_adjustments[-10:]  # Last 10
    
    # Rejected patterns (what the AI generated that the user rejected)
    rejected = learnings.get('rejected_patterns', [])
    if rejected:
        bible['learnings_from_edits']['rejected_patterns'] = rejected[-10:]
    
    # Edit history summary
    if edit_history:
        bible['learnings_from_edits']['total_edits_recorded'] = len(edit_history)
        bible['learnings_from_edits']['last_edit'] = edit_history[-1].get('timestamp', '') if edit_history else ''
        
        # Count types of edits
        edit_types = {}
        for edit in edit_history[-50:]:  # Last 50 edits
            for change in edit.get('changes', []):
                change_type = change.get('type', 'unknown')
                edit_types[change_type] = edit_types.get(change_type, 0) + 1
        bible['learnings_from_edits']['edit_type_frequency'] = edit_types


def render_training_tab():
    """Render the Training tab - manage what's fed into the AI model."""
    st.header("Training & Model Management")
    st.markdown("*See exactly what's being fed into your AI model and manage training*")
    
    # Sub-tabs for different training areas
    train_tab1, train_tab2, train_tab3, train_tab4, train_tab5, train_tab6, train_tab7 = st.tabs([
        "Newsletter Bible",
        "Deep Style Analysis",
        "What's Fed to the Model",
        "Fine-Tuning",
        "AI Learning",
        "Published Newsletters",
        "Performance Learnings"
    ])
    
    with train_tab1:
        render_newsletter_bible_tab()
    
    with train_tab2:
        render_deep_style_analysis_tab()
    
    with train_tab3:
        render_model_inputs_section()
    
    with train_tab4:
        render_fine_tuning_section()
    
    with train_tab5:
        render_ai_learning_section()
    
    with train_tab6:
        render_published_newsletters_section()
    
    with train_tab7:
        render_performance_learnings_section()


def render_model_inputs_section():
    """Show exactly what context is being fed to the model during generation."""
    st.subheader("What's Being Fed to the Model")
    st.markdown("*A transparent view of all the context used when generating newsletters*")
    
    # Overview cards
    col1, col2, col3, col4 = st.columns(4)
    
    # Count each source
    bible = load_bible()
    kb_stats = get_kb_stats() if HAS_KNOWLEDGE_BASE else {'total_articles': 0}
    edit_stats = get_edit_stats()
    learnings = get_performance_learnings()
    
    with col1:
        bible_status = "Loaded" if bible else "Not found"
        st.metric("Newsletter Bible", bible_status)
    with col2:
        st.metric("Knowledge Base", f"{kb_stats.get('total_articles', 0)} articles")
    with col3:
        st.metric("Edit History", f"{edit_stats.get('total_edits', 0)} edits")
    with col4:
        has_learnings = "Active" if learnings else "None yet"
        st.metric("Performance Learnings", has_learnings)
    
    st.divider()
    
    st.markdown("### Context Sources Breakdown")
    st.markdown("*Each of these contributes to how the AI writes your newsletters:*")
    
    # 1. Newsletter Bible / Style Guide
    with st.expander("1. Newsletter Bible (Writing Style)", expanded=True):
        st.markdown("""
        **What it provides:** Your unique voice, tone, structure patterns, and proven formulas
        
        **How it's used:** System prompt context that teaches the AI how to write like you
        """)
        
        if bible:
            st.success("Newsletter Bible is loaded and active")
            
            # Show key elements
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Style Elements:**")
                style = bible.get('style', {})
                st.markdown(f"- Tone: {style.get('tone', 'N/A')}")
                st.markdown(f"- Voice: {style.get('voice', 'N/A')}")
                st.markdown(f"- Avg word count: {style.get('average_word_count', 'N/A')}")
            with col2:
                st.markdown("**Structure Patterns:**")
                structure = bible.get('structure', {})
                st.markdown(f"- Typical sections: {structure.get('typical_sections', 'N/A')}")
                st.markdown(f"- Opening style: {structure.get('opening_style', 'N/A')}")
        else:
            st.warning("Newsletter Bible not found. Go to Settings to generate it.")
    
    # 2. Knowledge Base (Facts & Sources)
    with st.expander("2. Knowledge Base (Facts & Sources)", expanded=True):
        st.markdown("""
        **What it provides:** Verified facts, statistics, quotes, and source URLs
        
        **How it's used:** Injects relevant, citable information into newsletter generation
        """)
        
        if HAS_KNOWLEDGE_BASE:
            try:
                facts_stats = get_facts_stats()
                total_facts = facts_stats.get('total_facts', 0)
                st.success(f"Knowledge Base active: {kb_stats.get('total_articles', 0)} articles, {total_facts} extracted facts")
                
                if total_facts > 0:
                    st.markdown("**Fact Types Available:**")
                    by_type = facts_stats.get('by_type', {})
                    for fact_type, count in by_type.items():
                        st.caption(f"- {fact_type.replace('_', ' ').title()}: {count}")
                else:
                    st.warning("⚠️ **No facts extracted yet!** Facts are pulled from articles to provide citable data to the AI.")
                    st.markdown("Click below to extract facts from your existing articles:")
                    
                    if st.button("🔬 Extract Facts from All Articles", type="primary"):
                        try:
                            from knowledge_base import process_all_articles_for_facts
                            with st.spinner("Extracting facts from articles... This may take a minute."):
                                result = process_all_articles_for_facts()
                                if result.get('articles_processed', 0) > 0:
                                    st.success(f"✅ Extracted {result.get('facts_extracted', 0)} facts from {result.get('articles_processed', 0)} articles!")
                                    st.rerun()
                                else:
                                    st.info("No articles to process. Add articles to the Knowledge Base first.")
                        except Exception as e:
                            st.error(f"Error extracting facts: {e}")
            except Exception as e:
                st.info(f"Knowledge Base available but no facts extracted yet. Error: {e}")
        else:
            st.warning("Knowledge Base not available")
    
    # 3. RAG - Writing Examples
    with st.expander("3. Similar Past Newsletters (RAG)", expanded=True):
        st.markdown("""
        **What it provides:** Passages from your past newsletters on similar topics
        
        **How it's used:** Shows the AI exactly how you've written about similar subjects before
        """)
        
        if RAG_AVAILABLE:
            st.success("RAG system active - semantic search across your newsletter archive")
            st.caption("When you generate a newsletter, the system finds 3-5 similar passages from your past work")
        else:
            st.info("RAG system not active. Newsletter generation will still work using the Bible.")
    
    # 4. Edit History & Preferences
    with st.expander("4. Your Edit History (Learned Preferences)", expanded=True):
        st.markdown("""
        **What it provides:** Patterns from how you edit AI suggestions
        
        **How it's used:** Adjusts outputs based on your demonstrated preferences
        """)
        
        learning_context = get_learning_context()
        if learning_context:
            st.success(f"Learning active: {edit_stats.get('total_edits', 0)} edits tracked")
            st.markdown("**Current Learned Context:**")
            st.text(learning_context[:1000] + "..." if len(learning_context) > 1000 else learning_context)
        else:
            st.info("No edit patterns learned yet. Edit a few generated newsletters to teach the AI your preferences.")
    
    # 5. Performance Learnings
    with st.expander("5. Performance Learnings (What Works)", expanded=True):
        st.markdown("""
        **What it provides:** Insights from your Substack metrics and notes on what worked/didn't
        
        **How it's used:** Guides the AI to replicate successful patterns and avoid failures
        """)
        
        if learnings:
            st.success("Performance learnings active")
            st.markdown("**Current Performance Context:**")
            st.text(learnings[:1500] + "..." if len(learnings) > 1500 else learnings)
        else:
            st.info("No performance learnings yet. Add stats and notes in Library > Progress & Stats")
    
    st.divider()
    
    # LIVE PREVIEW - Show exactly what would be sent
    st.markdown("### 🔍 Live Preview: Test What Gets Sent to the Model")
    st.markdown("*Enter a topic to see exactly what context would be included in the prompt*")
    
    test_topic = st.text_input("Test topic:", placeholder="e.g., 'AI replacing journalists'", key="model_test_topic")
    
    if st.button("Generate Preview", key="generate_model_preview") and test_topic:
        with st.spinner("Gathering context..."):
            preview_sections = {}
            
            # 1. Bible context
            if bible:
                bible_preview = "## YOUR WRITING STYLE\n\n"
                writing_voice = bible.get('writing_voice', {})
                sig_phrases = writing_voice.get('signature_phrases', [])
                if sig_phrases:
                    bible_preview += f"**Signature phrases:** {', '.join(sig_phrases[:5])}\n"
                
                rules = bible.get('rules_for_success', [])
                if rules:
                    bible_preview += f"\n**Rules:** {len(rules)} rules loaded\n"
                    bible_preview += f"First rule: {rules[0][:100]}...\n" if rules else ""
                
                cliches = bible.get('cliches_to_avoid', [])
                if cliches:
                    bible_preview += f"\n**Cliches to avoid:** {len(cliches)} cliches loaded\n"
                    bible_preview += f"Examples: {', '.join(cliches[:3])}\n"
                
                # Deep analysis
                deep = bible.get('deep_analysis', {})
                if deep:
                    bible_preview += f"\n**Deep analysis:** Integrated ✅\n"
                    vocab = deep.get('vocabulary', {})
                    if vocab:
                        bible_preview += f"- Signature words: {', '.join(vocab.get('signature_words', [])[:5])}\n"
                
                preview_sections['Newsletter Bible'] = bible_preview
            else:
                preview_sections['Newsletter Bible'] = "❌ NOT LOADED - Please generate Bible in Settings"
            
            # 2. Knowledge Base facts
            if HAS_KNOWLEDGE_BASE:
                try:
                    from knowledge_base import get_relevant_facts_context, get_relevant_facts
                    facts = get_relevant_facts(test_topic, max_facts=5)
                    if facts:
                        kb_preview = f"## KNOWLEDGE BASE FACTS ({len(facts)} relevant to '{test_topic}')\n\n"
                        for fact in facts[:3]:
                            kb_preview += f"- **{fact.get('fact_type', 'fact').upper()}:** {fact.get('text', '')[:100]}...\n"
                            kb_preview += f"  Source: {fact.get('source_url', 'No URL')}\n\n"
                        preview_sections['Knowledge Base'] = kb_preview
                    else:
                        preview_sections['Knowledge Base'] = f"⚠️ No facts found for topic '{test_topic}' - KB has {get_facts_stats().get('total_facts', 0)} total facts"
                except Exception as e:
                    preview_sections['Knowledge Base'] = f"❌ Error loading KB: {e}"
            else:
                preview_sections['Knowledge Base'] = "❌ Knowledge Base not available"
            
            # 3. RAG context
            if RAG_AVAILABLE:
                try:
                    from rag_system import get_writing_examples
                    examples = get_writing_examples(test_topic, n_results=3)
                    if examples:
                        rag_preview = f"## SIMILAR PAST NEWSLETTERS ({len(examples)} found)\n\n"
                        for i, ex in enumerate(examples[:2], 1):
                            rag_preview += f"**Example {i}:**\n{ex.get('text', '')[:200]}...\n\n"
                        preview_sections['RAG (Past Newsletters)'] = rag_preview
                    else:
                        preview_sections['RAG (Past Newsletters)'] = f"No similar passages found for '{test_topic}'"
                except Exception as e:
                    preview_sections['RAG (Past Newsletters)'] = f"⚠️ RAG error: {e}"
            else:
                preview_sections['RAG (Past Newsletters)'] = "RAG system not active (optional)"
            
            # 4. Deep style context
            if DEEP_ANALYZER_AVAILABLE:
                try:
                    deep_context = get_deep_style_context(test_topic)
                    if deep_context:
                        preview_sections['Deep Style Analysis'] = deep_context[:500] + "..."
                    else:
                        preview_sections['Deep Style Analysis'] = "No deep analysis available - Run Deep Analysis first"
                except:
                    preview_sections['Deep Style Analysis'] = "Deep analysis not available"
            
            # Display preview
            for section_name, section_content in preview_sections.items():
                with st.expander(f"📄 {section_name}", expanded=True):
                    st.text(section_content)
            
            # Summary
            st.markdown("### Summary")
            total_chars = sum(len(str(v)) for v in preview_sections.values())
            st.info(f"Total context size: ~{total_chars:,} characters ({total_chars//4:,} tokens approx)")
    
    st.divider()
    
    # 6. Fine-Tuned Model
    with st.expander("6. Fine-Tuned Model (Deep Style Learning)", expanded=True):
        st.markdown("""
        **What it provides:** A custom GPT model trained on all your past newsletters
        
        **How it's used:** Depends on the model tier (see below)
        """)
        
        if HAS_FINE_TUNING:
            try:
                active_model = get_active_fine_tuned_model()
                if active_model:
                    st.success(f"Fine-tuned model active: `{active_model}`")
                    
                    # Determine the model tier and explain generation mode
                    model_lower = active_model.lower()
                    if 'gpt-4o-mini' in model_lower:
                        st.info("""
                        **Generation Mode: Two-Stage**
                        1. Your fine-tuned model writes a style prompt
                        2. GPT-4.1 executes it to generate the full newsletter
                        
                        *Upgrade to GPT-4o fine-tuning for single-stage generation*
                        """)
                    elif 'gpt-4o' in model_lower:
                        st.success("""
                        **Generation Mode: Single-Stage (Best)**
                        - Your fine-tuned GPT-4o generates newsletters directly
                        - Your unique voice + powerful reasoning in one model
                        - No need for GPT-4.1 fallback
                        """)
                    else:
                        st.caption("Model tier: Unknown")
                else:
                    st.info("No fine-tuned model active yet. Train one in the Fine-Tuning tab.")
            except:
                st.info("Fine-tuning available but no model trained yet")
        else:
            st.warning("Fine-tuning module not available")


def render_fine_tuning_section():
    """Render the fine-tuning dashboard (moved from Settings)."""
    st.subheader("Fine-Tuning (Custom AI Model)")
    st.markdown("*Train a custom GPT model on your newsletters to write exactly like you*")
    
    if not HAS_FINE_TUNING:
        st.warning("Fine-tuning module not available. Check that fine_tuning.py exists.")
        return
    
    # Show current status
    ft_status = load_fine_tuning_status()
    active_model = ft_status.get('active_model')
    current_job_id = get_current_job_id()
    
    # =====================================================================
    # LIVE TRAINING STATUS (if a job is running)
    # =====================================================================
    if current_job_id:
        try:
            live_status = check_job_status(current_job_id)
            
            if live_status['status'] in ['validating_files', 'queued', 'running']:
                st.info("### Training In Progress")
                
                # Status metrics
                status_col1, status_col2, status_col3, status_col4 = st.columns(4)
                
                status_emoji = {
                    'validating_files': '',
                    'queued': '',
                    'running': '',
                }
                
                with status_col1:
                    st.metric("Status", f"{status_emoji.get(live_status['status'], '')} {live_status['status'].replace('_', ' ').title()}")
                
                with status_col2:
                    from datetime import datetime
                    try:
                        created = int(live_status['created_at'])
                        created_dt = datetime.fromtimestamp(created)
                        elapsed = datetime.now() - created_dt
                        elapsed_mins = int(elapsed.total_seconds() / 60)
                        st.metric("Elapsed", f"{elapsed_mins} min")
                    except:
                        st.metric("Elapsed", "-")
                
                with status_col3:
                    if live_status.get('trained_tokens'):
                        st.metric("Tokens Trained", f"{live_status['trained_tokens']:,}")
                    else:
                        st.metric("Tokens Trained", "Starting...")
                
                with status_col4:
                    st.metric("Base Model", live_status['base_model'].split('-')[0])
                
                # Training log
                with st.expander("Live Training Log", expanded=True):
                    events = get_job_events(current_job_id, limit=10)
                    for event in reversed(events):
                        level_icon = 'OK' if event['level'] == 'info' else ''
                        st.markdown(f"{level_icon} {event['message']}")
                
                if st.button("Refresh Status", key="refresh_training_status"):
                    st.rerun()
                
                st.divider()
            
            elif live_status['status'] == 'succeeded' and live_status.get('fine_tuned_model'):
                if not active_model:
                    set_active_model(live_status['fine_tuned_model'])
                    active_model = live_status['fine_tuned_model']
                    st.balloons()
        except Exception as e:
            st.warning(f"Could not fetch job status: {e}")
    
    # =====================================================================
    # ACTIVE MODEL STATUS
    # =====================================================================
    if active_model:
        st.success(f"**Active Fine-Tuned Model:** `{active_model}`")
        st.caption("This model is trained on YOUR writing style and is used for all newsletter generation.")
        
        # Show training metrics if available
        if current_job_id:
            try:
                metrics = get_training_metrics(current_job_id)
                if metrics.get('training_steps') and len(metrics['training_steps']) > 0:
                    with st.expander("Training Metrics", expanded=False):
                        met_col1, met_col2, met_col3 = st.columns(3)
                        with met_col1:
                            st.metric("Initial Loss", f"{metrics.get('initial_loss', 0):.4f}")
                        with met_col2:
                            st.metric("Final Loss", f"{metrics.get('final_loss', 0):.4f}")
                        with met_col3:
                            reduction = metrics.get('loss_reduction', 0)
                            st.metric("Improvement", f"{reduction}%", delta=f"-{reduction}% loss")
                        
                        if metrics.get('trained_tokens'):
                            st.markdown(f"**Total tokens trained:** {metrics['trained_tokens']:,}")
            except:
                pass
    else:
        st.info("No fine-tuned model active. Train one below to get newsletters that write exactly like you!")
    
    # =====================================================================
    # TABS: Train / Compare / Manage
    # =====================================================================
    ft_sub1, ft_sub2, ft_sub3, ft_sub4 = st.tabs([
        "Create Training Data", 
        "Start Training", 
        "Compare Models",
        "Manage Models"
    ])
    
    with ft_sub1:
        st.markdown("""
        **Step 1: Export your newsletters as training data**
        
        This converts your newsletters into training pairs (idea > newsletter) 
        that OpenAI uses to teach the model your writing style.
        """)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("Export Training Data", use_container_width=True, type="primary", key="ft_export_btn"):
                with st.spinner("Exporting newsletters..."):
                    result = export_training_data()
                    st.session_state['ft_export_result'] = result
        
        with col2:
            st.markdown("**What happens:**")
            st.markdown("- Extracts all newsletters")
            st.markdown("- Creates idea>newsletter pairs")
            st.markdown("- Saves as JSONL file")
        
        if 'ft_export_result' in st.session_state:
            result = st.session_state['ft_export_result']
            st.success(f"Exported **{result['training_examples']}** training examples!")
            
            cost = result.get('cost_estimate', {})
            st.markdown(f"""
            **Training Cost Estimate:**
            - Tokens: **{cost.get('total_tokens', 0):,}**
            - Estimated cost: **${cost.get('estimated_cost_usd', 0):.2f}**
            - Base model: `{cost.get('base_model', 'gpt-4o-mini')}`
            """)
    
    with ft_sub2:
        st.markdown("""
        **Step 2: Choose model and start fine-tuning**
        
        Training typically takes 15-60 minutes.
        """)
        
        # Model selection with clear explanations
        st.markdown("#### Choose Your Base Model")
        
        model_options = {
            "gpt-4o-2024-08-06": "GPT-4o (Recommended) - Full newsletter generation",
            "gpt-4o-mini-2024-07-18": "GPT-4o-mini (Budget) - Style prompts only",
        }
        
        base_model = st.selectbox(
            "Base Model",
            list(model_options.keys()),
            index=0,
            format_func=lambda x: model_options.get(x, x),
            key="ft_base_model"
        )
        
        # Show model-specific info
        if base_model == "gpt-4o-2024-08-06":
            st.success("""
            **GPT-4o Fine-Tuning (Recommended)**
            - Single-stage generation: Your voice + powerful reasoning
            - Handles full 1000+ word newsletters directly
            - No need for GPT-4.1 fallback
            - Higher training cost, but better results
            """)
        else:
            st.info("""
            **GPT-4o-mini Fine-Tuning (Budget)**
            - Two-stage generation: Style prompts + GPT-4.1 execution
            - Good for headlines and style guidance
            - Lower cost, but requires GPT-4.1 for full newsletters
            """)
        
        model_suffix = st.text_input(
            "Model Suffix",
            value="newsletter-paul",
            help="Custom name for your model",
            key="ft_model_suffix"
        )
        
        epochs = st.slider(
            "Training Epochs",
            min_value=1,
            max_value=10,
            value=3,
            help="3 is usually ideal.",
            key="ft_epochs"
        )
        
        # Show cost estimate based on selected model
        if 'ft_export_result' in st.session_state:
            # Recalculate cost for selected model
            from fine_tuning import estimate_training_cost
            training_examples = st.session_state['ft_export_result'].get('training_examples', 0)
            tokens = st.session_state['ft_export_result'].get('cost_estimate', {}).get('total_tokens', 0)
            
            # Estimate based on selected model
            if base_model == "gpt-4o-2024-08-06":
                est_cost = (tokens / 1_000_000) * 25.00
                per_newsletter = 0.03  # ~$0.03 per newsletter
            else:
                est_cost = (tokens / 1_000_000) * 0.30
                per_newsletter = 0.001  # ~$0.001 per newsletter
            
            st.markdown(f"""
            **Cost Estimate for {model_options.get(base_model, base_model)}:**
            - Training cost: **${est_cost:.2f}**
            - Per newsletter (after training): **${per_newsletter:.3f}**
            - Total tokens: {tokens:,}
            """)
        
        if st.button("Start Fine-Tuning", use_container_width=True, type="primary", key="ft_start_btn"):
            with st.spinner("Uploading training data..."):
                try:
                    file_id = upload_training_file()
                    st.success(f"File uploaded: `{file_id}`")
                    
                    with st.spinner("Creating fine-tuning job..."):
                        job = create_fine_tuning_job(
                            training_file_id=file_id,
                            base_model=base_model,
                            suffix=model_suffix,
                            n_epochs=epochs
                        )
                        st.session_state['ft_current_job'] = job
                        st.success(f"Job created: `{job['job_id']}`")
                        st.info("Refresh the page to see live training status above.")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with ft_sub3:
        st.markdown("### Compare Base vs Fine-Tuned Model")
        st.markdown("*See the real difference in writing quality*")
        
        if not active_model:
            st.warning("No fine-tuned model available yet. Complete training first!")
        else:
            test_idea = st.text_area(
                "Enter a test newsletter idea:",
                value="Write a newsletter about how African AI startups are using local languages to build more inclusive AI products",
                height=100,
                key="ft_compare_idea"
            )
            
            if st.button("Generate Comparison", type="primary", key="ft_compare_btn"):
                with st.spinner("Generating with both models..."):
                    comparison = compare_models(
                        idea=test_idea,
                        fine_tuned_model=active_model,
                        max_tokens=800
                    )
                    st.session_state['model_comparison'] = comparison
            
            if 'model_comparison' in st.session_state:
                comp = st.session_state['model_comparison']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Base Model (GPT-4o-mini)")
                    st.caption(f"Tokens: {comp.get('base_tokens', 0)}")
                    st.markdown("---")
                    st.markdown(comp.get('base_output', 'No output'))
                
                with col2:
                    st.markdown("#### YOUR Fine-Tuned Model")
                    st.caption(f"Tokens: {comp.get('fine_tuned_tokens', 0)}")
                    st.markdown("---")
                    st.markdown(comp.get('fine_tuned_output', 'No output'))
    
    with ft_sub4:
        st.markdown("**Manage your fine-tuned models and training jobs**")
        
        if st.button("Refresh Jobs & Models", key="ft_refresh_btn"):
            st.session_state['ft_jobs'] = list_fine_tuning_jobs()
            st.session_state['ft_models'] = list_fine_tuned_models()
        
        if 'ft_jobs' in st.session_state and st.session_state['ft_jobs']:
            st.markdown("### Recent Training Jobs")
            for job in st.session_state['ft_jobs'][:5]:
                status_emoji = {'succeeded': 'OK', 'failed': 'FAIL', 'running': 'RUN', 'queued': 'WAIT'}
                emoji = status_emoji.get(job['status'], '?')
                with st.expander(f"{emoji} {job['status'].upper()} - {job['job_id'][:20]}..."):
                    st.json(job)
        
        if 'ft_models' in st.session_state and st.session_state['ft_models']:
            st.markdown("### Available Fine-Tuned Models")
            for model in st.session_state['ft_models']:
                model_id = model['model_id']
                is_active = model_id == active_model
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    if is_active:
                        st.markdown(f"**{model_id}** (active)")
                    else:
                        st.markdown(f"{model_id}")
                with col2:
                    if not is_active:
                        if st.button("Use", key=f"use_model_{model_id}"):
                            set_active_model(model_id)
                            st.success(f"Now using: {model_id}")
                            st.rerun()
        
        if 'ft_jobs' not in st.session_state:
            st.caption("Click 'Refresh Jobs & Models' to load from OpenAI")


def render_ai_learning_section():
    """Render the AI learning dashboard (moved from Settings)."""
    st.subheader("AI Learning Dashboard")
    st.markdown("*See how the AI is learning from your edits and preferences*")
    
    # Get learning stats
    edit_stats = get_edit_stats()
    
    # Stats cards
    learn_col1, learn_col2, learn_col3, learn_col4 = st.columns(4)
    
    with learn_col1:
        st.metric("Total Edits Tracked", edit_stats.get('total_edits', 0))
    with learn_col2:
        st.metric("Custom Headlines", edit_stats.get('custom_headlines', 0), 
                  help="Headlines you wrote instead of using AI suggestions")
    with learn_col3:
        st.metric("Tone Adjustments", edit_stats.get('tone_adjustments', 0),
                  help="Times you changed the suggested tone")
    with learn_col4:
        st.metric("Content Additions", edit_stats.get('content_additions', 0),
                  help="Bullet points and content you added")
    
    # Show learned preferences
    learning_context = get_learning_context()
    
    if learning_context:
        with st.expander("What the AI has learned about your preferences", expanded=True):
            st.markdown(learning_context)
            st.caption("This context is included in every generation prompt to personalize outputs.")
    else:
        st.info("The AI hasn't learned your preferences yet. Generate and edit a few newsletters to teach it your style!")
    
    # Show recent edit history
    from learning_system import load_edit_history
    history = load_edit_history()
    
    if history:
        with st.expander(f"Recent Edit History ({len(history)} edits)", expanded=False):
            for i, edit in enumerate(reversed(history[-10:])):
                st.markdown(f"**{edit.get('timestamp', 'Unknown')[:10]}** - {edit.get('idea', 'No idea')[:50]}...")
                changes = edit.get('changes', [])
                if changes:
                    for change in changes:
                        change_type = change.get('type', 'unknown')
                        if change_type == 'custom_headline':
                            st.markdown(f"  - Wrote custom headline: *\"{change.get('user_wrote', '')[:50]}...\"*")
                        elif change_type == 'chose_headline':
                            st.markdown(f"  - Chose headline option #{change.get('index', 0) + 1}")
                        elif change_type == 'tone_adjustment':
                            st.markdown(f"  - Adjusted tone to: *{change.get('adjusted_to', '')[:50]}*")
                        elif change_type == 'bullets_added':
                            st.markdown(f"  - Added {len(change.get('added', []))} bullet points")
                        elif change_type == 'user_notes':
                            st.markdown(f"  - Added notes to section {change.get('section', 0) + 1}")
                st.divider()
    
    # Clear learning data
    with st.expander("Reset Learning Data", expanded=False):
        st.warning("This will delete all learned preferences. The AI will start fresh.")
        if st.button("Clear All Learning Data", type="secondary", key="clear_learning_btn"):
            from learning_system import save_learnings, save_edit_history
            save_learnings({
                'headline_preferences': [],
                'section_preferences': [],
                'tone_adjustments': [],
                'common_additions': [],
                'rejected_patterns': [],
            })
            save_edit_history([])
            st.success("Learning data cleared!")
            st.rerun()


def render_published_newsletters_section():
    """Render published newsletters section (training data source)."""
    st.subheader("Published Newsletters (Training Data)")
    st.markdown("*Newsletters you've published become training data for your AI model*")
    
    if not HAS_PUBLISHED:
        st.warning("Published newsletters module not available.")
        return
    
    # Get published stats
    pub_stats = get_published_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Published", pub_stats.get('total_published', 0))
    with col2:
        st.metric("Ready for Training", pub_stats.get('ready_for_training', 0),
                  help="Newsletters not yet used for fine-tuning")
    with col3:
        st.metric("Total Words", f"{pub_stats.get('total_words', 0):,}")
    
    published = get_published_newsletters()
    
    if published:
        with st.expander(f"View Published Newsletters ({len(published)})", expanded=False):
            for pub in published:
                st.markdown(f"**{pub.get('headline', 'Untitled')}**")
                st.caption(f"{pub.get('published_at', '')[:10]} | {pub.get('word_count', 0)} words | {'Trained' if pub.get('used_for_training') else 'Pending'}")
                st.divider()
        
        ready_count = pub_stats.get('ready_for_training', 0)
        if ready_count > 0:
            st.info(f"{ready_count} newsletter(s) ready for training")
            
            if st.button("Export for Fine-Tuning", type="primary", key="export_published_btn", help="Export new newsletters as training data"):
                result = export_published_for_training()
                if result.get('success'):
                    st.success(f"Exported {result['count']} newsletters")
                    st.caption("You can now use these in the Fine-Tuning tab to improve your model.")
    else:
        st.info("No newsletters published yet. Use the **Publish & Train** button after generating a newsletter to add it to your training data.")


def render_performance_learnings_section():
    """Render performance learnings section - stats and notes that feed into the model."""
    st.subheader("Performance Learnings")
    st.markdown("*Your Substack stats and notes on what worked/didn't - these feed into future generation*")
    
    # Get all stats
    all_stats = get_all_newsletter_stats()
    published_stats = [s for s in all_stats if s.get('status') == 'published']
    
    # Summary
    col1, col2, col3, col4 = st.columns(4)
    
    newsletters_with_notes = len([s for s in all_stats if s.get('notes')])
    newsletters_with_stats = len([s for s in all_stats if s.get('substack_views', 0) > 0])
    
    with col1:
        st.metric("Total Newsletters", len(all_stats))
    with col2:
        st.metric("With Stats", newsletters_with_stats)
    with col3:
        st.metric("With Notes", newsletters_with_notes)
    with col4:
        avg_open_rate = sum(s.get('substack_open_rate', 0) for s in published_stats) / len(published_stats) if published_stats else 0
        st.metric("Avg Open Rate", f"{avg_open_rate:.1f}%")
    
    st.divider()
    
    # What's currently being fed to the model
    st.markdown("### Current Learnings Fed to Model")
    
    learnings = get_performance_learnings()
    
    if learnings:
        st.success("Performance learnings are active and being used in generation")
        with st.expander("View Full Learnings Context", expanded=True):
            st.text(learnings)
    else:
        st.info("No performance learnings yet. Add stats and notes in Library > Progress & Stats")
        st.markdown("""
        **To build performance learnings:**
        1. Go to **Library** > **Progress & Stats** tab
        2. Select a published newsletter
        3. Add your Substack metrics (views, opens, open rate, etc.)
        4. Add notes about what worked and what didn't
        5. These insights will automatically inform future newsletter generation
        """)
    
    st.divider()
    
    # Quick stats entry
    st.markdown("### Quick Stats Entry")
    st.caption("Go to Library > Progress & Stats for full stats entry. This is a quick overview.")
    
    if all_stats:
        for s in all_stats[:5]:
            with st.expander(f"{s['headline'][:50]}..." if len(s['headline']) > 50 else s['headline']):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.caption(f"Status: {s['status']}")
                    st.caption(f"Views: {s.get('substack_views', 0)}")
                with col2:
                    st.caption(f"Open Rate: {s.get('substack_open_rate', 0):.1f}%")
                    st.caption(f"New Subs: {s.get('substack_new_subscribers', 0)}")
                with col3:
                    st.caption(f"Creation Time: {s.get('creation_time_minutes', 0)} min")
                
                if s.get('notes'):
                    st.markdown(f"**Notes:** {s['notes']}")
                else:
                    st.caption("No notes yet")
    else:
        st.info("No newsletters found. Create and publish newsletters to track their performance.")


# ============================================================================
# Tab 5: Newsletter Bible
# ============================================================================
# Tab 4: Content Inbox
# ============================================================================

def render_inbox_tab():
    """Render the Content Inbox tab - scrape and collect AI news."""
    st.header("Content Inbox")
    st.markdown("*Scrape AI news from the last 2 days and add to your Knowledge Base*")
    
    # Source indicator - compact since this is a simple collection tab
    render_source_indicator("Content Collection", show_model=False, show_kb=True, show_bible=False, compact=True)
    
    # Get stats
    inbox_stats = get_inbox_stats()
    kb_stats = get_kb_stats() if HAS_KNOWLEDGE_BASE else {'total_articles': 0, 'recent_articles': 0}
    
    # Stats row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Knowledge Base", kb_stats.get('total_articles', 0), 
                  help="Curated articles that inform content")
    with col2:
        st.metric("Recent (2 days)", kb_stats.get('recent_articles', 0),
                  help="Articles from last 2 days")
    with col3:
        scraped_count = len(st.session_state.get('scraped_news', []))
        st.metric("Scraped News", scraped_count)
    
    st.divider()
    
    # Quick link to full Knowledge Base
    st.info("For full Knowledge Base management (add URLs, upload PDFs, browse articles), go to the **Knowledge Base** tab.")
    
    st.divider()
    
    # =========================================================================
    # SCRAPE NEWS SECTION
    # =========================================================================
    st.subheader("Scrape Recent AI News")
    st.markdown("*Fetch AI news from the last 2 days. Select articles to add to your knowledge base.*")
    
    if not HAS_NEWS_FETCHER:
        st.warning("News fetcher not available. Install feedparser: `pip install feedparser`")
    else:
        # Fetch and Clear buttons
        fetch_col, clear_col, checkbox_col = st.columns([2, 1, 1])
        with fetch_col:
            if st.button("Scrape Latest AI News", type="primary", use_container_width=True):
                with st.spinner("Fetching news from RSS feeds (last 2 days)..."):
                    news = get_selectable_news()
                    st.session_state['scraped_news'] = news
                    st.success(f"Found {len(news)} articles from the last 2 days")
        
        with clear_col:
            if st.button("Clear Scraped News", use_container_width=True):
                st.session_state['scraped_news'] = []
                st.rerun()
        
        with checkbox_col:
            include_africa = st.checkbox("Include Africa tech", value=True)
        
        # Display scraped news with selection (persisted in session state)
        if 'scraped_news' in st.session_state and st.session_state['scraped_news']:
            news = st.session_state['scraped_news']
            
            st.markdown(f"**{len(news)} articles available** - select the ones you want to add to your knowledge base:")
            
            # Select all / none
            sel_col1, sel_col2, sel_col3 = st.columns([1, 1, 2])
            with sel_col1:
                if st.button("Select All"):
                    for article in news:
                        article['selected'] = True
                    st.rerun()
            with sel_col2:
                if st.button("Select None"):
                    for article in news:
                        article['selected'] = False
                    st.rerun()
            with sel_col3:
                selected_count = sum(1 for a in news if a.get('selected', False))
                st.markdown(f"**{selected_count}** selected")
            
            st.divider()
            
            # Display articles in a scrollable container
            for i, article in enumerate(news):
                with st.container():
                    chk_col, info_col = st.columns([1, 10])
                    
                    with chk_col:
                        selected = st.checkbox(
                            "",
                            value=article.get('selected', False),
                            key=f"select_article_{i}"
                        )
                        article['selected'] = selected
                    
                    with info_col:
                        # Source badge
                        source = article.get('source', 'Unknown')
                        category = article.get('category', 'tech')
                        badge = "" if category == 'africa' else ""
                        
                        st.markdown(f"**{article.get('title', 'Untitled')}**")
                        st.markdown(f"{badge} {source} | [Link]({article.get('url', '#')})")
                        
                        if article.get('summary'):
                            st.caption(article['summary'][:150] + "...")
                    
                    st.divider()
            
            # Add selected to knowledge base
            st.markdown("### Add to Knowledge Base")
            selected_articles = [a for a in news if a.get('selected', False)]
            
            if selected_articles:
                if st.button(f"Add {len(selected_articles)} Articles to Knowledge Base", type="primary"):
                    if HAS_KNOWLEDGE_BASE:
                        added = add_articles_batch(selected_articles)
                        st.success(f"Added {added} articles to knowledge base!")
                        # Clear selection but keep the news list
                        for article in news:
                            article['selected'] = False
                        st.rerun()
                    else:
                        st.error("Knowledge base not available")
            else:
                st.info("Select articles above to add them to your knowledge base")


# ============================================================================
# Tab 5: Library - Saved Newsletters
# ============================================================================

def render_library_tab():
    """Render the Newsletter Library tab - browse, manage, publish, and track newsletters."""
    
    st.header("Newsletter Library")
    st.markdown("*Your saved newsletters, publishing tools, and performance tracking*")
    
    # Sub-tabs combining Library and Publishing features
    lib_tab1, lib_tab2, lib_tab3, lib_tab4, lib_tab5, lib_tab6 = st.tabs([
        "Newsletters",
        "Progress & Stats",
        "Best Time to Publish",
        "Social Media Posts",
        "Performance Insights",
        "Publishing Checklist"
    ])
    
    with lib_tab1:
        render_newsletters_subtab()
    
    with lib_tab2:
        render_progress_subtab()
    
    with lib_tab3:
        render_best_time_subtab()
    
    with lib_tab4:
        render_social_media_subtab()
    
    with lib_tab5:
        render_performance_insights_subtab()
    
    with lib_tab6:
        render_publishing_checklist_subtab()


def render_newsletters_subtab():
    """Render the newsletters browsing sub-tab."""
    # Get database stats
    db_stats = get_db_stats()
    
    # Stats bar
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Newsletters", db_stats['total_newsletters'])
    with col2:
        st.metric("Total Versions", db_stats['total_versions'])
    with col3:
        drafts = db_stats.get('by_status', {}).get('draft', 0)
        st.metric("Drafts", drafts)
    with col4:
        published = db_stats.get('by_status', {}).get('published', 0)
        st.metric("Published", published)
    
    st.divider()
    
    # Filters
    filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])
    
    with filter_col1:
        search_query = st.text_input("Search", placeholder="Search headlines and ideas...", key="library_search")
    
    with filter_col2:
        status_filter = st.selectbox(
            "Status",
            options=["All", "draft", "in_progress", "ready", "published"],
            key="library_status"
        )
    
    with filter_col3:
        sort_by = st.selectbox(
            "Sort by",
            options=["Updated (newest)", "Created (newest)", "Headline (A-Z)"],
            key="library_sort"
        )
    
    # Get newsletters
    status = None if status_filter == "All" else status_filter
    sort_field = 'updated_at'
    if 'Created' in sort_by:
        sort_field = 'created_at'
    elif 'Headline' in sort_by:
        sort_field = 'headline'
    
    newsletters = list_newsletters(
        status=status,
        search=search_query if search_query else None,
        sort_by=sort_field,
        sort_desc='newest' in sort_by.lower() or 'A-Z' not in sort_by,
        limit=50
    )
    
    if not newsletters:
        st.info("📭 No newsletters saved yet. Generate your first newsletter to see it here!")
        return
    
    st.markdown(f"**{len(newsletters)} newsletter(s) found**")
    
    # Newsletter list - each is an expandable card
    for nl in newsletters:
        headline = nl.get('headline', 'Untitled')
        
        # Content stage badge
        content_stage = nl.get('content_stage', 'idea')
        stage_badge = {
            'idea': '[Idea]',
            'outline': '[Outline]',
            'complete': '[Complete]'
        }.get(content_stage, '[Idea]')
        
        status_badge = {
            'draft': 'Draft',
            'in_progress': 'In Progress',
            'ready': 'Ready',
            'published': 'Published'
        }.get(nl.get('status', 'draft'), 'Draft')
        
        updated = nl.get('updated_at', '')[:10] if nl.get('updated_at') else ''
        
        # Make each newsletter an expander so you can click to read
        with st.expander(f"**{headline}** — {stage_badge} {status_badge} — {updated}", expanded=False):
            # Get full newsletter data
            full_nl = get_newsletter(nl['id'])
            
            if full_nl:
                current_version = full_nl['versions'].get(full_nl['current_version'], {})
                content = current_version.get('content', '')
                
                # Action buttons at top
                btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
                with btn_col1:
                    if st.button("Continue Editing", key=f"continue_{nl['id']}", use_container_width=True):
                        st.session_state.current_newsletter_id = nl['id']
                        st.session_state.generator_idea = full_nl.get('idea', '')
                        st.session_state.generator_outline = current_version.get('outline', {})
                        st.session_state.generator_edited_outline = current_version.get('edited_outline', {})
                        st.session_state.generator_story_type = full_nl.get('story_type', '')
                        st.session_state.generator_sections = current_version.get('sections', [])
                        st.session_state.generator_metrics = current_version.get('metrics', {})
                        st.session_state.generator_final = current_version.get('content', '')
                        st.session_state.generator_step = 4 if current_version.get('content') else 2
                        st.success("Loaded! Go to **Write** tab to continue.")
                
                with btn_col2:
                    if content:
                        st.download_button(
                            "Download .md",
                            data=content,
                            file_name=f"{headline[:30].replace(' ', '_')}.md",
                            mime="text/markdown",
                            use_container_width=True,
                            key=f"download_{nl['id']}"
                        )
                
                with btn_col3:
                    # Metadata
                    versions_count = nl.get('version_count', 1)
                    story_type = nl.get('story_type', 'unclassified')
                    st.caption(f"{versions_count} version(s) | {story_type}")
                
                st.divider()
                
                # Show the full content
                if content:
                    st.markdown("### Full Newsletter Content")
                    st.markdown(content)
                else:
                    # Show outline if no content
                    edited_outline = current_version.get('edited_outline', {})
                    if edited_outline:
                        st.markdown("### Outline (No full content yet)")
                        st.markdown(f"**Headline:** {edited_outline.get('headline', 'Not set')}")
                        st.markdown(f"**Preview:** {edited_outline.get('preview', 'Not set')}")
                        sections = edited_outline.get('sections', [])
                        if sections:
                            st.markdown("**Sections:**")
                            for section in sections:
                                if isinstance(section, dict):
                                    st.markdown(f"- {section.get('heading', 'Section')}")
                                elif isinstance(section, str):
                                    st.markdown(f"- {section}")
                    else:
                        idea = nl.get('idea', '')
                        if idea:
                            st.markdown("### Idea (No outline or content yet)")
                            st.markdown(idea)
                        else:
                            st.info("No content generated yet for this newsletter.")
            else:
                st.error("Could not load newsletter data")
            
            # Delete option at bottom of each expander
            st.divider()
            delete_col1, delete_col2 = st.columns([3, 1])
            with delete_col2:
                if st.button("Delete", key=f"delete_{nl['id']}", type="secondary"):
                    if delete_newsletter(nl['id']):
                        st.success("Newsletter deleted")
                        st.rerun()


def render_progress_subtab():
    """Render the progress and stats tracking sub-tab."""
    st.subheader("Progress & Performance Tracking")
    st.markdown("*Track creation time and Substack performance for each newsletter*")
    
    # Get all newsletter stats
    all_stats = get_all_newsletter_stats()
    published_stats = [s for s in all_stats if s.get('status') == 'published']
    
    # Summary metrics
    st.markdown("### Overall Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    total_time = sum(s.get('creation_time_minutes', 0) for s in all_stats)
    total_views = sum(s.get('substack_views', 0) for s in published_stats)
    total_opens = sum(s.get('substack_opens', 0) for s in published_stats)
    total_new_subs = sum(s.get('substack_new_subscribers', 0) for s in published_stats)
    
    with col1:
        hours = total_time // 60
        mins = total_time % 60
        st.metric("Total Creation Time", f"{hours}h {mins}m" if hours > 0 else f"{mins}m")
    with col2:
        st.metric("Total Views", f"{total_views:,}")
    with col3:
        st.metric("Total Opens", f"{total_opens:,}")
    with col4:
        st.metric("New Subscribers", f"+{total_new_subs}")
    
    if published_stats:
        avg_time = total_time / len(published_stats) if published_stats else 0
        avg_views = total_views / len(published_stats) if published_stats else 0
        avg_open_rate = sum(s.get('substack_open_rate', 0) for s in published_stats) / len(published_stats) if published_stats else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Avg. Creation Time", f"{int(avg_time)} min")
        with col2:
            st.metric("Avg. Views", f"{int(avg_views):,}")
        with col3:
            st.metric("Avg. Open Rate", f"{avg_open_rate:.1f}%")
    
    st.divider()
    
    # Select a newsletter to add/edit stats
    st.markdown("### Add/Edit Newsletter Stats")
    
    if not all_stats:
        st.info("No newsletters found. Create and publish newsletters to track their performance.")
        return
    
    # Dropdown to select newsletter
    newsletter_options = {f"{s['headline'][:50]}... ({s['status']})" if len(s['headline']) > 50 else f"{s['headline']} ({s['status']})": s['id'] for s in all_stats}
    
    selected_label = st.selectbox(
        "Select Newsletter",
        options=list(newsletter_options.keys()),
        key="progress_newsletter_select"
    )
    
    if selected_label:
        selected_id = newsletter_options[selected_label]
        selected_stats = next((s for s in all_stats if s['id'] == selected_id), None)
        
        if selected_stats:
            st.markdown(f"**{selected_stats['headline']}**")
            st.caption(f"Status: {selected_stats['status']} | Created: {selected_stats['created_at'][:10] if selected_stats['created_at'] else 'N/A'}")
            
            # Form for editing stats
            with st.form(key=f"stats_form_{selected_id}"):
                st.markdown("#### Creation Time")
                creation_time = st.number_input(
                    "Time spent creating (minutes)",
                    min_value=0,
                    max_value=600,
                    value=selected_stats.get('creation_time_minutes', 0),
                    help="How long did it take to create this newsletter from idea to final?"
                )
                
                st.markdown("#### Substack Performance Metrics")
                st.caption("Enter these stats from your Substack dashboard")
                
                col1, col2 = st.columns(2)
                with col1:
                    published_date = st.date_input(
                        "Published Date",
                        value=None,
                        help="When was this published on Substack?"
                    )
                    substack_views = st.number_input(
                        "Views",
                        min_value=0,
                        value=selected_stats.get('substack_views', 0)
                    )
                    substack_opens = st.number_input(
                        "Opens",
                        min_value=0,
                        value=selected_stats.get('substack_opens', 0)
                    )
                
                with col2:
                    substack_url = st.text_input(
                        "Substack URL",
                        value=selected_stats.get('substack_url', ''),
                        placeholder="https://yourname.substack.com/p/..."
                    )
                    substack_open_rate = st.number_input(
                        "Open Rate (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(selected_stats.get('substack_open_rate', 0)),
                        step=0.1
                    )
                    substack_clicks = st.number_input(
                        "Clicks",
                        min_value=0,
                        value=selected_stats.get('substack_clicks', 0)
                    )
                
                substack_new_subscribers = st.number_input(
                    "New Subscribers from this post",
                    min_value=0,
                    value=selected_stats.get('substack_new_subscribers', 0)
                )
                
                st.markdown("#### Learnings & Notes")
                notes = st.text_area(
                    "What worked? What didn't? Lessons learned?",
                    value=selected_stats.get('notes', ''),
                    height=120,
                    placeholder="e.g., 'Strong headline drove high open rate. Personal story at the start got good engagement. Could have been shorter in the middle section...'",
                    help="These notes feed back into the model to improve future newsletters"
                )
                
                submitted = st.form_submit_button("Save Stats", type="primary", use_container_width=True)
                
                if submitted:
                    update_newsletter_stats(
                        newsletter_id=selected_id,
                        creation_time_minutes=creation_time,
                        substack_views=substack_views,
                        substack_opens=substack_opens,
                        substack_open_rate=substack_open_rate,
                        substack_clicks=substack_clicks,
                        substack_new_subscribers=substack_new_subscribers,
                        substack_url=substack_url,
                        published_date=published_date.isoformat() if published_date else None,
                        notes=notes,
                    )
                    st.success("Stats saved successfully! Learnings will inform future newsletter generation.")
                    st.rerun()
    
    st.divider()
    
    # Show all newsletter stats in a table
    st.markdown("### All Newsletter Performance")
    
    if published_stats:
        # Create a dataframe-like display
        for s in published_stats:
            with st.expander(f"{s['headline'][:60]}..." if len(s['headline']) > 60 else s['headline']):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    time_mins = s.get('creation_time_minutes', 0)
                    st.metric("Creation Time", f"{time_mins} min" if time_mins > 0 else "Not recorded")
                with col2:
                    st.metric("Views", f"{s.get('substack_views', 0):,}")
                with col3:
                    st.metric("Open Rate", f"{s.get('substack_open_rate', 0):.1f}%")
                with col4:
                    st.metric("New Subs", f"+{s.get('substack_new_subscribers', 0)}")
                
                if s.get('substack_url'):
                    st.markdown(f"[View on Substack]({s['substack_url']})")
                
                # Show notes if available
                if s.get('notes'):
                    st.markdown("**Notes & Learnings:**")
                    st.markdown(f"*{s['notes']}*")
    else:
        st.info("No published newsletters yet. Publish newsletters and add their Substack stats to see performance data here.")
    
    st.divider()
    
    # Show aggregated learnings that feed into the model
    st.markdown("### Learnings Feeding Into Model")
    st.caption("These insights from your notes and performance data are automatically used when generating new newsletters")
    
    learnings = get_performance_learnings()
    if learnings:
        with st.expander("View Current Learnings", expanded=False):
            st.markdown(learnings)
    else:
        st.info("Add notes and stats to your published newsletters to build up learnings that improve future generation.")


def render_best_time_subtab():
    """Render the best time to publish analysis subtab."""
    st.subheader("Optimal Publishing Time")
    st.markdown("*Based on analysis of your newsletter performance data*")
    
    if not HAS_PUBLISHING:
        st.warning("Publishing analytics not available. Check that publishing_analytics.py exists.")
        return
    
    try:
        recommendation = get_publishing_recommendation()
        day_analysis = recommendation.get('day_analysis', {})
        
        # Show the main recommendation
        optimal = recommendation.get('optimal_publish_time', {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Best Day",
                optimal.get('day', 'Tuesday'),
                help="Day with highest average open rate"
            )
        with col2:
            st.metric(
                "Recommended Time",
                optimal.get('time', '10:00 AM'),
                help="Based on industry best practices for B2B newsletters"
            )
        with col3:
            confidence = day_analysis.get('confidence', 'low')
            confidence_emoji = {'high': 'High', 'medium': 'Medium', 'low': 'Low'}.get(confidence, 'Low')
            st.metric(
                "Confidence",
                confidence_emoji,
                help=f"Based on {day_analysis.get('best_day_sample_size', 0)} newsletters"
            )
        
        # Show the recommendation
        st.info(day_analysis.get('recommendation', 'Not enough data for recommendations.'))
        
        # Day-by-day breakdown
        st.markdown("### Day-by-Day Performance")
        
        day_stats = day_analysis.get('day_stats', {})
        if day_stats:
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            for day in days_order:
                if day in day_stats:
                    stats = day_stats[day]
                    open_rate = stats.get('avg_open_rate', 0)
                    count = stats.get('count', 0)
                    
                    max_rate = max([s.get('avg_open_rate', 0) for s in day_stats.values()])
                    bar_width = int((open_rate / max_rate) * 100) if max_rate > 0 else 0
                    
                    is_best = day == day_analysis.get('best_day')
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if is_best:
                            st.markdown(f"**{day}** (Best)")
                        else:
                            st.markdown(day)
                    with col2:
                        st.progress(bar_width / 100)
                        st.caption(f"{open_rate*100:.1f}% open rate ({count} newsletters)")
        else:
            st.warning("Not enough data to show day-by-day breakdown. Publish more newsletters to get insights.")
        
        # Improvement potential
        if day_analysis.get('improvement_potential'):
            st.markdown("---")
            st.markdown(f"**Potential improvement:** Switching from {day_analysis.get('worst_day', 'worst day')} to {day_analysis.get('best_day', 'best day')} could improve open rates by **{day_analysis.get('improvement_potential', 'N/A')}**")
    
    except Exception as e:
        st.error(f"Error loading analytics: {e}")


def render_social_media_subtab():
    """Render the social media posts generation subtab."""
    st.subheader("Social Media Distribution")
    st.markdown("*Generate posts to promote your newsletter on social platforms*")
    
    if not HAS_PUBLISHING:
        st.warning("Publishing analytics not available.")
        return
    
    # Check if we have a current newsletter
    edited_outline = st.session_state.get('generator_edited_outline') or {}
    current_headline = edited_outline.get('headline', '') if isinstance(edited_outline, dict) else ''
    current_preview = edited_outline.get('preview', '') if isinstance(edited_outline, dict) else ''
    current_content = st.session_state.get('generator_final', '') or ''
    
    col1, col2 = st.columns(2)
    
    with col1:
        headline = st.text_input(
            "Newsletter Headline",
            value=current_headline,
            help="The headline of your newsletter",
            key="social_headline"
        )
    
    with col2:
        newsletter_url = st.text_input(
            "Newsletter URL",
            value="",
            placeholder="https://yoursubstack.substack.com/p/...",
            help="Link to your newsletter (leave blank if not published yet)",
            key="social_url"
        )
    
    preview = st.text_area(
        "Preview/Description",
        value=current_preview,
        height=80,
        help="Brief description of what the newsletter covers",
        key="social_preview"
    )
    
    key_points_text = st.text_area(
        "Key Points (one per line)",
        value="",
        height=100,
        placeholder="Main insight 1\nMain insight 2\nMain insight 3",
        help="The main takeaways from your newsletter",
        key="social_key_points"
    )
    key_points = [p.strip() for p in key_points_text.split('\n') if p.strip()]
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Generate Social Posts", type="primary", use_container_width=True, key="gen_social_posts"):
            if not headline:
                st.warning("Please enter a headline first")
            else:
                with st.spinner("Generating social media posts..."):
                    result = generate_social_posts(
                        headline=headline,
                        preview=preview,
                        newsletter_url=newsletter_url or "[YOUR_NEWSLETTER_URL]",
                        key_points=key_points
                    )
                    st.session_state['social_posts'] = result
    
    with col2:
        if st.button("Generate Twitter Thread", use_container_width=True, key="gen_twitter_thread"):
            if not headline:
                st.warning("Please enter a headline first")
            elif not current_content:
                st.warning("Generate a newsletter first in the Write tab")
            else:
                with st.spinner("Generating thread..."):
                    result = generate_thread_content(
                        headline=headline,
                        preview=preview,
                        content=current_content,
                        platform='twitter'
                    )
                    st.session_state['social_thread'] = result
    
    # Display generated posts
    if 'social_posts' in st.session_state:
        result = st.session_state['social_posts']
        
        if result.get('error'):
            st.error(f"Error: {result['error']}")
        else:
            posts = result.get('posts', {})
            
            st.markdown("### Generated Posts")
            st.caption("Click to copy, then paste into your social platform")
            
            if posts.get('twitter'):
                st.markdown("**Twitter/X**")
                st.code(posts['twitter'], language=None)
                st.caption(f"Characters: {len(posts['twitter'])}/280")
            
            if posts.get('linkedin'):
                st.markdown("**LinkedIn**")
                st.code(posts['linkedin'], language=None)
            
            if posts.get('threads'):
                st.markdown("**Threads**")
                st.code(posts['threads'], language=None)
            
            if posts.get('raw'):
                st.markdown("**Generated Content**")
                st.markdown(posts['raw'])
    
    # Display generated thread
    if 'social_thread' in st.session_state:
        result = st.session_state['social_thread']
        
        if result.get('error'):
            st.error(f"Error: {result['error']}")
        elif result.get('thread'):
            st.markdown("### Twitter/X Thread")
            st.caption("Copy each tweet to build your thread")
            
            for i, tweet in enumerate(result['thread'], 1):
                st.markdown(f"**Tweet {i}/{len(result['thread'])}**")
                st.code(tweet, language=None)
                if i < len(result['thread']):
                    st.caption("↓")


def render_performance_insights_subtab():
    """Render the performance insights subtab."""
    st.subheader("Performance Insights")
    st.markdown("*Trends and patterns from your newsletter history*")
    
    if not HAS_PUBLISHING:
        st.warning("Publishing analytics not available.")
        return
    
    try:
        trends = analyze_performance_trends()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Newsletters", trends.get('total_newsletters', 0))
        
        with col2:
            st.metric("Total Opens", f"{trends.get('total_opens', 0):,}")
        
        with col3:
            st.metric("Avg Open Rate", f"{trends.get('overall_avg', 0)*100:.1f}%")
        
        with col4:
            trend = trends.get('trend', 'unknown')
            trend_emoji = {'improving': 'Improving', 'stable': 'Stable', 'declining': 'Declining'}.get(trend, 'Unknown')
            st.metric("Trend", trend_emoji)
        
        st.info(trends.get('trend_description', 'Not enough data for trend analysis.'))
        
        # Insights
        st.markdown("### Key Insights")
        insights = trends.get('insights', [])
        if insights:
            for insight in insights:
                st.markdown(f"- {insight}")
        else:
            st.caption("Publish more newsletters to unlock insights.")
        
        # Top performers
        st.markdown("### Top Performing Newsletters")
        top_performers = trends.get('top_performers', [])
        
        if top_performers:
            for i, nl in enumerate(top_performers, 1):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    title = nl.get('title', 'Untitled')[:60]
                    st.markdown(f"**{i}. {title}**")
                
                with col2:
                    open_rate = nl.get('open_rate', 0)
                    st.markdown(f"{open_rate*100:.1f}%")
                
                with col3:
                    opens = nl.get('opens', 0)
                    st.markdown(f"{opens:,} opens")
        else:
            st.caption("No newsletter data available yet.")
        
        # Recent vs historical comparison
        st.markdown("### Recent vs Historical Performance")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Recent (last 5)",
                f"{trends.get('recent_avg', 0)*100:.1f}%",
                help="Average open rate of last 5 newsletters"
            )
        
        with col2:
            st.metric(
                "Historical",
                f"{trends.get('historical_avg', 0)*100:.1f}%",
                help="Average open rate of older newsletters"
            )
        
        with col3:
            recent = trends.get('recent_avg', 0)
            hist = trends.get('historical_avg', 0)
            if hist > 0:
                change = ((recent / hist) - 1) * 100
                st.metric("Change", f"{change:+.1f}%", help="How recent performance compares to historical")
            else:
                st.metric("Change", "N/A")
    
    except Exception as e:
        st.error(f"Error loading performance data: {e}")


def render_publishing_checklist_subtab():
    """Render the publishing checklist subtab."""
    st.subheader("Publishing Checklist")
    st.markdown("*Make sure you're ready to publish*")
    
    if not HAS_PUBLISHING:
        st.warning("Publishing analytics not available.")
        return
    
    # Get current newsletter data
    checklist_outline = st.session_state.get('generator_edited_outline') or {}
    newsletter_data = {
        'headline': checklist_outline.get('headline') if isinstance(checklist_outline, dict) else None,
        'preview': checklist_outline.get('preview') if isinstance(checklist_outline, dict) else None,
        'content': st.session_state.get('generator_final'),
        'image_url': st.session_state.get('generator_image_url')
    }
    
    checklist = get_publishing_checklist(newsletter_data)
    
    # Display checklist
    completed = 0
    for item in checklist:
        col1, col2 = st.columns([0.1, 0.9])
        
        with col1:
            key = f"checklist_{item['id']}_lib"
            is_complete = item['status'] == 'complete' or st.session_state.get(key, False)
            checked = st.checkbox("", value=is_complete, key=key, label_visibility="collapsed")
            if checked:
                completed += 1
        
        with col2:
            if checked:
                st.markdown(f"~~{item['title']}~~")
            else:
                st.markdown(f"**{item['title']}**")
            st.caption(item['description'])
    
    # Progress
    st.markdown("---")
    progress = completed / len(checklist) if checklist else 0
    st.progress(progress)
    st.caption(f"{completed}/{len(checklist)} items complete")
    
    if progress == 1.0:
        st.success("You're ready to publish!")
        st.balloons()
    elif progress >= 0.7:
        st.info("Almost there! Complete the remaining items before publishing.")
    else:
        st.warning("Complete more items before publishing.")


# ============================================================================
# Tab 6: Newsletter Bible
# ============================================================================

def render_bible_section():
    """Render the Newsletter Bible section (integrated into Settings tab)."""
    st.subheader("Newsletter Bible & Archive Patterns")
    st.markdown("*Your personalized guide to writing high-performing newsletters, learned from your archive*")
    
    # Source indicator
    render_source_indicator("Newsletter Bible", show_model=True, show_kb=False, show_bible=True, compact=True)
    
    # Load data
    df = load_data()
    bible = load_bible()
    
    # ==========================================================================
    # SECTION 1: Archive Statistics (from old Archive & Patterns tab)
    # ==========================================================================
    st.subheader("Archive Overview")
    
    if df.empty:
        st.warning("No newsletter data found. Please:")
        st.markdown("""
        1. Run the scraper first: `python scrape_substack.py`
        2. Add your performance stats to `data/newsletters_with_stats.csv`
        3. Refresh this page
        """)
        
        if st.button("Re-scrape Substack Archive"):
            with st.spinner("Scraping your Substack archive..."):
                posts = run_scraper(fetch_content=True)
                if posts:
                    st.success(f"Scraped {len(posts)} posts!")
                    refresh_data()
                    st.rerun()
                else:
                    st.error("No posts were scraped. Check the console for errors.")
    else:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Newsletters", len(df))
        
        with col2:
            if 'views' in df.columns:
                total_views = df['views'].sum() if df['views'].notna().any() else 0
                st.metric("Total Views", f"{total_views:,.0f}")
            else:
                st.metric("Total Views", "N/A")
        
        with col3:
            if 'open_rate' in df.columns and df['open_rate'].notna().any():
                avg_open = df['open_rate'].mean()
                st.metric("Avg Open Rate", f"{avg_open:.1%}")
            else:
                st.metric("Avg Open Rate", "N/A")
        
        with col4:
            if 'open_rate' in df.columns and df['open_rate'].notna().any():
                max_open = df['open_rate'].max()
                st.metric("Best Open Rate", f"{max_open:.1%}")
            else:
                st.metric("Best Open Rate", "N/A")
    
    st.divider()
    
    # ==========================================================================
    # SECTION 2: Newsletter Bible (learned patterns)
    # ==========================================================================
    st.subheader("Your Style Bible")
    
    if not bible:
        st.warning("Newsletter Bible not generated yet.")
        if st.button("Generate Newsletter Bible", type="primary"):
            with st.spinner("Analyzing all your newsletters to build the Bible..."):
                regenerate_bible()
            st.success("Newsletter Bible generated!")
            st.rerun()
    else:
        st.success(f"Based on analysis of **{bible.get('meta', {}).get('newsletters_analyzed', 0)}** newsletters")
        
        # Three column layout for Bible
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("##### Headline Formulas")
            st.markdown(f"**Optimal Length:** {bible.get('headline_formulas', {}).get('optimal_length', 'N/A')}")
            
            st.markdown("**Pattern Breakdown:**")
            patterns = bible.get('headline_formulas', {}).get('pattern_breakdown', {})
            for pattern_name, data in patterns.items():
                pct = data.get('percentage', 0)
                if pct > 5:
                    st.markdown(f"• {pattern_name.replace('_', ' ').title()}: **{pct:.0f}%**")
            
            st.markdown("**Top Opening Words:**")
            opening_words = bible.get('headline_formulas', {}).get('opening_words_that_work', {})
            top_words = list(opening_words.items())[:8]
            for word, count in top_words:
                st.markdown(f"• \"{word.title()}\" ({count}x)")
        
        with col2:
            st.markdown("##### 🎤 Your Voice")
            
            st.markdown("**Voice Characteristics:**")
            for trait in bible.get('writing_voice', {}).get('characteristics', []):
                st.markdown(f"• {trait}")
            
            st.markdown("**Sentence Style:**")
            sentence = bible.get('writing_voice', {}).get('sentence_style', {})
            st.markdown(f"• Average length: {sentence.get('avg_length', 'N/A')}")
            st.markdown(f"• {sentence.get('punchy_short_sentences', 'N/A')}")
            
            st.markdown("**Signature Vocabulary:**")
            vocab = bible.get('writing_voice', {}).get('signature_vocabulary', [])[:15]
            st.markdown(", ".join(f"*{w}*" for w in vocab))
        
        with col3:
            st.markdown("##### 📐 Structure")
            
            structure = bible.get('structure_blueprint', {})
            st.markdown(f"**Target Length:** {structure.get('typical_length', 'N/A')}")
            st.markdown(f"**Avg Word Count:** {structure.get('avg_word_count', 0):.0f} words")
            
            sections = structure.get('sections', {})
            st.markdown(f"**H2 Sections:** {sections.get('avg_h2_sections', 0):.1f} per newsletter")
            
            elements = structure.get('elements', {})
            st.markdown(f"**Avg Paragraphs:** {elements.get('avg_paragraphs', 0):.0f}")
            st.markdown(f"**Avg Links:** {elements.get('avg_links', 0):.0f}")
        
        st.divider()
        
        # Rules for Success
        st.markdown("##### Rules for Success")
        rules = bible.get('rules_for_success', [])
        
        rules_col1, rules_col2 = st.columns(2)
        half = len(rules) // 2 + 1
        
        with rules_col1:
            for rule in rules[:half]:
                st.markdown(f"✓ {rule}")
        
        with rules_col2:
            for rule in rules[half:]:
                st.markdown(f"✓ {rule}")
        
        st.divider()
        
        # Headline Examples by Type
        st.markdown("##### Headline Examples by Type")
        
        examples = bible.get('headline_formulas', {}).get('examples_by_type', {})
        
        example_cols = st.columns(3)
        example_items = list(examples.items())
        
        for i, (headline_type, headlines) in enumerate(example_items):
            if headlines:
                with example_cols[i % 3]:
                    st.markdown(f"**{headline_type.replace('_', ' ').title()}:**")
                    for h in headlines[:3]:
                        st.markdown(f"• {h}")
    
    st.divider()
    
    # ==========================================================================
    # SECTION 3: Pattern Insights (from old Archive & Patterns tab)
    # ==========================================================================
    if not df.empty:
        st.subheader("Pattern Insights")
        
        left_col, right_col = st.columns([2, 1])
        
        with left_col:
            st.markdown("##### All Newsletters")
            
            # Prepare display columns
            display_cols = ['title', 'date']
            if 'views' in df.columns:
                display_cols.append('views')
            if 'open_rate' in df.columns:
                display_cols.append('open_rate')
            if 'headline_word_count' in df.columns:
                display_cols.append('headline_word_count')
            if 'primary_topic' in df.columns:
                display_cols.append('primary_topic')
            
            # Filter available columns
            display_cols = [c for c in display_cols if c in df.columns]
            
            # Sort by date if available
            display_df = df[display_cols].copy()
            if 'date' in display_df.columns:
                display_df = display_df.sort_values('date', ascending=False)
            
            # Format open_rate as percentage
            if 'open_rate' in display_df.columns:
                display_df['open_rate'] = display_df['open_rate'].apply(
                    lambda x: f"{x:.1%}" if pd.notna(x) else "N/A"
                )
            
            st.dataframe(display_df, use_container_width=True, height=400)
        
        with right_col:
            st.markdown("##### Performance Patterns")
            
            if 'open_rate' not in df.columns or df['open_rate'].isna().all():
                st.info("Add performance data to see pattern insights")
            else:
                correlations = describe_feature_correlations(df)
                
                # Question marks
                if 'has_question_mark' in correlations:
                    q_data = correlations['has_question_mark']
                    diff = q_data.get('difference', 0)
                    if diff > 0:
                        st.success(f"❓ Questions: +{diff:.1%} open rate")
                    elif diff < 0:
                        st.warning(f"❓ Questions: {diff:.1%} open rate")
                
                # Colons
                if 'has_colon' in correlations:
                    c_data = correlations['has_colon']
                    diff = c_data.get('difference', 0)
                    if diff > 0:
                        st.success(f"Colons: +{diff:.1%} open rate")
                    elif diff < 0:
                        st.warning(f"Colons: {diff:.1%} open rate")
                
                # Numbers
                if 'starts_with_number' in correlations:
                    n_data = correlations['starts_with_number']
                    diff = n_data.get('difference', 0)
                    if diff > 0:
                        st.success(f"🔢 Numbers: +{diff:.1%} open rate")
                    elif diff < 0:
                        st.warning(f"🔢 Numbers: {diff:.1%} open rate")
                
                # AI terms
                if 'contains_ai_term' in correlations:
                    ai_data = correlations['contains_ai_term']
                    diff = ai_data.get('difference', 0)
                    if diff > 0:
                        st.success(f"AI terms: +{diff:.1%} open rate")
                
                st.divider()
                
                # Topic breakdown
                if 'primary_topic' in correlations:
                    st.markdown("**Open Rate by Topic:**")
                    topic_data = correlations['primary_topic']
                    for topic, rate in sorted(topic_data.items(), key=lambda x: x[1], reverse=True):
                        st.markdown(f"• {topic}: {rate:.1%}")
                
                # Headline length
                if 'headline_length_bucket' in correlations:
                    st.divider()
                    st.markdown("**Open Rate by Headline Length:**")
                    length_data = correlations['headline_length_bucket']
                    for bucket, rate in sorted(length_data.items()):
                        st.markdown(f"• {bucket}: {rate:.1%}")
        
        st.divider()
        
        # Charts section
        st.markdown("##### Visualizations")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            if 'primary_topic' in df.columns and 'open_rate' in df.columns:
                topic_avg = df.groupby('primary_topic')['open_rate'].mean().sort_values(ascending=True)
                if not topic_avg.empty:
                    st.markdown("**Average Open Rate by Topic**")
                    st.bar_chart(topic_avg)
        
        with chart_col2:
            if 'headline_length_bucket' in df.columns and 'open_rate' in df.columns:
                length_avg = df.groupby('headline_length_bucket')['open_rate'].mean()
                if not length_avg.empty:
                    st.markdown("**Average Open Rate by Headline Length**")
                    st.bar_chart(length_avg)
    
    st.divider()
    
    # Action buttons
    action_col1, action_col2 = st.columns(2)
    
    with action_col1:
        if st.button("Regenerate Bible (re-analyze all newsletters)"):
            with st.spinner("Re-analyzing all newsletters..."):
                regenerate_bible()
            st.success("Newsletter Bible regenerated!")
            st.rerun()
    
    with action_col2:
        if not df.empty:
            if st.button("Re-scrape Substack Archive"):
                with st.spinner("Scraping your Substack archive..."):
                    posts = run_scraper(fetch_content=True)
                    if posts:
                        st.success(f"Scraped {len(posts)} posts!")
                        refresh_data()
                        st.rerun()
                    else:
                        st.error("No posts were scraped. Check the console for errors.")


# ============================================================================
# Tab 5: Newsletter Generator (Multi-Step Workflow with Metric Dials)
# ============================================================================

# Metric categories for display grouping
METRIC_CATEGORIES = {
    'tone': {
        'name': '🎭 Tone & Emotion',
        'description': 'Control the emotional feel of your newsletter'
    },
    'style': {
        'name': '✍️ Writing Style',
        'description': 'Adjust how you write, not what you write'
    },
    'depth': {
        'name': 'Research & Depth',
        'description': 'How deep into the weeds should we go?'
    },
    'practical': {
        'name': '🛠️ Practicality',
        'description': 'How actionable should the content be?'
    },
    'geographic': {
        'name': 'Geographic Focus',
        'description': 'Regional perspectives and angles'
    },
    'industry': {
        'name': 'Industry Focus',
        'description': 'Journalism, regulation, and media industry'
    },
    'engagement': {
        'name': '📣 Engagement Style',
        'description': 'How to engage your readers'
    },
    'structure': {
        'name': '📐 Structure',
        'description': 'Newsletter formatting and organization'
    },
}


def render_generator_tab():
    """Render the Newsletter Generator tab with multi-step outline workflow + metric dials."""
    st.header("Newsletter Generator")
    st.markdown("*Step-by-step newsletter creation with 22 style dials trained on your data*")
    
    # Source indicator - shows what powers this feature
    render_source_indicator("Newsletter Generation", show_model=True, show_kb=True, show_bible=True, compact=False)
    
    # Show work-in-progress status
    if has_work_in_progress():
        wip = get_work_summary()
        with st.container():
            col_wip1, col_wip2 = st.columns([4, 1])
            with col_wip1:
                st.info(f"**Work in progress:** {wip['stage_icon']} {wip['stage'].title()} - *\"{wip['idea_preview']}\"*" if wip['idea_preview'] else f"**Work in progress:** {wip['stage_icon']} {wip['stage'].title()}")
            with col_wip2:
                if st.button("Clear", key="clear_wip", help="Start fresh"):
                    clear_and_reset_streamlit(st)
                    st.rerun()
    
    # Check if Bible exists
    bible = load_bible()
    if not bible:
        st.warning("Newsletter Bible required for generation")
        st.markdown("The generator needs to learn your style first.")
        if st.button("Generate Newsletter Bible First", type="primary"):
            with st.spinner("Analyzing your newsletters..."):
                regenerate_bible()
            st.success("Done! Now you can generate newsletters.")
            st.rerun()
        return
    
    # Check API
    connected, msg = check_api_connection()
    if not connected:
        st.error(f"OpenAI API required: {msg}")
        st.markdown("Set `OPENAI_API_KEY` in your `.env` file")
        return
    
    # Load advanced metrics analysis
    metrics_analysis = load_analysis()
    metric_definitions = get_metric_definitions()
    
    if not metrics_analysis:
        st.warning("Advanced metrics not yet analyzed.")
        if st.button("Run Advanced Metrics Analysis", type="primary"):
            with st.spinner("Analyzing 22 content metrics across all newsletters..."):
                run_metrics_analysis()
            st.success("Analysis complete!")
            st.rerun()
        return
    
    # Initialize session state for the workflow
    if 'generator_step' not in st.session_state:
        st.session_state.generator_step = 1
    if 'generator_idea' not in st.session_state:
        st.session_state.generator_idea = ""
    if 'generator_outline' not in st.session_state:
        st.session_state.generator_outline = None
    if 'generator_edited_outline' not in st.session_state:
        st.session_state.generator_edited_outline = None
    if 'generator_final' not in st.session_state:
        st.session_state.generator_final = None
    if 'generator_prompt' not in st.session_state:
        st.session_state.generator_prompt = None  # The AI-generated meticulous prompt
    if 'generator_prompt_edited' not in st.session_state:
        st.session_state.generator_prompt_edited = None  # User's edited version
    if 'generator_metrics' not in st.session_state:
        # Initialize with your average values
        st.session_state.generator_metrics = {
            key: int(metrics_analysis.get('metrics', {}).get(key, {}).get('mean', 50))
            for key in metric_definitions.keys()
        }
    
    # Show current step
    step = st.session_state.generator_step
    
    # Progress indicator with CLICKABLE navigation - 5 steps now
    st.markdown("#### Workflow")
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns(5)
    
    with nav_col1:
        is_current = step == 1
        step1_label = ">>> 1 <<<" if is_current else ("1 ✓" if step > 1 else "1")
        step1_enabled = True
        btn_type = "primary" if is_current else "secondary"
        if st.button(step1_label, key="nav_step1", disabled=not step1_enabled, use_container_width=True, type=btn_type):
            st.session_state.generator_step = 1
            st.rerun()
        st.caption("**Idea**" if is_current else "Idea")
    
    with nav_col2:
        is_current = step == 2
        step2_label = ">>> 2 <<<" if is_current else ("2 ✓" if step > 2 else "2")
        step2_enabled = step >= 2 or st.session_state.get('generator_outline') is not None
        btn_type = "primary" if is_current else "secondary"
        if st.button(step2_label, key="nav_step2", disabled=not step2_enabled, use_container_width=True, type=btn_type):
            if st.session_state.get('generator_outline'):
                st.session_state.generator_step = 2
                st.rerun()
        st.caption("**Outline**" if is_current else "Outline")
    
    with nav_col3:
        is_current = step == 3
        step3_label = ">>> 3 <<<" if is_current else ("3 ✓" if step > 3 else "3")
        step3_enabled = step >= 3 or st.session_state.get('generator_prompt') is not None
        btn_type = "primary" if is_current else "secondary"
        if st.button(step3_label, key="nav_step3", disabled=not step3_enabled, use_container_width=True, type=btn_type):
            if st.session_state.get('generator_prompt'):
                st.session_state.generator_step = 3
                st.rerun()
        st.caption("**Prompt**" if is_current else "Prompt")
    
    with nav_col4:
        is_current = step == 4
        step4_label = ">>> 4 <<<" if is_current else ("4 ✓" if step > 4 else "4")
        step4_enabled = step >= 4 or st.session_state.get('generator_final') is not None
        btn_type = "primary" if is_current else "secondary"
        if st.button(step4_label, key="nav_step4", disabled=not step4_enabled, use_container_width=True, type=btn_type):
            if st.session_state.get('generator_final'):
                st.session_state.generator_step = 4
                st.rerun()
        st.caption("**Newsletter**" if is_current else "Newsletter")
    
    with nav_col5:
        is_current = step == 5
        step5_label = ">>> 5 <<<" if is_current else ("5 ✓" if step > 5 else "5")
        step5_enabled = step >= 5 or st.session_state.get('generator_final') is not None
        btn_type = "primary" if is_current else "secondary"
        if st.button(step5_label, key="nav_step5", disabled=not step5_enabled, use_container_width=True, type=btn_type):
            if st.session_state.get('generator_final'):
                st.session_state.generator_step = 5
                st.rerun()
        st.caption("**Image**" if is_current else "Image")
    
    st.divider()
    
    # Load section templates
    section_analysis = load_section_analysis()
    section_templates = get_section_templates()
    
    # Initialize section state
    if 'generator_sections' not in st.session_state:
        st.session_state.generator_sections = []
    
    # =========================================
    # STEP 1: Enter Idea & Set Metric Dials & Select Sections
    # =========================================
    if step == 1:
        st.subheader("Step 1: Your Newsletter Idea, Sections & Style")
        
        # Get story types
        story_types = get_story_type_list()
        valid_story_type_keys = [stype['key'] for stype in story_types]
        
        # Initialize story type state (validate existing value)
        if 'generator_story_type' not in st.session_state or st.session_state.generator_story_type not in valid_story_type_keys:
            st.session_state.generator_story_type = 'news_analysis'
        
        # Initialize image state
        if 'generator_images' not in st.session_state:
            st.session_state.generator_images = []
        
        # ====================
        # SECTION 1: YOUR IDEA
        # ====================
        st.markdown("### What's your newsletter about?")
        
        # =====================
        # SAVED IDEAS BANK - Show prominently at the top
        # =====================
        saved_ideas = load_saved_ideas()
        unused_saved_ideas = get_unused_ideas()
        
        if saved_ideas:
            ideas_label = f"Your Ideas Bank ({len(unused_saved_ideas)} unused / {len(saved_ideas)} total)"
            with st.expander(ideas_label, expanded=len(unused_saved_ideas) > 0):
                if unused_saved_ideas:
                    st.markdown("**Ready to use:**")
                    for idx, saved in enumerate(unused_saved_ideas[:10]):  # Show max 10
                        with st.container():
                            col_idea, col_actions = st.columns([4, 1])
                            
                            with col_idea:
                                st.markdown(f"**{saved.get('title', 'Untitled')}**")
                                story_type = saved.get('story_type', 'general')
                                saved_date = saved.get('saved_at', '')[:10] if saved.get('saved_at') else ''
                                st.caption(f"{story_type.replace('_', ' ').title()} | Saved: {saved_date}")
                                
                                if saved.get('summary'):
                                    st.markdown(f"*{saved.get('summary', '')[:200]}...*" if len(saved.get('summary', '')) > 200 else f"*{saved.get('summary', '')}*")
                                
                                if saved.get('angle'):
                                    st.markdown(f"**Angle:** {saved.get('angle')}")
                                
                                # Show sources count
                                sources = saved.get('sources', [])
                                if sources:
                                    st.caption(f"{len(sources)} sources attached")
                            
                            with col_actions:
                                if st.button("Use This", key=f"use_saved_{saved.get('id', idx)}", use_container_width=True, type="primary"):
                                    # Load into generator
                                    st.session_state.generator_idea = saved.get('title', '') + "\n\n" + saved.get('summary', '')
                                    if saved.get('angle'):
                                        st.session_state.generator_idea += f"\n\nAngle: {saved['angle']}"
                                    st.session_state.generator_story_type = saved.get('story_type', 'news_analysis')
                                    st.session_state.generator_idea_sources = saved.get('sources', [])
                                    st.session_state.current_idea_id = saved.get('id')
                                    
                                    # Clear old outline data when loading a new idea
                                    st.session_state.generator_outline = None
                                    st.session_state.generator_edited_outline = None
                                    st.session_state.generator_step = 1  # Reset to step 1
                                    
                                    # Mark as used
                                    mark_idea_used(saved.get('id'))
                                    
                                    # Add sources to knowledge base
                                    sources = saved.get('sources', [])
                                    if sources and HAS_KNOWLEDGE_BASE:
                                        for source in sources:
                                            if isinstance(source, dict) and source.get('url'):
                                                try:
                                                    add_article(
                                                        title=source.get('title', 'Untitled'),
                                                        url=source.get('url'),
                                                        source=source.get('publication', 'Unknown'),
                                                        published=source.get('date', ''),
                                                        category='idea_source'
                                                    )
                                                except:
                                                    pass
                                    st.rerun()
                                
                                if st.button("Delete", key=f"del_saved_{saved.get('id', idx)}", use_container_width=True):
                                    delete_saved_idea(saved.get('id'))
                                    st.rerun()
                            
                            st.divider()
                else:
                    st.info("All saved ideas have been used. You can reuse them below!")
                
                # Show used ideas - allow reusing them
                used_ideas = [i for i in saved_ideas if i.get('used')]
                if used_ideas:
                    st.markdown("---")
                    st.markdown(f"**Previously used ({len(used_ideas)}) - You can reuse these:**")
                    for idx, used in enumerate(used_ideas[:10]):  # Show max 10
                        with st.container():
                            col_idea, col_actions = st.columns([4, 1])
                            
                            with col_idea:
                                st.markdown(f"**{used.get('title', 'Untitled')}**")
                                story_type = used.get('story_type', 'general')
                                saved_date = used.get('saved_at', '')[:10] if used.get('saved_at') else ''
                                used_date = used.get('used_at', '')[:10] if used.get('used_at') else ''
                                date_info = f"Saved: {saved_date}"
                                if used_date:
                                    date_info += f" | Used: {used_date}"
                                st.caption(f"{story_type.replace('_', ' ').title()} | {date_info}")
                                
                                if used.get('summary'):
                                    st.markdown(f"*{used.get('summary', '')[:200]}...*" if len(used.get('summary', '')) > 200 else f"*{used.get('summary', '')}*")
                                
                                if used.get('angle'):
                                    st.markdown(f"**Angle:** {used.get('angle')}")
                                
                                # Show sources count
                                sources = used.get('sources', [])
                                if sources:
                                    st.caption(f"{len(sources)} sources attached")
                            
                            with col_actions:
                                if st.button("Use This", key=f"use_used_{used.get('id', idx)}", use_container_width=True, type="secondary"):
                                    # Load into generator
                                    st.session_state.generator_idea = used.get('title', '') + "\n\n" + used.get('summary', '')
                                    if used.get('angle'):
                                        st.session_state.generator_idea += f"\n\nAngle: {used['angle']}"
                                    st.session_state.generator_story_type = used.get('story_type', 'news_analysis')
                                    st.session_state.generator_idea_sources = used.get('sources', [])
                                    st.session_state.current_idea_id = used.get('id')
                                    
                                    # Clear old outline data when loading a new idea
                                    st.session_state.generator_outline = None
                                    st.session_state.generator_edited_outline = None
                                    st.session_state.generator_step = 1  # Reset to step 1
                                    
                                    # Update the used_at timestamp (idea is already marked as used)
                                    mark_idea_used(used.get('id'))
                                    
                                    # Add sources to knowledge base (if not already added)
                                    sources = used.get('sources', [])
                                    if sources and HAS_KNOWLEDGE_BASE:
                                        for source in sources:
                                            if isinstance(source, dict) and source.get('url'):
                                                try:
                                                    add_article(
                                                        title=source.get('title', 'Untitled'),
                                                        url=source.get('url'),
                                                        source=source.get('publication', 'Unknown'),
                                                        published=source.get('date', ''),
                                                        category='idea_source'
                                                    )
                                                except:
                                                    pass
                                    st.rerun()
                                
                                if st.button("Delete", key=f"del_used_{used.get('id', idx)}", use_container_width=True):
                                    delete_saved_idea(used.get('id'))
                                    st.rerun()
                            
                            st.divider()
        else:
            st.info("No saved ideas yet. Go to **Ideas** tab to generate and save ideas!")
        
        st.markdown("---")
        
        # Check if there's inbox content to help
        inbox_items = load_inbox()
        unused_inbox = [i for i in inbox_items if not i.get('used')]
        
        if unused_inbox:
            with st.expander(f"{len(unused_inbox)} items in your Content Inbox - Get AI ideas", expanded=False):
                if st.button("Generate Ideas from Inbox Content", key="gen_ideas_inbox"):
                    with st.spinner("Analyzing inbox content and generating ideas..."):
                        ideas_result = generate_ideas_from_inbox(
                            story_type=st.session_state.generator_story_type
                        )
                    
                    if ideas_result.get('error'):
                        st.error(ideas_result['error'])
                    elif ideas_result.get('ideas'):
                        st.success(f"Generated {len(ideas_result['ideas'])} ideas from {ideas_result['source_count']} inbox items!")
                        for idea_item in ideas_result['ideas']:
                            with st.container():
                                st.markdown(f"**{idea_item.get('title', 'Untitled')}**")
                                st.caption(f"{idea_item.get('story_type', '')} | {idea_item.get('angle', '')}")
                                st.markdown(idea_item.get('summary', ''))
                                if st.button(f"Use this idea", key=f"use_idea_{idea_item.get('title', '')[:20]}"):
                                    st.session_state.generator_idea = f"{idea_item.get('title', '')}\n\n{idea_item.get('summary', '')}\n\nAngle: {idea_item.get('angle', '')}"
                                    # Clear old outline data when loading a new idea
                                    st.session_state.generator_outline = None
                                    st.session_state.generator_edited_outline = None
                                    st.session_state.generator_step = 1  # Reset to step 1
                                    st.rerun()
                                st.divider()
        
        st.markdown("**Or write your own idea:**")
        
        idea = st.text_area(
            "Describe your main topic/story in detail",
            value=st.session_state.get('generator_idea', ''),
            placeholder="e.g., The rise of AI-generated news anchors in Africa and what it means for journalism jobs. Could cover Zimbabwe's recent AI newsreader, concerns about job displacement, but also potential benefits for under-resourced newsrooms...",
            height=120,
            key="idea_input"
        )
        # Sync idea to session state and persist
        if idea != st.session_state.get('generator_idea', ''):
            st.session_state.generator_idea = idea
            sync_from_streamlit(st)
        
        # Show sources if carried over from Idea Generator
        idea_sources = st.session_state.get('generator_idea_sources', [])
        if idea_sources:
            with st.expander(f"**{len(idea_sources)} Sources** (from Idea Generator - added to Knowledge Base)", expanded=True):
                for source in idea_sources:
                    if isinstance(source, dict):
                        url = source.get('url', '')
                        title = source.get('title', 'Source')
                        pub = source.get('publication', '')
                        date = source.get('date', '')
                        
                        source_text = f"**{title}**"
                        if pub:
                            source_text += f" - *{pub}*"
                        if date:
                            source_text += f" ({date})"
                        if url:
                            source_text += f" | [Link]({url})"
                        st.markdown(f"• {source_text}")
                
                if st.button("Clear Sources", key="clear_idea_sources"):
                    st.session_state.generator_idea_sources = []
                    st.rerun()
        
        additional_context = st.text_input(
            "Any specific angle or focus? (optional)",
            value=st.session_state.get('generator_angle', ''),
            placeholder="e.g., Focus on Africa, make it practical, be provocative",
            key="angle_input"
        )
        # Sync angle to session state and persist
        if additional_context != st.session_state.get('generator_angle', ''):
            st.session_state.generator_angle = additional_context
            sync_from_streamlit(st)
        
        st.divider()
        
        # ====================
        # SECTION 2: STORY TYPE
        # ====================
        st.markdown("### Main Story Type")
        st.caption("What kind of story is this? This influences headline style, tone, and structure.")
        
        # Create radio options with details
        story_type_options = {stype['key']: f"{stype['icon']} {stype['name']}" for stype in story_types}
        
        selected_story_type = st.radio(
            "Select the primary story type:",
            options=list(story_type_options.keys()),
            format_func=lambda x: story_type_options[x],
            index=list(story_type_options.keys()).index(st.session_state.generator_story_type),
            key="story_type_radio",
            horizontal=True
        )
        # Sync and persist story type
        if selected_story_type != st.session_state.get('generator_story_type'):
            st.session_state.generator_story_type = selected_story_type
            sync_from_streamlit(st)
        st.session_state.generator_story_type = selected_story_type
        
        # Show details for selected type in compact form
        selected_type_data = next((stype for stype in story_types if stype['key'] == selected_story_type), None)
        if selected_type_data:
            st.info(f"**{selected_type_data['description']}** | Impact: {selected_type_data['open_rate_impact']}")
        
        st.divider()
        
        # ====================
        # SECTION 3: EXTRA SECTIONS (Optional)
        # ====================
        st.markdown("### Extra Sections (Optional)")
        st.caption("Your main story is always included. Add extra sections if you want them.")
        
        # Option for no extra sections
        no_extras = st.checkbox(
            "**Main story only** (no extra sections)",
            value=len(st.session_state.generator_sections) == 0,
            key="no_extra_sections"
        )
        
        if no_extras:
            st.session_state.generator_sections = []
            st.info("Your newsletter will contain only the main story based on your idea and story type above.")
        else:
            # Clear all / Select common
            action_col1, action_col2 = st.columns(2)
            with action_col1:
                if st.button("Clear All", use_container_width=True, key="clear_sections"):
                    st.session_state.generator_sections = []
                    st.rerun()
            with action_col2:
                if st.button("Select Common", use_container_width=True, key="select_common"):
                    st.session_state.generator_sections = [
                        t for t in section_templates 
                        if t['key'] in ['news_roundup', 'tools_and_tips', 'closing_signoff']
                    ]
                    st.rerun()
            
            st.markdown("---")
            
            # Section checkboxes in columns - sorted by frequency
            selected_sections = []
            sorted_templates = sorted(section_templates, key=lambda x: x['frequency'], reverse=True)
            
            sec_col1, sec_col2, sec_col3 = st.columns(3)
            third = len(sorted_templates) // 3 + 1
            
            for col, templates_slice in zip(
                [sec_col1, sec_col2, sec_col3],
                [sorted_templates[:third], sorted_templates[third:third*2], sorted_templates[third*2:]]
            ):
                with col:
                    for template in templates_slice:
                        key = template['key']
                        icon = template['icon']
                        name = template['name']
                        freq = template['frequency']
                        
                        # Check if already selected
                        is_selected = key in [s['key'] for s in st.session_state.generator_sections]
                        
                        if st.checkbox(
                            f"{icon} {name} ({freq})",
                            value=is_selected,
                            key=f"section_{key}"
                        ):
                            if template not in selected_sections:
                                selected_sections.append(template)
            
            st.session_state.generator_sections = selected_sections
        
        # Show count
        section_count = len(st.session_state.generator_sections)
        if section_count > 0:
            st.caption(f"**{section_count} extra section(s)** selected")
        
        st.divider()
        
        # ====================
        # SECTION 4: STYLE & IMAGES (Collapsible)
        # ====================
        with st.expander("Style Dials & Images (Advanced)", expanded=False):
            style_col, image_col = st.columns(2)
            
            with style_col:
                st.markdown("#### Style Dials")
                st.caption("Adjust tone and style metrics")
                
                # Show just the most impactful dials
                recommendations = metrics_analysis.get('recommendations', [])
                
                for rec in recommendations[:6]:
                    metric_key = rec['metric']
                    if metric_key in metric_definitions:
                        metric_def = metric_definitions[metric_key]
                        avg_val = metrics_analysis.get('metrics', {}).get(metric_key, {}).get('mean', 50)
                        current_val = st.session_state.generator_metrics.get(metric_key, int(avg_val))
                        
                        impact = f"{'' if rec['direction'] == 'positive' else '📉'} {rec['impact']}"
                        
                        new_val = st.slider(
                            f"{metric_def['name']} {impact}",
                            min_value=0,
                            max_value=100,
                            value=current_val,
                            key=f"metric_{metric_key}",
                        )
                        st.session_state.generator_metrics[metric_key] = new_val
            
            with image_col:
                st.markdown("#### Newsletter Image")
                image_services = check_image_services()
                
                if image_services['dalle']:
                    st.success("✓ DALL-E 3 ready")
                    
                    # Initialize image prompt state
                    if 'generator_image_prompt' not in st.session_state:
                        st.session_state.generator_image_prompt = ""
                    if 'image_prompt_suggestions' not in st.session_state:
                        st.session_state.image_prompt_suggestions = []
                    
                    # Generate suggestions
                    if idea and st.button("Get AI Image Suggestions", key="gen_img_suggestions"):
                        with st.spinner("Generating prompt ideas..."):
                            prompts = suggest_image_prompts(idea, selected_story_type)
                            st.session_state.image_prompt_suggestions = prompts
                    
                    # Show suggestions as selectable options
                    if st.session_state.image_prompt_suggestions:
                        st.markdown("**Select a prompt:**")
                        for i, prompt in enumerate(st.session_state.image_prompt_suggestions):
                            if st.button(f"📷 {prompt[:60]}...", key=f"select_img_prompt_{i}", use_container_width=True):
                                st.session_state.generator_image_prompt = prompt
                                st.rerun()
                    
                    # Custom prompt input
                    custom_prompt = st.text_area(
                        "Or write your own prompt:",
                        value=st.session_state.generator_image_prompt,
                        height=80,
                        key="custom_image_prompt",
                        placeholder="e.g., African journalist using AI tools in a modern newsroom, editorial photography style"
                    )
                    if custom_prompt != st.session_state.generator_image_prompt:
                        st.session_state.generator_image_prompt = custom_prompt
                    
                    # Preview generation (optional in Step 1)
                    if st.session_state.generator_image_prompt:
                        st.caption(f"📷 Image will be generated with newsletter")
                        if st.button("Preview Image Now", key="preview_image_now"):
                            with st.spinner("Generating preview (15-30 seconds)..."):
                                result = generate_image_dalle(
                                    prompt=st.session_state.generator_image_prompt,
                                    size="1024x1024",
                                    quality="standard"
                                )
                                if result.get('url'):
                                    st.image(result['url'], caption="Preview (will regenerate at full size)")
                                    st.caption(f"Revised: {result.get('revised_prompt', '')[:100]}...")
                                else:
                                    st.error(result.get('error', 'Generation failed'))
                else:
                    st.info("Add OPENAI_API_KEY to enable DALL-E")
        
        st.divider()
        
        # ====================
        # DATA RECOMMENDATIONS
        # ====================
        st.markdown("### Data-Driven Recommendations")
        recommendations = metrics_analysis.get('recommendations', [])
        
        rec_col1, rec_col2 = st.columns(2)
        with rec_col1:
            for rec in recommendations[:3]:
                emoji = "" if rec['direction'] == 'positive' else ""
                st.markdown(f"{emoji} **{rec['name']}**: {rec['impact']}")
        with rec_col2:
            for rec in recommendations[3:6]:
                emoji = "" if rec['direction'] == 'positive' else ""
                st.markdown(f"{emoji} **{rec['name']}**: {rec['impact']}")
        
        st.divider()
        
        # Summary of selections
        st.markdown("### Summary")
        sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
        
        with sum_col1:
            selected_type = next((stype for stype in story_types if stype['key'] == st.session_state.generator_story_type), {})
            st.metric("Story Type", selected_type.get('icon', ''))
        with sum_col2:
            st.metric("Sections", len(st.session_state.generator_sections))
        with sum_col3:
            high_metrics = sum(1 for v in st.session_state.generator_metrics.values() if v > 70)
            st.metric("High Dials", high_metrics)
        with sum_col4:
            st.metric("Images", len(st.session_state.generator_images))
        
        # Generate button
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            # Check if idea has actual content (not just whitespace)
            # Require at least 10 characters to ensure it's a real idea
            idea_trimmed = idea.strip() if idea else ""
            can_generate = len(idea_trimmed) >= 10
            if st.button("Generate Outline with These Settings", type="primary", use_container_width=True, disabled=not can_generate):
                st.session_state.generator_idea = idea
                
                # Clear edited outline so it gets reinitialized with sources from the idea
                st.session_state.generator_edited_outline = None
                
                # Build story type instructions
                story_type_data = next((stype for stype in story_types if stype['key'] == st.session_state.generator_story_type), {})
                story_type_instructions = build_story_type_instructions(story_type_data)
                
                # Build metric instructions from dial settings
                metric_instructions = build_metric_instructions(
                    st.session_state.generator_metrics,
                    metric_definitions,
                    metrics_analysis
                )
                
                # Build section instructions
                section_instructions = build_section_instructions(st.session_state.generator_sections)
                
                # Combine all instructions
                all_instructions = f"""{additional_context}

{story_type_instructions}

{section_instructions}

{metric_instructions}"""
                
                style_model, is_fine_tuned = get_active_model_display()
                model_display = style_model if is_fine_tuned else "gpt-4o-mini"
                
                with st.spinner(f"Generating outline with `{model_display}`... (30-45 seconds)"):
                    result = generate_newsletter(
                        idea=idea,
                        format_type="outline",
                        additional_instructions=all_instructions,
                        temperature=0.8
                    )
                
                if result.get('error'):
                    st.error(f"Generation failed: {result['error']}")
                elif result.get('outline'):
                    # Store the fresh outline and RESET any previous edited_outline
                    st.session_state.generator_outline = result['outline']
                    st.session_state.generator_edited_outline = None
                    st.session_state.generator_step = 2
                    # Persist the outline
                    sync_from_streamlit(st)
                    st.rerun()
                else:
                    st.error("Failed to generate outline. Please try again.")
            
            if not can_generate:
                # Only the main idea is required to generate an outline.
                # Extra sections are optional (you can run with main story only).
                if not idea or not idea.strip():
                    st.caption("⚠️ **Enter an idea in the text area above** (at least 10 characters). Extra sections are optional.")
                    st.caption(f"💡 Debug: Idea length = {len(idea) if idea else 0} characters")
                elif len(idea_trimmed) < 10:
                    st.caption(f"⚠️ **Your idea is too short** ({len(idea_trimmed)} characters). Please enter at least 10 characters to generate an outline.")
                else:
                    st.caption("Enter an idea above to generate your outline. Extra sections are optional.")
        
        with col2:
            # Save idea as draft (before generating outline)
            can_save = idea and len(idea) > 10
            if st.button("Save Idea", use_container_width=True, disabled=not can_save):
                try:
                    saved = create_newsletter(
                        idea=idea,
                        headline=f"[IDEA] {idea[:50]}...",
                        story_type=st.session_state.get('generator_story_type', ''),
                        sections=st.session_state.get('generator_sections', []),
                        metrics=st.session_state.generator_metrics,
                        status='draft',
                    )
                    st.session_state.current_newsletter_id = saved['id']
                    st.success(f"Saved as draft (ID: {saved['id']})")
                except Exception as e:
                    st.error(f"Could not save: {e}")
        
        with col3:
            if st.button("Reset All", use_container_width=True):
                st.session_state.generator_step = 1
                st.session_state.generator_idea = ""
                st.session_state.generator_angle = ""
                st.session_state.generator_outline = None
                st.session_state.generator_edited_outline = None
                st.session_state.generator_final = None
                st.session_state.generator_sections = []
                st.session_state.current_newsletter_id = None
                # Reset metrics to averages
                for metric_key in metric_definitions.keys():
                    avg = metrics_analysis.get('metrics', {}).get(metric_key, {}).get('mean', 50)
                    st.session_state.generator_metrics[metric_key] = int(avg)
                # Clear persisted session
                clear_and_reset_streamlit(st)
                st.rerun()
    
    # =========================================
    # STEP 2: Edit Outline (same as before)
    # =========================================
    elif step == 2:
        st.subheader("Step 2: Customize Your Outline")
        
        outline = st.session_state.generator_outline
        if not outline:
            st.error("No outline found. Please go back to Step 1.")
            if st.button("< Back to Step 1"):
                st.session_state.generator_step = 1
                st.rerun()
            return
        
        st.markdown(f"**Original idea:** {st.session_state.generator_idea[:200]}...")
        
        # Show current metric settings summary
        with st.expander("Your Style Settings", expanded=False):
            metric_summary = []
            for k, v in st.session_state.generator_metrics.items():
                if v > 70:
                    metric_summary.append(f"High {metric_definitions[k]['name']} ({v})")
                elif v < 30:
                    metric_summary.append(f"Low {metric_definitions[k]['name']} ({v})")
            if metric_summary:
                st.markdown(", ".join(metric_summary[:8]))
        
        st.divider()
        
        # Initialize edited outline from original
        # Handle both old format (sections) and new format (main_story + additional_sections)
        # Only initialize if it's None/empty OR if it belongs to a different idea
        existing_edited = st.session_state.generator_edited_outline
        current_idea = st.session_state.generator_idea
        should_initialize = (
            existing_edited is None
            or not isinstance(existing_edited, dict)
            or existing_edited.get('original_idea') != current_idea
            or (not existing_edited.get('headline') and not existing_edited.get('main_story'))
        )
        if should_initialize:
            # Convert new format to unified structure if needed
            if outline.get('main_story'):
                # New format with separate main_story
                additional = outline.get('additional_sections', [])
                if not isinstance(additional, list):
                    additional = [additional] if additional else []
                all_sections = [outline.get('main_story', {})] + additional
            else:
                # Old format with just sections
                all_sections = outline.get('sections', [])
            
            # Collect sources from idea generator and outline
            initial_sources = []
            
            # Add sources from idea generator
            idea_sources = st.session_state.get('generator_idea_sources', [])
            for source in idea_sources:
                if isinstance(source, dict):
                    initial_sources.append({
                        'title': source.get('title', source.get('publication', 'Source')),
                        'url': source.get('url', ''),
                        'note': source.get('date', '')
                    })
                elif isinstance(source, str) and source.strip():
                    initial_sources.append({'title': source, 'url': '', 'note': ''})
            
            # Add suggested links from outline
            suggested_links = outline.get('suggested_links', [])
            for link in suggested_links:
                if isinstance(link, str):
                    initial_sources.append({'title': link, 'url': '', 'note': 'From outline'})
                elif isinstance(link, dict):
                    initial_sources.append({
                        'title': link.get('title', link.get('text', 'Link')),
                        'url': link.get('url', ''),
                        'note': link.get('note', '')
                    })
            
            st.session_state.generator_edited_outline = {
                # Track which idea this outline was built for, so we don't reuse
                # headlines/previews from a different topic.
                'original_idea': current_idea,
                'headline': '',
                'preview': '',
                'opening_hook': outline.get('opening_hook', ''),
                'main_story': outline.get('main_story', {}),
                'additional_sections': outline.get('additional_sections', []),
                'sections': all_sections,  # Keep for backward compatibility
                'closing_approach': outline.get('closing_approach', ''),
                'tone_notes': outline.get('tone_notes', ''),
                'sources': initial_sources,  # Collected sources for the newsletter
            }
        
        edited = st.session_state.generator_edited_outline
        
        # Always merge sources from idea generator if they exist and aren't already in the list
        idea_sources = st.session_state.get('generator_idea_sources', [])
        if idea_sources and isinstance(edited, dict):
            existing_urls = {s.get('url', '').lower() for s in edited.get('sources', []) if s.get('url')}
            for source in idea_sources:
                if isinstance(source, dict):
                    source_url = source.get('url', '').lower()
                    # Only add if URL doesn't already exist
                    if source_url and source_url not in existing_urls:
                        edited.setdefault('sources', []).append({
                            'title': source.get('title', source.get('publication', 'Source')),
                            'url': source.get('url', ''),
                            'note': source.get('date', '')
                        })
                        existing_urls.add(source_url)
        
        # === HEADLINE SELECTION ===
        st.markdown("### Choose Your Headline")
        headline_options = outline.get('headline_options', ['No headlines generated'])
        headline_options_with_custom = headline_options + ["✍️ Write my own..."]
        
        # Get previously selected headline index or find it from saved headline
        saved_headline = edited.get('headline', '')
        default_headline_idx = edited.get('headline_idx', 0)
        if saved_headline and saved_headline in headline_options:
            default_headline_idx = headline_options.index(saved_headline)
        elif saved_headline and saved_headline not in headline_options:
            # Custom headline was used
            default_headline_idx = len(headline_options)  # "Write my own" option
        
        selected_headline_idx = st.radio(
            "Select a headline or write your own:",
            range(len(headline_options_with_custom)),
            format_func=lambda i: headline_options_with_custom[i],
            index=default_headline_idx,
            key="headline_selector"
        )
        
        if selected_headline_idx == len(headline_options):
            custom_headline = st.text_input("Your custom headline:", value=edited.get('headline', ''))
            edited['headline'] = custom_headline
        else:
            edited['headline'] = headline_options[selected_headline_idx]
        edited['headline_idx'] = selected_headline_idx
        
        st.divider()
        
        # === PREVIEW SELECTION ===
        st.markdown("### Choose Your Preview/Subtitle")
        preview_options = outline.get('preview_options', ['No previews generated'])
        preview_options_with_custom = preview_options + ["✍️ Write my own..."]
        
        # Get previously selected preview index or find it from saved preview
        saved_preview = edited.get('preview', '')
        default_preview_idx = edited.get('preview_idx', 0)
        if saved_preview and saved_preview in preview_options:
            default_preview_idx = preview_options.index(saved_preview)
        elif saved_preview and saved_preview not in preview_options:
            # Custom preview was used
            default_preview_idx = len(preview_options)  # "Write my own" option
        
        selected_preview_idx = st.radio(
            "Select a preview:",
            range(len(preview_options_with_custom)),
            format_func=lambda i: preview_options_with_custom[i],
            index=default_preview_idx,
            key="preview_selector"
        )
        
        if selected_preview_idx == len(preview_options):
            custom_preview = st.text_input("Your custom preview:", value=edited.get('preview', ''))
            edited['preview'] = custom_preview
        else:
            edited['preview'] = preview_options[selected_preview_idx]
        edited['preview_idx'] = selected_preview_idx
        
        st.divider()
        
        # === OPENING HOOK ===
        st.markdown("### 🎣 Opening Hook")
        edited['opening_hook'] = st.text_area(
            "Edit the opening paragraph:",
            value=edited.get('opening_hook', outline.get('opening_hook', '')),
            height=100,
            key="opening_hook_edit"
        )
        
        st.divider()
        
        # === SOURCES & LINKS ===
        st.markdown("### Sources & Links")
        st.caption("Add and manage sources for your newsletter. These will be included and help with accuracy.")
        
        sources = edited.get('sources', [])
        
        with st.expander(f"**{len(sources)} Sources** (click to manage)", expanded=len(sources) > 0):
            if sources:
                edited_sources = []
                for idx, source in enumerate(sources):
                    src_col1, src_col2, src_col3 = st.columns([2, 3, 0.5])
                    with src_col1:
                        title = st.text_input(
                            "Title/Description",
                            value=source.get('title', ''),
                            key=f"source_title_{idx}",
                            label_visibility="collapsed",
                            placeholder="Source title or description"
                        )
                    with src_col2:
                        url = st.text_input(
                            "URL",
                            value=source.get('url', ''),
                            key=f"source_url_{idx}",
                            label_visibility="collapsed",
                            placeholder="https://..."
                        )
                    with src_col3:
                        remove = st.button("", key=f"remove_source_{idx}", help="Remove this source")
                    
                    if not remove and (title or url):
                        edited_sources.append({
                            'title': title,
                            'url': url,
                            'note': source.get('note', '')
                        })
                
                edited['sources'] = edited_sources
            else:
                st.info("No sources added yet. Add sources below to cite in your newsletter.")
            
            st.divider()
            
            # === ADD FROM KNOWLEDGE BASE ===
            st.markdown("**Add from Knowledge Base:**")
            
            # Get articles from knowledge base
            if HAS_KNOWLEDGE_BASE:
                kb_articles = get_articles(limit=100)
                if kb_articles:
                    # Create options for dropdown
                    kb_options = ["-- Select an article --"]
                    kb_article_map = {}
                    for article in kb_articles:
                        title = article.get('title', 'Untitled')[:60]
                        source = article.get('source', 'Unknown')
                        date = article.get('published', article.get('added_at', ''))[:10]
                        display = f"{title} ({source}, {date})"
                        kb_options.append(display)
                        kb_article_map[display] = article
                    
                    kb_col1, kb_col2 = st.columns([4, 1])
                    with kb_col1:
                        selected_kb = st.selectbox(
                            "Select from your Knowledge Base:",
                            options=kb_options,
                            key="kb_source_select",
                            label_visibility="collapsed"
                        )
                    with kb_col2:
                        if st.button("Add", key="add_kb_source", use_container_width=True):
                            if selected_kb != "-- Select an article --":
                                article = kb_article_map.get(selected_kb, {})
                                if 'sources' not in edited:
                                    edited['sources'] = []
                                edited['sources'].append({
                                    'title': article.get('title', 'Untitled'),
                                    'url': article.get('url', ''),
                                    'note': f"From Knowledge Base - {article.get('source', 'Unknown')}"
                                })
                                st.success(f"Added: {article.get('title', 'Article')[:40]}...")
                                st.rerun()
                            else:
                                st.warning("Please select an article first")
                    
                    st.caption(f"{len(kb_articles)} articles available in your Knowledge Base")
                else:
                    st.caption("No articles in Knowledge Base yet. Add some in the Knowledge Base tab.")
            else:
                st.caption("Knowledge Base not available")
            
            st.divider()
            st.markdown("**Or add manually:**")
            
            new_src_col1, new_src_col2 = st.columns([2, 3])
            with new_src_col1:
                new_source_title = st.text_input(
                    "Source title",
                    key="new_source_title",
                    placeholder="e.g., Reuters article on AI regulation"
                )
            with new_src_col2:
                new_source_url = st.text_input(
                    "Source URL",
                    key="new_source_url",
                    placeholder="https://..."
                )
            
            if st.button("Add Source", key="add_new_source"):
                if new_source_title or new_source_url:
                    if 'sources' not in edited:
                        edited['sources'] = []
                    edited['sources'].append({
                        'title': new_source_title,
                        'url': new_source_url,
                        'note': 'Added manually'
                    })
                    st.success(f"Added: {new_source_title or new_source_url}")
                    st.rerun()
                else:
                    st.warning("Please enter a title or URL")
            
            # Quick search button
            st.divider()
            st.markdown("**Need to find sources?**")
            search_topic = st.text_input(
                "Search for sources about:",
                key="source_search_topic",
                placeholder="e.g., AI regulation 2024"
            )
            if search_topic:
                google_url = f"https://www.google.com/search?q={search_topic.replace(' ', '+')}"
                google_news_url = f"https://news.google.com/search?q={search_topic.replace(' ', '+')}"
                st.markdown(f"[🔎 Google Search]({google_url}) | [Google News]({google_news_url})")
        
        st.divider()
        
        # === MAIN STORY (the deep dive based on the idea) ===
        st.markdown("### Main Story")
        st.caption("This is the primary article (400-600 words) based on your idea. The headline you selected above will be used.")
        
        # Use EDITED main_story if available, otherwise fall back to original outline
        main_story = edited.get('main_story') or outline.get('main_story', {})
        if main_story:
            with st.expander("Story Structure & Length", expanded=True):
                # Word count slider
                main_word_count = st.slider(
                    "📏 Target Word Count",
                    min_value=200,
                    max_value=1000,
                    value=main_story.get('target_word_count', 500),
                    step=50,
                    key="main_story_word_count",
                    help="Target word count for main story"
                )
                
                st.markdown("**Story structure** *(edit each section's focus)*:")
                structure = main_story.get('structure', [])
                edited_structure = []
                for j, point in enumerate(structure):
                    edited_point = st.text_input(
                        f"Section {j+1}:",
                        value=point,
                        key=f"structure_{j}",
                        label_visibility="collapsed"
                    )
                    if edited_point:
                        edited_structure.append(edited_point)
                
                new_structure_point = st.text_input(
                    "Add another structure section:",
                    placeholder="e.g., Personal anecdote: Share your own experience with...",
                    key="new_structure_point"
                )
                if new_structure_point:
                    edited_structure.append(new_structure_point)
                
                st.divider()
                
                st.markdown("**Key points to develop:**")
                main_bullets = main_story.get('key_points', main_story.get('bullet_points', []))
                edited_main_bullets = []
                for j, bullet in enumerate(main_bullets):
                    edited_bullet = st.text_input(
                        f"Point {j+1}:",
                        value=bullet,
                        key=f"main_bullet_{j}",
                        label_visibility="collapsed"
                    )
                    if edited_bullet:
                        edited_main_bullets.append(edited_bullet)
                
                new_main_point = st.text_input(
                    "Add another key point:",
                    placeholder="Type to add...",
                    key="new_main_bullet"
                )
                if new_main_point:
                    edited_main_bullets.append(new_main_point)
                
                main_user_notes = st.text_area(
                    "Your notes for the main story (details, examples, sources):",
                    value=main_story.get('user_notes', ''),
                    height=80,
                    placeholder="Add specific details, data, quotes, or sources you want included...",
                    key="main_story_notes"
                )
                
                edited['main_story'] = {
                    'heading': edited.get('headline', main_story.get('heading', '')),  # Use newsletter headline
                    'structure': edited_structure,
                    'key_points': edited_main_bullets,
                    'target_word_count': main_word_count,
                    'notes': main_story.get('notes', ''),
                    'user_notes': main_user_notes
                }
        else:
            # Fallback for old format - treat first section as main story
            sections = outline.get('sections', [])
            if sections:
                first_section = sections[0]
                st.info("The main story is your in-depth article based on your idea.")
        
        st.divider()
        
        # === ADDITIONAL SECTIONS (News Roundup, Tools, etc.) ===
        st.markdown("### 📑 Additional Sections")
        st.caption("Quick news items, tools, updates - NOT the main content")
        
        # Fetch real news button
        if HAS_NEWS_FETCHER:
            news_col1, news_col2, news_col3 = st.columns([1, 1, 1])
            with news_col1:
                if st.button("Fetch Recent AI News", key="fetch_ai_news", help="Get real AI news from RSS feeds"):
                    with st.spinner("Fetching news from tech sources..."):
                        try:
                            news_items = get_recent_ai_news(days=7)
                            if news_items:
                                st.session_state.fetched_news = news_items[:10]
                                st.success(f"✓ Found {len(news_items)} recent articles!")
                            else:
                                st.warning("No recent news found. Try fetching all news.")
                        except Exception as e:
                            st.error(f"Could not fetch news: {e}")
            with news_col2:
                if st.button("Fetch Africa Tech News", key="fetch_africa_news", help="Get Africa-focused tech news"):
                    with st.spinner("Fetching Africa tech news..."):
                        try:
                            africa_news = get_africa_news(days=30)
                            if africa_news:
                                st.session_state.fetched_news = africa_news[:10]
                                st.success(f"✓ Found {len(africa_news)} Africa tech articles!")
                            else:
                                st.warning("No Africa news found.")
                        except Exception as e:
                            st.error(f"Could not fetch news: {e}")
            with news_col3:
                topic = st.text_input("Search topic:", placeholder="e.g., ChatGPT, journalism", key="news_search_topic", label_visibility="collapsed")
                if st.button("Search", key="search_news_btn") and topic:
                    with st.spinner(f"Searching for '{topic}'..."):
                        try:
                            results = search_news(topic)
                            if results:
                                st.session_state.fetched_news = results[:10]
                                st.success(f"✓ Found {len(results)} articles about '{topic}'!")
                        except Exception as e:
                            st.error(f"Search failed: {e}")
            
            # Show fetched news for easy copy
            if st.session_state.get('fetched_news'):
                with st.expander(f"{len(st.session_state.fetched_news)} Real News Items (click to add to your newsletter)", expanded=True):
                    for idx, article in enumerate(st.session_state.fetched_news):
                        col_news, col_add = st.columns([4, 1])
                        with col_news:
                            pub_date = article.get('published', '')[:10] if article.get('published') else ''
                            st.markdown(f"**{article.get('title', 'No title')[:70]}...**")
                            st.caption(f"{article.get('source', 'Unknown')} | {pub_date} | [Link]({article.get('url', '#')})")
                        with col_add:
                            if st.button("", key=f"add_news_{idx}", help="Copy to clipboard"):
                                st.toast(f"Copied: {article.get('title', '')[:40]}...")
                                # Store for easy paste
                                st.session_state.last_copied_news = f"{article.get('title', '')} | Source: {article.get('source', '')} | {article.get('url', '')}"
                    
                    if st.button("Clear", key="clear_fetched_news"):
                        st.session_state.fetched_news = None
                        st.rerun()
        else:
            st.info("Install `feedparser` to enable automatic news fetching: `pip install feedparser`")
        
        st.warning("**News items need verification** - Even with fetched news, verify before publishing.")
        
        # Use EDITED additional_sections if available, otherwise fall back to original outline
        additional_sections = edited.get('additional_sections') or outline.get('additional_sections', outline.get('sections', []))
        # Skip main_story if it's in the sections list
        if not outline.get('main_story') and not edited.get('additional_sections') and additional_sections:
            # Old format: first section is main story, rest are additional
            additional_sections = additional_sections[1:] if len(additional_sections) > 1 else []
        
        edited_sections = []
        
        for i, section in enumerate(additional_sections):
            # Handle case where section might be a string instead of dict
            if isinstance(section, str):
                section = {'heading': section, 'type': 'general', 'content': ''}
            elif not isinstance(section, dict):
                continue  # Skip invalid sections
            
            section_type = section.get('type', 'general')
            section_icon = '' if section_type == 'news_roundup' else '' if section_type == 'develop_ai' else ''
            is_news = section_type == 'news_roundup'
            
            with st.expander(f"{section_icon} {section.get('heading', 'Section')}", expanded=True):
                # Header row with heading and word count
                sec_head_col, sec_wc_col = st.columns([3, 1])
                with sec_head_col:
                    new_heading = st.text_input(
                        "Section heading:",
                        value=section.get('heading', ''),
                        key=f"add_section_heading_{i}"
                    )
                with sec_wc_col:
                    # Different defaults for different section types
                    default_wc = 100 if is_news else 150 if section_type == 'develop_ai' else 150
                    section_word_count = st.slider(
                        "📏 Words",
                        min_value=50,
                        max_value=400,
                        value=section.get('target_word_count', default_wc),
                        step=25,
                        key=f"section_word_count_{i}",
                        help="Target word count for this section"
                    )
                
                if is_news:
                    st.markdown("**News items** *(add source URL for each - must be recent!)*:")
                else:
                    st.markdown("**Points to cover:**")
                
                bullets = section.get('bullet_points', [])
                sources = section.get('sources', [])
                edited_bullets = []
                edited_sources = []
                
                for j, bullet in enumerate(bullets):
                    col_bullet, col_source = st.columns([3, 2])
                    with col_bullet:
                        edited_bullet = st.text_input(
                            f"Item {j+1}:",
                            value=bullet,
                            key=f"add_bullet_{i}_{j}",
                            label_visibility="collapsed"
                        )
                    with col_source:
                        if is_news:
                            existing_source = sources[j] if j < len(sources) else ''
                            source_url = st.text_input(
                                "Source URL:",
                                value=existing_source,
                                placeholder="https://... (required)",
                                key=f"add_source_{i}_{j}",
                                label_visibility="collapsed"
                            )
                            edited_sources.append(source_url)
                    
                    if edited_bullet:
                        edited_bullets.append(edited_bullet)
                
                # Add new item
                new_col1, new_col2 = st.columns([3, 2])
                with new_col1:
                    new_point = st.text_input(
                        "Add another item:",
                        placeholder="Type to add...",
                        key=f"add_new_bullet_{i}"
                    )
                with new_col2:
                    if is_news:
                        new_source = st.text_input(
                            "Source:",
                            placeholder="https://...",
                            key=f"add_new_source_{i}",
                            label_visibility="collapsed"
                        )
                    else:
                        new_source = ''
                
                if new_point:
                    edited_bullets.append(new_point)
                    if is_news:
                        edited_sources.append(new_source)
                
                user_notes = st.text_area(
                    "Your notes for this section:",
                    value=section.get('user_notes', ''),
                    height=60,
                    placeholder="Add any specific details, context, or your own commentary...",
                    key=f"add_section_notes_{i}"
                )
                
                edited_sections.append({
                    'type': section_type,
                    'heading': new_heading,
                    'bullet_points': edited_bullets,
                    'sources': edited_sources if is_news else [],
                    'target_word_count': section_word_count,
                    'notes': section.get('notes', ''),
                    'user_notes': user_notes
                })
        
        edited['additional_sections'] = edited_sections
        # Keep backward compatible sections format
        edited['sections'] = [edited.get('main_story', {})] + edited_sections if edited.get('main_story') else edited_sections
        
        st.divider()
        
        # === IMAGE PROMPT SELECTION ===
        st.markdown("### Newsletter Image")
        st.caption("Select an image prompt or write your own. The image will be generated with the newsletter.")
        
        image_prompts = outline.get('image_prompts', [])
        
        # Initialize selected image prompt in session state
        if 'selected_image_prompt' not in st.session_state:
            st.session_state.selected_image_prompt = None
        
        if image_prompts:
            # Add options: the prompts + "Write my own" + "No image"
            image_options = ["🚫 No image for this newsletter"] + image_prompts + ["✍️ Write my own prompt..."]
            
            selected_image_idx = st.radio(
                "Choose an image style:",
                range(len(image_options)),
                format_func=lambda i: image_options[i][:100] + "..." if len(image_options[i]) > 100 else image_options[i],
                key="image_prompt_selector",
                horizontal=False
            )
            
            if selected_image_idx == 0:
                # No image
                edited['image_prompt'] = None
                st.session_state.selected_image_prompt = None
            elif selected_image_idx == len(image_options) - 1:
                # Custom prompt
                custom_prompt = st.text_area(
                    "Your custom DALL-E prompt:",
                    value=edited.get('image_prompt', ''),
                    height=80,
                    placeholder="Describe the image you want... (e.g., 'A photorealistic image of African journalists in a modern newsroom, looking at AI-generated content on multiple screens')",
                    key="custom_image_prompt"
                )
                edited['image_prompt'] = custom_prompt
                st.session_state.selected_image_prompt = custom_prompt
            else:
                # Selected one of the AI prompts
                edited['image_prompt'] = image_prompts[selected_image_idx - 1]
                st.session_state.selected_image_prompt = image_prompts[selected_image_idx - 1]
            
            # Show preview of selected prompt
            if edited.get('image_prompt'):
                st.info(f"📸 **Selected prompt:** {edited['image_prompt']}")
        else:
            st.warning("No image prompts were generated. You can write your own:")
            custom_prompt = st.text_area(
                "DALL-E image prompt (optional):",
                value=edited.get('image_prompt', ''),
                height=80,
                placeholder="Describe the image you want...",
                key="custom_image_prompt_fallback"
            )
            edited['image_prompt'] = custom_prompt if custom_prompt else None
            st.session_state.selected_image_prompt = custom_prompt if custom_prompt else None
        
        st.divider()
        
        # === CLOSING ===
        st.markdown("### 🎬 Closing Approach")
        edited['closing_approach'] = st.text_area(
            "How should the newsletter end?",
            value=edited.get('closing_approach', outline.get('closing_approach', '')),
            height=80,
            key="closing_edit"
        )
        
        # === TONE ===
        st.markdown("### 🎭 Tone")
        edited['tone_notes'] = st.text_input(
            "Any tone adjustments?",
            value=edited.get('tone_notes', outline.get('tone_notes', '')),
            placeholder="e.g., More urgent, more hopeful, more skeptical...",
            key="tone_edit"
        )
        
        st.divider()
        
        # === STYLE CONTROLS (moved here from Step 1) ===
        st.markdown("### Style Controls")
        st.caption("Adjust these dials before generating the final newsletter")
        
        # Show the most impactful style dials
        recommendations = metrics_analysis.get('recommendations', [])
        
        style_col1, style_col2 = st.columns(2)
        
        with style_col1:
            for rec in recommendations[:4]:
                metric_key = rec['metric']
                if metric_key in metric_definitions:
                    metric_def = metric_definitions[metric_key]
                    avg_val = metrics_analysis.get('metrics', {}).get(metric_key, {}).get('mean', 50)
                    current_val = st.session_state.generator_metrics.get(metric_key, int(avg_val))
                    
                    impact = f"{'' if rec['direction'] == 'positive' else '📉'} {rec['impact']}"
                    
                    new_val = st.slider(
                        f"{metric_def['name']} {impact}",
                        min_value=0,
                        max_value=100,
                        value=current_val,
                        key=f"step2_metric_{metric_key}",
                    )
                    st.session_state.generator_metrics[metric_key] = new_val
        
        with style_col2:
            for rec in recommendations[4:8]:
                metric_key = rec['metric']
                if metric_key in metric_definitions:
                    metric_def = metric_definitions[metric_key]
                    avg_val = metrics_analysis.get('metrics', {}).get(metric_key, {}).get('mean', 50)
                    current_val = st.session_state.generator_metrics.get(metric_key, int(avg_val))
                    
                    impact = f"{'' if rec['direction'] == 'positive' else '📉'} {rec['impact']}"
                    
                    new_val = st.slider(
                        f"{metric_def['name']} {impact}",
                        min_value=0,
                        max_value=100,
                        value=current_val,
                        key=f"step2_metric_{metric_key}",
                    )
                    st.session_state.generator_metrics[metric_key] = new_val
        
        st.session_state.generator_edited_outline = edited
        
        st.divider()
        
        # Navigation buttons
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.button("< Back to Step 1", use_container_width=True):
                st.session_state.generator_step = 1
                st.rerun()
        
        with col2:
            if st.button("Save Draft", use_container_width=True):
                try:
                    if st.session_state.get('current_newsletter_id'):
                        # Update existing draft
                        save_version(
                            newsletter_id=st.session_state.current_newsletter_id,
                            headline=edited.get('headline', ''),
                            preview=edited.get('preview', ''),
                            outline=outline,
                            edited_outline=edited,
                            sections=st.session_state.get('generator_sections', []),
                            metrics=st.session_state.generator_metrics,
                            notes='Saved outline draft',
                        )
                        st.success("Draft updated!")
                    else:
                        # Create new draft
                        saved = create_newsletter(
                            idea=st.session_state.generator_idea,
                            headline=edited.get('headline', '') or f"[DRAFT] {st.session_state.generator_idea[:40]}...",
                            preview=edited.get('preview', ''),
                            outline=outline,
                            edited_outline=edited,
                            story_type=st.session_state.get('generator_story_type', ''),
                            sections=st.session_state.get('generator_sections', []),
                            metrics=st.session_state.generator_metrics,
                            status='draft',
                        )
                        st.session_state.current_newsletter_id = saved['id']
                        st.success(f"Saved as draft! (ID: {saved['id']})")
                except Exception as e:
                    st.error(f"Could not save: {e}")
        
        with col3:
            if st.button("Regenerate Outline", use_container_width=True):
                metric_instructions = build_metric_instructions(
                    st.session_state.generator_metrics,
                    metric_definitions,
                    metrics_analysis
                )
                with st.spinner("Regenerating outline..."):
                    result = generate_newsletter(
                        idea=st.session_state.generator_idea,
                        format_type="outline",
                        additional_instructions=metric_instructions,
                        temperature=0.9
                    )
                if result.get('outline'):
                    st.session_state.generator_outline = result['outline']
                    st.session_state.generator_edited_outline = None
                    st.rerun()
        
        with col4:
            if st.button("Generate Prompt >", type="primary", use_container_width=True):
                if not edited.get('headline'):
                    st.error("Please select or write a headline")
                elif not edited.get('preview'):
                    st.error("Please select or write a preview")
                else:
                    # Force save to session state explicitly
                    st.session_state.generator_edited_outline = edited
                    
                    # Record learnings from edits
                    try:
                        learn_result = record_outline_edit(
                            original_outline=outline,
                            edited_outline=edited,
                            idea=st.session_state.generator_idea,
                            story_type=st.session_state.generator_story_type
                        )
                        if learn_result.get('changes_recorded', 0) > 0:
                            st.toast(f"Learned from {learn_result['changes_recorded']} edit(s)")
                    except Exception as e:
                        pass  # Don't block generation if learning fails
                    
                    # NEW: Record article usage in Knowledge Base
                    if HAS_KNOWLEDGE_BASE:
                        try:
                            sources = edited.get('sources', [])
                            headline = edited.get('headline', 'Untitled Newsletter')
                            for source in sources:
                                if isinstance(source, dict) and source.get('url'):
                                    record_article_usage_by_url(
                                        url=source['url'],
                                        newsletter_headline=headline,
                                        usage_type='generation'
                                    )
                        except Exception as e:
                            pass  # Don't block generation if tracking fails
                    
                    # Clear the cached prompt and newsletter
                    st.session_state.generator_prompt = None
                    st.session_state.generator_prompt_edited = None
                    st.session_state.generator_final = None
                    
                    st.session_state.generator_step = 3
                    st.rerun()
    
    # =========================================
    # STEP 3: Review & Edit the AI-Generated Prompt (NEW!)
    # =========================================
    elif step == 3:
        st.subheader("Step 3: Review & Edit the AI-Generated Prompt")
        st.markdown("*Your fine-tuned model has written a meticulous prompt. Review, edit if needed, then generate.*")
        
        edited = st.session_state.generator_edited_outline
        
        if not edited:
            st.error("No outline found. Please go back.")
            if st.button("< Back to Outline"):
                st.session_state.generator_step = 2
                st.rerun()
            return
        
        # Generate the prompt if not already done
        if not st.session_state.generator_prompt:
            # Get the story type data (full details, not just instructions)
            story_types = get_story_type_list()
            story_type_data = next((stype for stype in story_types if stype['key'] == st.session_state.get('generator_story_type', 'news_analysis')), {})
            
            # Build additional text instructions (legacy format)
            story_type_instructions = build_story_type_instructions(story_type_data)
            metric_instructions = build_metric_instructions(
                st.session_state.generator_metrics,
                metric_definitions,
                metrics_analysis
            )
            all_instructions = f"""{story_type_instructions}

{metric_instructions}"""
            
            # Get the style metrics (the dial values)
            style_metrics = st.session_state.get('generator_metrics', {})
            
            style_model, is_fine_tuned = get_active_model_display()
            
            with st.spinner(f"🚀 Newsletter Engine building intelligent prompt (semantic search, RAG examples, style Bible)..."):
                try:
                    # USE NEWSLETTER ENGINE - Intelligent prompt construction
                    if NEWSLETTER_ENGINE_AVAILABLE:
                        engine = NewsletterEngine()
                        
                        # Build prompt using intelligent system
                        system_prompt, user_prompt, metadata = engine.generator.build_prompt_from_outline_data(
                            outline_data=edited,
                            idea=st.session_state.generator_idea,
                            style_metrics=style_metrics,
                            story_type_data=story_type_data
                        )
                        
                        # Store the results
                        st.session_state.generator_prompt = user_prompt
                        st.session_state.generator_prompt_system = system_prompt
                        st.session_state.generator_prompt_model = 'Newsletter Engine + GPT-4o'
                        st.session_state.generator_prompt_word_count = metadata.get('target_word_count', 0)
                        
                        # Store metadata for display
                        st.session_state.generator_engine_metadata = metadata
                        
                        # Show what was used
                        facts_used = metadata.get('facts_count', 0)
                        rag_used = metadata.get('rag_examples_count', 0)
                        learnings = metadata.get('learnings_applied', 0)
                        bible_sections = len(metadata.get('bible_sections', []))
                        
                        st.success(f"✅ Intelligent prompt built!")
                        st.caption(f"📊 Used: {facts_used} facts (semantic search) | {rag_used} RAG examples | {bible_sections} Bible sections | {learnings} learnings applied")
                        st.rerun()
                    else:
                        # Fallback to old method if engine not available
                        from newsletter_generator import generate_meticulous_prompt
                        
                        prompt_result = generate_meticulous_prompt(
                            idea=st.session_state.generator_idea,
                            outline_data=edited,
                            additional_instructions=all_instructions,
                            style_metrics=style_metrics,
                            story_type_data=story_type_data
                        )
                        
                        if prompt_result.get('error'):
                            st.error(f"❌ Prompt generation failed: {prompt_result['error']}")
                        elif not prompt_result.get('prompt'):
                            st.error("❌ No prompt was generated. Please try again.")
                        else:
                            st.session_state.generator_prompt = prompt_result.get('prompt', '')
                            st.session_state.generator_prompt_system = prompt_result.get('system_prompt', '')
                            st.session_state.generator_prompt_model = prompt_result.get('model_used', 'gpt-4o')
                            st.session_state.generator_prompt_word_count = prompt_result.get('total_word_count', 0)
                            st.success(f"✅ Prompt generated (fallback mode)")
                            st.rerun()
                        
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"❌ Error generating prompt: {error_msg[:500]}")
                    if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                        st.info("💡 The request timed out. This might be due to a long prompt or network issues. Try again.")
                    elif "rate limit" in error_msg.lower():
                        st.info("💡 Rate limit exceeded. Please wait a moment and try again.")
                    else:
                        st.info("💡 Check your OpenAI API key and network connection.")
        
        # Display the prompt for review/editing
        if st.session_state.generator_prompt:
            st.success(f"Prompt generated by `{st.session_state.get('generator_prompt_model', 'fine-tuned model')}`")
            
            # Show Newsletter Engine metadata if available
            engine_meta = st.session_state.get('generator_engine_metadata', {})
            if engine_meta:
                with st.expander("📊 Intelligent Prompt Components Used", expanded=True):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Facts (Semantic)", engine_meta.get('facts_count', 0))
                    with col2:
                        st.metric("RAG Examples", engine_meta.get('rag_examples_count', 0))
                    with col3:
                        st.metric("Bible Sections", len(engine_meta.get('bible_sections', [])))
                    with col4:
                        st.metric("Learnings Applied", engine_meta.get('learnings_applied', 0))
                    
                    if engine_meta.get('bible_sections'):
                        st.caption(f"Bible sections: {', '.join(engine_meta['bible_sections'])}")
                    if engine_meta.get('embedding_source'):
                        st.caption(f"Embeddings: {engine_meta['embedding_source']}")
            
            # Show what the fine-tuned model produced
            st.markdown("### The AI-Generated Prompt")
            st.caption("This intelligent prompt combines your outline, semantic search for facts, RAG examples from your best newsletters, targeted Bible sections, and learnings from your past edits.")
            
            # Editable prompt
            edited_prompt = st.text_area(
                "Edit the prompt (or leave as-is):",
                value=st.session_state.get('generator_prompt_edited') or st.session_state.generator_prompt,
                height=500,
                key="prompt_editor"
            )
            
            # Store edited version
            st.session_state.generator_prompt_edited = edited_prompt
            
            # Show the system prompt (collapsible)
            with st.expander("System Prompt (context sent to GPT-4.1)", expanded=False):
                st.code(st.session_state.get('generator_prompt_system', 'Default system prompt'), language=None)
            
            # Word count and info
            word_count = len(edited_prompt.split())
            st.caption(f"Prompt length: {word_count} words | {len(edited_prompt)} characters")
            
            st.divider()
            
            # Navigation
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("< Back to Outline", use_container_width=True):
                    st.session_state.generator_step = 2
                    st.rerun()
            
            with col2:
                if st.button("Regenerate Prompt", use_container_width=True):
                    st.session_state.generator_prompt = None
                    st.session_state.generator_prompt_edited = None
                    st.rerun()
            
            with col3:
                if st.button("Generate Newsletter with GPT-4.1 >", type="primary", use_container_width=True):
                    st.session_state.generator_final = None  # Clear any previous
                    st.session_state.generator_step = 4
                    st.rerun()
    
    # =========================================
    # STEP 4: Generate Final Newsletter (was Step 3)
    # =========================================
    elif step == 4:
        st.subheader("Step 4: Your Newsletter")
        
        edited = st.session_state.generator_edited_outline
        
        if not edited:
            st.error("No outline found. Please go back.")
            if st.button("< Back"):
                st.session_state.generator_step = 2
                st.rerun()
            return
        
        # Show a summary of the outline
        with st.expander("Your Outline Summary", expanded=False):
            st.markdown(f"**Headline:** {edited.get('headline', 'Not set')}")
            st.markdown(f"**Preview:** {edited.get('preview', 'Not set')}")
            
            main_story = edited.get('main_story', {})
            if main_story.get('key_points'):
                st.markdown("**Main Story Key Points:**")
                for point in main_story.get('key_points', []):
                    st.markdown(f"- {point}")
            
            add_sections = edited.get('additional_sections', [])
            if add_sections:
                st.markdown(f"**{len(add_sections)} Additional Sections**")
        
        # Show the prompts/blueprint that were used to generate the newsletter
        # Check for new blueprint-based generation
        blueprint_instructions = st.session_state.get('generator_blueprint_instructions', '')
        blueprint = st.session_state.get('generator_blueprint', '')
        execution_prompt = st.session_state.get('generator_execution_prompt', '')
        generation_mode = st.session_state.get('generator_generation_mode', '')
        
        # Legacy prompts
        style_prompt = st.session_state.get('generator_style_prompt', '')
        user_prompt = st.session_state.get('generator_user_prompt', '')
        
        # NEW: Blueprint Two-Stage Display
        if generation_mode == 'blueprint_two_stage' or blueprint:
            with st.expander("View Generation Process (Blueprint Two-Stage)", expanded=True):
                st.markdown("### How Your Newsletter Was Generated")
                st.caption("Your fine-tuned GPT-4o was used for both stages - planning AND writing.")
                
                # Stage 1: Blueprint Instructions
                st.markdown("---")
                st.markdown("#### STAGE 1: Blueprint Instructions")
                st.caption("These instructions were sent to your fine-tuned model to create a comprehensive plan.")
                if blueprint_instructions:
                    with st.container():
                        if len(blueprint_instructions) > 3000:
                            st.code(blueprint_instructions[:3000] + "\n\n... [truncated]", language=None)
                            if st.checkbox("Show full blueprint instructions", key="show_full_bp_instructions"):
                                st.code(blueprint_instructions, language=None)
                        else:
                            st.code(blueprint_instructions, language=None)
                else:
                    st.info("Blueprint instructions will appear after generation.")
                
                # Stage 1 Output: The Blueprint
                st.markdown("---")
                st.markdown("#### STAGE 1 OUTPUT: The Blueprint")
                st.caption("Your fine-tuned model created this detailed plan for the newsletter.")
                if blueprint:
                    st.markdown(blueprint)
                else:
                    st.info("Blueprint will appear after generation.")
                
                # Stage 2: Execution
                st.markdown("---")
                st.markdown("#### STAGE 2: Execution Prompt")
                st.caption("The blueprint was then sent back to your model with these instructions.")
                if execution_prompt:
                    with st.container():
                        if len(execution_prompt) > 3000:
                            st.code(execution_prompt[:3000] + "\n\n... [truncated]", language=None)
                            if st.checkbox("Show full execution prompt", key="show_full_exec_prompt"):
                                st.code(execution_prompt, language=None)
                        else:
                            st.code(execution_prompt, language=None)
                else:
                    st.info("Execution prompt will appear after generation.")
        
        # LEGACY: Style Prompt + GPT-4.1 Display
        elif style_prompt or user_prompt:
            with st.expander("View Full Prompts Sent to AI", expanded=False):
                if style_prompt:
                    st.markdown("### Stage 1: Style Prompt (from your fine-tuned model)")
                    st.caption("This prompt was generated by your fine-tuned gpt-4o-mini to guide GPT-4.1.")
                    st.code(style_prompt, language=None)
                    st.divider()
                
                if user_prompt:
                    st.markdown("### Stage 2: Content Generation Prompt")
                    st.caption("This is the full prompt sent to GPT-4.1 to generate the newsletter.")
                    if len(user_prompt) > 5000:
                        st.code(user_prompt[:5000] + "\n\n... [truncated - click below to see full prompt]", language=None)
                        if st.checkbox("Show full prompt", key="show_full_prompt"):
                            st.code(user_prompt, language=None)
                    else:
                        st.code(user_prompt, language=None)
        
        # Show facts used from Knowledge Base (if any)
        facts_used = st.session_state.get('generator_facts_used', [])
        if facts_used:
            with st.expander(f"{len(facts_used)} Facts from Knowledge Base (Available for Citation)", expanded=False):
                st.caption("These facts were automatically matched to your topic and made available to the AI. Use the citations in your newsletter.")
                for fact in facts_used:
                    confidence_emoji = {'high': '', 'medium': '', 'low': ''}.get(fact.get('confidence', 'medium'), '')
                    fact_type = fact.get('fact_type', 'fact').upper()
                    st.markdown(f"**{confidence_emoji} [{fact_type}]** {fact.get('text', '')[:150]}...")
                    st.caption(f"{fact.get('citation', 'No URL')} | Source: {fact.get('source_name', 'Unknown')} | Relevance: {fact.get('relevance_score', 0):.1f}")
                    st.markdown("---")
        
        # Generate or show the final newsletter
        if not st.session_state.generator_final:
            # Get the approved prompt from Step 3
            approved_prompt = st.session_state.get('generator_prompt_edited') or st.session_state.get('generator_prompt')
            system_prompt = st.session_state.get('generator_prompt_system', '')
            
            if not approved_prompt:
                st.error("No prompt found. Please go back to Step 3 to generate and approve the prompt.")
                if st.button("< Back to Prompt"):
                    st.session_state.generator_step = 3
                    st.rerun()
                return
            
            progress_placeholder = st.empty()
            progress_placeholder.info("**Generating newsletter with GPT-4.1** using your approved prompt...")
            
            try:
                from newsletter_generator import execute_approved_prompt
                
                result = execute_approved_prompt(
                    approved_prompt=approved_prompt,
                    system_prompt=system_prompt,
                    outline_data=edited,
                    temperature=0.7
                )
                
                if result.get('error'):
                    st.error(f"Generation failed: {result['error']}")
                    progress_placeholder.empty()
                    if st.button("Try Again"):
                        st.session_state.generator_final = None
                        st.rerun()
                    return
                
                # Success!
                model_used = result.get('model_used', 'gpt-4.1')
                progress_placeholder.success(f"**Done!** Newsletter generated by `{model_used}`")
                
                generated_content = result.get('content', '')
                st.session_state.generator_final = generated_content
                # Store original for automatic learning when user edits
                st.session_state.generator_original_content = generated_content
                
                # Store the prompts for display
                st.session_state.generator_approved_prompt = approved_prompt
                st.session_state.generator_execution_system = system_prompt
                
            except ImportError:
                st.error("execute_approved_prompt function not available. Please update newsletter_generator.py")
                progress_placeholder.empty()
            except Exception as e:
                st.error(f"Generation failed: {e}")
                progress_placeholder.empty()
            st.session_state.generator_two_stage_used = result.get('two_stage', False)
            st.session_state.generator_generation_mode = result.get('generation_mode', '')
            
            # Store blueprint data (new mode)
            st.session_state.generator_blueprint_instructions = result.get('blueprint_instructions', '')
            st.session_state.generator_blueprint = result.get('blueprint', '')
            st.session_state.generator_execution_prompt = result.get('execution_prompt', '')
            
            # Store legacy prompt data
            st.session_state.generator_style_prompt = result.get('style_prompt', '')
            st.session_state.generator_user_prompt = result.get('user_prompt', '')
            
            # Image generation moved to Step 4
            # Persist the generated newsletter
            sync_from_streamlit(st)
            
            # Save to database
            try:
                if st.session_state.get('current_newsletter_id'):
                    # Save as new version
                    save_version(
                        newsletter_id=st.session_state.current_newsletter_id,
                        headline=edited.get('headline', ''),
                        preview=edited.get('preview', ''),
                        content=st.session_state.generator_final,
                        outline=st.session_state.generator_outline,
                        edited_outline=edited,
                        sections=st.session_state.get('generator_sections', []),
                        metrics=st.session_state.generator_metrics,
                        notes='Regenerated version',
                    )
                else:
                    # Create new newsletter
                    saved = create_newsletter(
                        idea=st.session_state.generator_idea,
                        headline=edited.get('headline', ''),
                        preview=edited.get('preview', ''),
                        content=st.session_state.generator_final,
                        outline=st.session_state.generator_outline,
                        edited_outline=edited,
                        story_type=st.session_state.get('generator_story_type', ''),
                        sections=st.session_state.get('generator_sections', []),
                        metrics=st.session_state.generator_metrics,
                        status='draft',
                    )
                    st.session_state.current_newsletter_id = saved['id']
                st.toast("Saved to Library")
            except Exception as e:
                st.warning(f"Could not save: {e}")
        
        # Display/Edit the final newsletter
        final_content = st.session_state.generator_final
        
        # Show image status - but images are generated in Step 4
        if st.session_state.get('generated_image'):
            st.success("Image attached (view in Step 4)")
        else:
            st.info("Go to **Step 4** to generate a header image for your newsletter")
        
        # Toggle between view and edit mode
        if 'newsletter_edit_mode' not in st.session_state:
            st.session_state.newsletter_edit_mode = False
        
        # =============================================
        # EDIT CONTROLS - Always visible at the top
        # =============================================
        st.markdown("---")
        st.markdown("### Newsletter Content")
        
        # View/Edit/Save toggle row
        edit_controls_col1, edit_controls_col2, edit_controls_col3, edit_controls_col4 = st.columns([1, 1, 1, 2])
        
        with edit_controls_col1:
            view_btn = st.button(
                "View Mode", 
                use_container_width=True, 
                type="primary" if not st.session_state.newsletter_edit_mode else "secondary",
                key="view_mode_btn"
            )
            if view_btn:
                st.session_state.newsletter_edit_mode = False
                st.rerun()
        
        with edit_controls_col2:
            edit_btn = st.button(
                "Edit Mode", 
                use_container_width=True,
                type="primary" if st.session_state.newsletter_edit_mode else "secondary",
                key="edit_mode_btn"
            )
            if edit_btn:
                st.session_state.newsletter_edit_mode = True
                st.rerun()
        
        with edit_controls_col3:
            if st.session_state.newsletter_edit_mode:
                if st.button("Save Edits", use_container_width=True, type="primary", key="save_edits_btn"):
                    edited_content = st.session_state.get('newsletter_editor_content', final_content)
                    original_content = st.session_state.get('generator_original_content', final_content)
                    
                    # AUTOMATIC LEARNING: Track the edit if content changed
                    if NEWSLETTER_ENGINE_AVAILABLE and edited_content != original_content:
                        try:
                            engine = NewsletterEngine()
                            # Calculate how much changed
                            from difflib import SequenceMatcher
                            similarity = SequenceMatcher(None, original_content, edited_content).ratio()
                            
                            # Only track if meaningful edits (more than 5% change)
                            if similarity < 0.95:
                                result = engine.track_edit(
                                    generation_id=st.session_state.get('current_newsletter_id', 'unknown'),
                                    original=original_content,
                                    edited=edited_content,
                                    notes=f"Auto-tracked from Write tab. Similarity: {similarity:.1%}"
                                )
                                st.toast(f"🎓 AI learned from your edits! ({(1-similarity)*100:.0f}% changed)")
                        except Exception as e:
                            # Don't block the save if learning fails
                            pass
                    
                    st.session_state.generator_final = edited_content
                    sync_from_streamlit(st)
                    st.success("Edits saved!")
                    st.rerun()
        
        with edit_controls_col4:
            if st.session_state.newsletter_edit_mode:
                st.caption("Edit mode active - make changes below")
            else:
                st.caption("View mode - click 'Edit Mode' to make changes")
        
        st.markdown("---")
        
        # =============================================
        # CONTENT DISPLAY/EDIT AREA
        # =============================================
        if st.session_state.newsletter_edit_mode:
            # Edit mode - show text area
            st.warning("**Editing Mode Active** — Make changes below, then click 'Save Edits'")
            edited_content = st.text_area(
                "Newsletter content (Markdown):",
                value=final_content,
                height=600,
                key="newsletter_editor_content",
                help="Edit your newsletter in Markdown format. Use # for headings, ** for bold, etc."
            )
            # Preview while editing
            with st.expander("Preview (as it will appear)", expanded=False):
                st.markdown(edited_content)
        else:
            # View mode - render markdown
            st.markdown(final_content)
        
        st.markdown("---")
        
        # Action buttons
        st.subheader("What's Next?")
        
        # Primary actions row
        primary_col1, primary_col2, primary_col3 = st.columns(3)
        
        with primary_col1:
            if st.button("Add Image >", use_container_width=True, help="Go to Step 5 to generate a header image"):
                st.session_state.generator_step = 5
                st.rerun()
        
        with primary_col2:
            if st.button("Save Draft", use_container_width=True, help="Save current version to library"):
                try:
                    if st.session_state.get('current_newsletter_id'):
                        # Update existing
                        save_version(
                            newsletter_id=st.session_state.current_newsletter_id,
                            headline=edited.get('headline', ''),
                            preview=edited.get('preview', ''),
                            content=final_content,
                            outline=st.session_state.generator_outline,
                            edited_outline=edited,
                            sections=st.session_state.get('generator_sections', []),
                            metrics=st.session_state.generator_metrics,
                            notes='Saved from generator',
                        )
                        st.success("Saved new version!")
                    else:
                        # Create new
                        saved = create_newsletter(
                            idea=st.session_state.generator_idea,
                            headline=edited.get('headline', ''),
                            preview=edited.get('preview', ''),
                            content=final_content,
                            outline=st.session_state.generator_outline,
                            edited_outline=edited,
                            story_type=st.session_state.get('generator_story_type', ''),
                            sections=st.session_state.get('generator_sections', []),
                            metrics=st.session_state.generator_metrics,
                            status='draft',
                        )
                        st.session_state.current_newsletter_id = saved['id']
                        st.success(f"Saved! (ID: {saved['id']})")
                    # Also persist to session
                    sync_from_streamlit(st)
                except Exception as e:
                    st.error(f"Save failed: {e}")
        
        with primary_col3:
            # PUBLISH BUTTON - saves to training data AND adds to incremental training
            if HAS_PUBLISHED:
                if st.button("Publish & Train", type="primary", use_container_width=True, 
                            help="Mark as final and add to training data for your AI model"):
                    try:
                        # 1. Publish to published newsletters store
                        published = publish_newsletter(
                            idea=st.session_state.generator_idea,
                            headline=edited.get('headline', ''),
                            content=final_content,
                            outline=st.session_state.generator_outline,
                            story_type=st.session_state.get('generator_story_type', ''),
                            notes=f"Published from generator on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        )
                        
                        # 2. Add to incremental training data for auto-training
                        if HAS_FINE_TUNING:
                            training_result = add_to_training_data(
                                idea=st.session_state.generator_idea,
                                headline=edited.get('headline', ''),
                                content=final_content,
                                story_type=st.session_state.get('generator_story_type', '')
                            )
                        
                        # 2b. Update Newsletter Bible with this successful newsletter
                        opening_hook = edited.get('opening_hook', '')
                        update_bible_from_newsletter(
                            headline=edited.get('headline', ''),
                            content=final_content,
                            opening_hook=opening_hook
                        )
                        
                        # 3. Save to library as 'published'
                        if st.session_state.get('current_newsletter_id'):
                            update_newsletter_metadata(
                                newsletter_id=st.session_state.current_newsletter_id,
                                status='published'
                            )
                        else:
                            saved = create_newsletter(
                                idea=st.session_state.generator_idea,
                                headline=edited.get('headline', ''),
                                preview=edited.get('preview', ''),
                                content=final_content,
                                outline=st.session_state.generator_outline,
                                edited_outline=edited,
                                story_type=st.session_state.get('generator_story_type', ''),
                                sections=st.session_state.get('generator_sections', []),
                                metrics=st.session_state.generator_metrics,
                                status='published',
                            )
                            st.session_state.current_newsletter_id = saved['id']
                        
                        st.success(f"Published! Added to training data (ID: {published['id']})")
                        st.balloons()
                        
                        # 4. Check if auto-training should be triggered
                        if HAS_FINE_TUNING:
                            auto_check = should_auto_train()
                            if auto_check['should_train']:
                                st.info(f"🎓 **Auto-training ready!** You have {auto_check['current_count']} new newsletters.")
                                if st.button("Start Training Now", key="auto_train_now"):
                                    with st.spinner("Starting fine-tuning job..."):
                                        result = trigger_incremental_training()
                                        if result.get('triggered'):
                                            st.success(f"Training started! Job ID: {result['job_id']}")
                                            st.caption(f"Training on {result['total_examples']} examples ({result['new_examples']} new)")
                                        else:
                                            st.warning(result.get('reason', 'Training not triggered'))
                            else:
                                st.info(f"Training data: {auto_check['current_count']}/{auto_check['threshold']} newsletters until next auto-training")
                        
                    except Exception as e:
                        st.error(f"Publish failed: {e}")
            else:
                st.button("Publish", use_container_width=True, disabled=True, 
                         help="Publishing module not available")
        
        st.divider()
        
        # Secondary actions row
        st.caption("**Other actions:**")
        sec_col1, sec_col2, sec_col3, sec_col4 = st.columns(4)
        
        with sec_col1:
            if st.button("Edit Outline", use_container_width=True, help="Go back to edit the outline structure"):
                st.session_state.generator_step = 2
                st.session_state.generator_final = None
                st.session_state.newsletter_edit_mode = False
                st.rerun()
        
        with sec_col2:
            if st.button("Regenerate", use_container_width=True, help="Generate a new version from the outline"):
                st.session_state.generator_final = None
                st.session_state.newsletter_edit_mode = False
                st.rerun()
        
        with sec_col3:
            if st.button("Start New", use_container_width=True):
                st.session_state.generator_step = 1
                st.session_state.generator_idea = ""
                st.session_state.generator_angle = ""
                st.session_state.generator_outline = None
                st.session_state.generator_edited_outline = None
                st.session_state.generator_final = None
                st.session_state.current_newsletter_id = None
                st.session_state.newsletter_edit_mode = False
                # Clear persisted session
                clear_and_reset_streamlit(st)
                st.rerun()
        
        with sec_col4:
            # Export to markdown/clipboard
            if st.button("Copy to Clipboard", use_container_width=True):
                st.code(final_content, language="markdown")
                st.caption("Select all and copy the text above")
        
        # Show current save status
        if st.session_state.get('current_newsletter_id'):
            st.caption(f"Saved in Library (ID: {st.session_state.current_newsletter_id})")
    
    # =========================================
    # STEP 5: Image Generation (was Step 4)
    # =========================================
    elif step == 5:
        st.subheader("Step 5: Generate Newsletter Image")
        
        if not st.session_state.get('generator_final'):
            st.error("No newsletter found. Please complete Step 4 first.")
            if st.button("< Back to Newsletter"):
                st.session_state.generator_step = 4
                st.rerun()
            return
        
        # Get the edited outline for context
        edited = st.session_state.get('generator_edited_outline', {})
        headline = edited.get('headline', st.session_state.get('generator_idea', 'Newsletter'))
        idea = st.session_state.get('generator_idea', '')
        
        st.markdown(f"**Newsletter:** *{headline[:80]}...*")
        st.divider()
        
        # Initialize image state
        if 'generator_image_result' not in st.session_state:
            st.session_state.generator_image_result = None
        if 'step4_image_prompt' not in st.session_state:
            st.session_state.step4_image_prompt = ""
        if 'step4_prompt_suggestions' not in st.session_state:
            st.session_state.step4_prompt_suggestions = []
        
        # Image generation options
        img_col1, img_col2 = st.columns([2, 1])
        
        with img_col1:
            st.markdown("### Image Prompt")
            
            # Get AI suggestions
            if st.button("Get AI Image Suggestions", key="step4_get_suggestions", use_container_width=True):
                with st.spinner("Generating prompt ideas based on your newsletter..."):
                    prompts = suggest_image_prompts(idea, st.session_state.get('generator_story_type', ''))
                    st.session_state.step4_prompt_suggestions = prompts
            
            # Show suggestions
            if st.session_state.step4_prompt_suggestions:
                st.markdown("**AI Suggestions (click to use):**")
                for i, prompt in enumerate(st.session_state.step4_prompt_suggestions):
                    if st.button(f"📷 {prompt[:70]}...", key=f"step4_use_prompt_{i}", use_container_width=True):
                        st.session_state.step4_image_prompt = prompt
                        st.rerun()
            
            st.divider()
            
            # Custom prompt input
            st.session_state.step4_image_prompt = st.text_area(
                "Your image prompt:",
                value=st.session_state.step4_image_prompt,
                height=100,
                placeholder="Describe the image you want for your newsletter header...\n\nExample: African journalist in a modern newsroom looking at AI tools on multiple screens, editorial photography style, warm lighting",
                key="step4_prompt_input"
            )
        
        with img_col2:
            st.markdown("### Settings")
            
            image_style = st.selectbox(
                "Style",
                ["vivid", "natural"],
                help="Vivid = dramatic/artistic, Natural = realistic"
            )
            
            image_size = st.selectbox(
                "Size",
                ["1792x1024 (Wide - Recommended)", "1024x1024 (Square)", "1024x1792 (Tall)"],
            )
            size_map = {
                "1792x1024 (Wide - Recommended)": "1792x1024",
                "1024x1024 (Square)": "1024x1024",
                "1024x1792 (Tall)": "1024x1792"
            }
            actual_size = size_map[image_size]
            
            image_quality = st.selectbox(
                "Quality",
                ["standard", "hd"],
                help="HD costs more but has better detail"
            )
            
            st.divider()
            st.caption("💰 **Cost estimate:**")
            if image_quality == "hd":
                st.caption("~$0.08 per image")
            else:
                st.caption("~$0.04 per image")
        
        st.divider()
        
        # Generate button
        gen_col1, gen_col2 = st.columns([2, 1])
        
        with gen_col1:
            if st.button("Generate Image", type="primary", use_container_width=True, 
                        disabled=not st.session_state.step4_image_prompt):
                if st.session_state.step4_image_prompt:
                    with st.spinner("Generating image with DALL-E 3... (15-30 seconds)"):
                        result = generate_image_dalle(
                            prompt=st.session_state.step4_image_prompt,
                            style=image_style,
                            size=actual_size,
                            quality=image_quality
                        )
                        st.session_state.generator_image_result = result
                        st.rerun()
                else:
                    st.warning("Please enter an image prompt first")
        
        with gen_col2:
            if st.session_state.generator_image_result and st.session_state.generator_image_result.get('url'):
                if st.button("Regenerate", use_container_width=True):
                    with st.spinner("Regenerating..."):
                        result = generate_image_dalle(
                            prompt=st.session_state.step4_image_prompt,
                            style=image_style,
                            size=actual_size,
                            quality=image_quality
                        )
                        st.session_state.generator_image_result = result
                        st.rerun()
        
        # Show generated image
        if st.session_state.generator_image_result:
            result = st.session_state.generator_image_result
            
            if result.get('error'):
                st.error(f"Image generation failed: {result['error']}")
            elif result.get('url'):
                st.divider()
                st.markdown("### Your Generated Image")
                
                st.image(result['url'], caption="Newsletter Header Image", use_column_width=True)
                
                # Show revised prompt
                if result.get('revised_prompt'):
                    with st.expander("DALL-E's revised prompt"):
                        st.caption(result['revised_prompt'])
                
                # Action buttons
                action_col1, action_col2, action_col3 = st.columns(3)
                
                with action_col1:
                    st.markdown(f"[Download Image]({result['url']})")
                
                with action_col2:
                    if st.button("Use This Image", type="primary"):
                        st.session_state.generated_image = result
                        st.success("Image saved! It will be included with your newsletter.")
                
                with action_col3:
                    if st.button("Discard"):
                        st.session_state.generator_image_result = None
                        st.rerun()
        
        st.divider()
        
        # Navigation
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
        
        with nav_col1:
            if st.button("< Back to Newsletter", use_container_width=True):
                st.session_state.generator_step = 4
                st.rerun()
        
        with nav_col2:
            if st.button("Edit Outline", use_container_width=True):
                st.session_state.generator_step = 2
                st.rerun()
        
        with nav_col3:
            if st.button("New Idea", use_container_width=True):
                st.session_state.generator_step = 1
                st.rerun()
        
        with nav_col4:
            if st.button("Complete", type="primary", use_container_width=True):
                st.success("Newsletter complete with image!")
                st.balloons()


def build_story_type_instructions(story_type_data: dict) -> str:
    """Build AI instructions from the selected story type."""
    
    if not story_type_data:
        return ""
    
    instructions = []
    instructions.append("## MAIN STORY TYPE")
    instructions.append("")
    instructions.append(f"This newsletter is a **{story_type_data.get('name', 'News')}** piece.")
    instructions.append(f"Description: {story_type_data.get('description', '')}")
    instructions.append(f"Tone: {story_type_data.get('tone', 'Informative')}")
    instructions.append("")
    
    # Add headline patterns
    patterns = story_type_data.get('headline_patterns', [])
    if patterns:
        instructions.append("**Headline patterns to follow:**")
        for pattern in patterns:
            instructions.append(f"- {pattern}")
        instructions.append("")
    
    # Add examples
    examples = story_type_data.get('examples', [])
    if examples:
        instructions.append("**Example headlines from this type:**")
        for example in examples[:3]:
            instructions.append(f"- {example}")
        instructions.append("")
    
    return "\n".join(instructions)


def build_section_instructions(selected_sections: list[dict]) -> str:
    """Build AI instructions from the selected section templates."""
    
    if not selected_sections:
        return ""
    
    instructions = []
    instructions.append("## NEWSLETTER STRUCTURE (user-selected sections)")
    instructions.append("")
    instructions.append("This newsletter MUST include the following sections in roughly this order:")
    instructions.append("")
    
    for i, section in enumerate(selected_sections, 1):
        icon = section.get('icon', '')
        name = section.get('name', 'Section')
        description = section.get('description', '')
        examples = section.get('example_headings', [])
        avg_words = section.get('avg_word_count', 200)
        
        instructions.append(f"{i}. **{icon} {name}**")
        instructions.append(f"   - Purpose: {description}")
        if examples:
            instructions.append(f"   - Example headings: {', '.join(examples[:3])}")
        instructions.append(f"   - Typical length: ~{avg_words:.0f} words")
        instructions.append("")
    
    instructions.append("Create the outline with these section types as the major sections.")
    instructions.append("Each section should have its own heading and bullet points for what to cover.")
    
    return "\n".join(instructions)


def build_metric_instructions(metrics: dict, definitions: dict, analysis: dict) -> str:
    """Build AI instructions from the metric dial settings."""
    
    instructions = []
    instructions.append("## STYLE SETTINGS (from user's dial adjustments)")
    instructions.append("")
    
    # Group by high/low values compared to average
    high_metrics = []
    low_metrics = []
    
    for metric_key, value in metrics.items():
        if metric_key not in definitions:
            continue
        
        avg = analysis.get('metrics', {}).get(metric_key, {}).get('mean', 50)
        name = definitions[metric_key]['name']
        description = definitions[metric_key]['description']
        
        diff_from_avg = value - avg
        
        if value >= 70:
            high_metrics.append({
                'name': name,
                'value': value,
                'description': description,
                'intensity': 'HEAVILY' if value >= 85 else 'MORE'
            })
        elif value <= 30:
            low_metrics.append({
                'name': name,
                'value': value,
                'description': description,
                'intensity': 'COMPLETELY AVOID' if value <= 15 else 'MINIMIZE'
            })
    
    if high_metrics:
        instructions.append("**EMPHASIZE THESE ELEMENTS (user set dials HIGH):**")
        for m in high_metrics:
            instructions.append(f"- {m['intensity']} use {m['name']}: {m['description']}")
    
    if low_metrics:
        instructions.append("")
        instructions.append("**MINIMIZE THESE ELEMENTS (user set dials LOW):**")
        for m in low_metrics:
            instructions.append(f"- {m['intensity']} {m['name']}: {m['description']}")
    
    # Add specific tone combinations
    instructions.append("")
    
    doom = metrics.get('doom_level', 50)
    optimism = metrics.get('optimism_level', 50)
    
    if doom >= 70 and optimism <= 30:
        instructions.append("**OVERALL TONE:** Dark and cautionary. This newsletter should feel urgent and warning-oriented.")
    elif optimism >= 70 and doom <= 30:
        instructions.append("**OVERALL TONE:** Hopeful and constructive. Focus on solutions and opportunities.")
    elif doom >= 60 and optimism >= 60:
        instructions.append("**OVERALL TONE:** Balanced but intense. Acknowledge serious risks while highlighting opportunities.")
    
    return "\n".join(instructions)


# ============================================================================
# Main App
# ============================================================================

def get_active_model_display():
    """Get the actual active model name for display - real data only."""
    if HAS_FINE_TUNING:
        try:
            ft_model = get_active_fine_tuned_model()
            if ft_model:
                return ft_model, True
        except:
            pass
    return "gpt-4o-mini", False


def show_model_badge(feature_name: str, models_used: list):
    """Display a small badge showing which model(s) are used for a feature.
    
    Args:
        feature_name: Name of the feature (e.g., "Idea Generation")
        models_used: List of model names actually used
    """
    model_str = " + ".join(models_used)
    st.caption(f"**{feature_name}** uses: `{model_str}`")


# ============================================================================
# PUBLISHING TAB
# ============================================================================

def render_publishing_tab():
    """Render the Publishing tab with analytics and social sharing tools."""
    st.header("Publishing")
    st.markdown("*Optimize your publishing time and distribute your newsletter*")
    
    if not HAS_PUBLISHING:
        st.error("Publishing analytics module not available. Check that publishing_analytics.py exists.")
        return
    
    # Create sub-tabs
    pub_tab1, pub_tab2, pub_tab3, pub_tab4 = st.tabs([
        "Best Time to Publish",
        "Social Media Posts",
        "Performance Insights",
        "Publishing Checklist"
    ])
    
    # =========================================================================
    # TAB 1: Best Time to Publish
    # =========================================================================
    with pub_tab1:
        st.subheader("Optimal Publishing Time")
        st.markdown("*Based on analysis of your newsletter performance data*")
        
        try:
            recommendation = get_publishing_recommendation()
            day_analysis = recommendation.get('day_analysis', {})
            
            # Show the main recommendation
            optimal = recommendation.get('optimal_publish_time', {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Best Day",
                    optimal.get('day', 'Tuesday'),
                    help="Day with highest average open rate"
                )
            with col2:
                st.metric(
                    "Recommended Time",
                    optimal.get('time', '10:00 AM'),
                    help="Based on industry best practices for B2B newsletters"
                )
            with col3:
                confidence = day_analysis.get('confidence', 'low')
                confidence_emoji = {'high': 'High', 'medium': 'Medium', 'low': 'Low'}.get(confidence, 'Low')
                st.metric(
                    "Confidence",
                    confidence_emoji,
                    help=f"Based on {day_analysis.get('best_day_sample_size', 0)} newsletters"
                )
            
            # Show the recommendation
            st.info(day_analysis.get('recommendation', 'Not enough data for recommendations.'))
            
            # Day-by-day breakdown
            st.markdown("### Day-by-Day Performance")
            
            day_stats = day_analysis.get('day_stats', {})
            if day_stats:
                # Create a visual breakdown
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                for day in days_order:
                    if day in day_stats:
                        stats = day_stats[day]
                        open_rate = stats.get('avg_open_rate', 0)
                        count = stats.get('count', 0)
                        
                        # Calculate bar width (relative to max)
                        max_rate = max([s.get('avg_open_rate', 0) for s in day_stats.values()])
                        bar_width = int((open_rate / max_rate) * 100) if max_rate > 0 else 0
                        
                        # Highlight best day
                        is_best = day == day_analysis.get('best_day')
                        
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            if is_best:
                                st.markdown(f"**{day}** (Best)")
                            else:
                                st.markdown(day)
                        with col2:
                            bar_color = "green" if is_best else "gray"
                            st.progress(bar_width / 100)
                            st.caption(f"{open_rate*100:.1f}% open rate ({count} newsletters)")
            else:
                st.warning("Not enough data to show day-by-day breakdown. Publish more newsletters to get insights.")
            
            # Improvement potential
            if day_analysis.get('improvement_potential'):
                st.markdown("---")
                st.markdown(f"**Potential improvement:** Switching from {day_analysis.get('worst_day', 'worst day')} to {day_analysis.get('best_day', 'best day')} could improve open rates by **{day_analysis.get('improvement_potential', 'N/A')}**")
        
        except Exception as e:
            st.error(f"Error loading analytics: {e}")
    
    # =========================================================================
    # TAB 2: Social Media Posts
    # =========================================================================
    with pub_tab2:
        st.subheader("Social Media Distribution")
        st.markdown("*Generate posts to promote your newsletter on social platforms*")
        
        # Check if we have a current newsletter
        edited_outline = st.session_state.get('generator_edited_outline') or {}
        current_headline = edited_outline.get('headline', '') if isinstance(edited_outline, dict) else ''
        current_preview = edited_outline.get('preview', '') if isinstance(edited_outline, dict) else ''
        current_content = st.session_state.get('generator_final', '') or ''
        
        col1, col2 = st.columns(2)
        
        with col1:
            headline = st.text_input(
                "Newsletter Headline",
                value=current_headline,
                help="The headline of your newsletter"
            )
        
        with col2:
            newsletter_url = st.text_input(
                "Newsletter URL",
                value="",
                placeholder="https://yoursubstack.substack.com/p/...",
                help="Link to your newsletter (leave blank if not published yet)"
            )
        
        preview = st.text_area(
            "Preview/Description",
            value=current_preview,
            height=80,
            help="Brief description of what the newsletter covers"
        )
        
        # Key points
        key_points_text = st.text_area(
            "Key Points (one per line)",
            value="",
            height=100,
            placeholder="Main insight 1\nMain insight 2\nMain insight 3",
            help="The main takeaways from your newsletter"
        )
        key_points = [p.strip() for p in key_points_text.split('\n') if p.strip()]
        
        st.markdown("---")
        
        # Generate buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Generate Social Posts", type="primary", use_container_width=True):
                if not headline:
                    st.warning("Please enter a headline first")
                else:
                    with st.spinner("Generating social media posts..."):
                        result = generate_social_posts(
                            headline=headline,
                            preview=preview,
                            newsletter_url=newsletter_url or "[YOUR_NEWSLETTER_URL]",
                            key_points=key_points
                        )
                        st.session_state['social_posts'] = result
        
        with col2:
            if st.button("Generate Twitter Thread", use_container_width=True):
                if not headline:
                    st.warning("Please enter a headline first")
                elif not current_content:
                    st.warning("Generate a newsletter first in the Write tab")
                else:
                    with st.spinner("Generating thread..."):
                        result = generate_thread_content(
                            headline=headline,
                            preview=preview,
                            content=current_content,
                            platform='twitter'
                        )
                        st.session_state['social_thread'] = result
        
        # Display generated posts
        if 'social_posts' in st.session_state:
            result = st.session_state['social_posts']
            
            if result.get('error'):
                st.error(f"Error: {result['error']}")
            else:
                posts = result.get('posts', {})
                
                st.markdown("### Generated Posts")
                st.caption("Click to copy, then paste into your social platform")
                
                # Twitter/X
                if posts.get('twitter'):
                    st.markdown("**Twitter/X**")
                    st.code(posts['twitter'], language=None)
                    st.caption(f"Characters: {len(posts['twitter'])}/280")
                
                # LinkedIn
                if posts.get('linkedin'):
                    st.markdown("**LinkedIn**")
                    st.code(posts['linkedin'], language=None)
                
                # Threads
                if posts.get('threads'):
                    st.markdown("**Threads**")
                    st.code(posts['threads'], language=None)
                
                # Raw output (if parsing failed)
                if posts.get('raw'):
                    st.markdown("**Generated Content**")
                    st.markdown(posts['raw'])
        
        # Display generated thread
        if 'social_thread' in st.session_state:
            result = st.session_state['social_thread']
            
            if result.get('error'):
                st.error(f"Error: {result['error']}")
            elif result.get('thread'):
                st.markdown("### Twitter/X Thread")
                st.caption("Copy each tweet to build your thread")
                
                for i, tweet in enumerate(result['thread'], 1):
                    st.markdown(f"**Tweet {i}/{len(result['thread'])}**")
                    st.code(tweet, language=None)
                    if i < len(result['thread']):
                        st.caption("↓")
    
    # =========================================================================
    # TAB 3: Performance Insights
    # =========================================================================
    with pub_tab3:
        st.subheader("Performance Insights")
        st.markdown("*Trends and patterns from your newsletter history*")
        
        try:
            trends = analyze_performance_trends()
            
            # Overall stats
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Newsletters",
                    trends.get('total_newsletters', 0)
                )
            
            with col2:
                st.metric(
                    "Total Opens",
                    f"{trends.get('total_opens', 0):,}"
                )
            
            with col3:
                st.metric(
                    "Avg Open Rate",
                    f"{trends.get('overall_avg', 0)*100:.1f}%"
                )
            
            with col4:
                trend = trends.get('trend', 'unknown')
                trend_emoji = {'improving': 'Improving', 'stable': 'Stable', 'declining': 'Declining'}.get(trend, 'Unknown')
                st.metric(
                    "Trend",
                    trend_emoji
                )
            
            # Trend description
            st.info(trends.get('trend_description', 'Not enough data for trend analysis.'))
            
            # Insights
            st.markdown("### Key Insights")
            insights = trends.get('insights', [])
            if insights:
                for insight in insights:
                    st.markdown(f"- {insight}")
            else:
                st.caption("Publish more newsletters to unlock insights.")
            
            # Top performers
            st.markdown("### Top Performing Newsletters")
            top_performers = trends.get('top_performers', [])
            
            if top_performers:
                for i, nl in enumerate(top_performers, 1):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        title = nl.get('title', 'Untitled')[:60]
                        st.markdown(f"**{i}. {title}**")
                    
                    with col2:
                        open_rate = nl.get('open_rate', 0)
                        st.markdown(f"{open_rate*100:.1f}%")
                    
                    with col3:
                        opens = nl.get('opens', 0)
                        st.markdown(f"{opens:,} opens")
            else:
                st.caption("No newsletter data available yet.")
            
            # Recent vs historical comparison
            st.markdown("### Recent vs Historical Performance")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Recent (last 5)",
                    f"{trends.get('recent_avg', 0)*100:.1f}%",
                    help="Average open rate of last 5 newsletters"
                )
            
            with col2:
                st.metric(
                    "Historical",
                    f"{trends.get('historical_avg', 0)*100:.1f}%",
                    help="Average open rate of older newsletters"
                )
            
            with col3:
                recent = trends.get('recent_avg', 0)
                hist = trends.get('historical_avg', 0)
                if hist > 0:
                    change = ((recent / hist) - 1) * 100
                    st.metric(
                        "Change",
                        f"{change:+.1f}%",
                        help="How recent performance compares to historical"
                    )
                else:
                    st.metric("Change", "N/A")
        
        except Exception as e:
            st.error(f"Error loading performance data: {e}")
    
    # =========================================================================
    # TAB 4: Publishing Checklist
    # =========================================================================
    with pub_tab4:
        st.subheader("Publishing Checklist")
        st.markdown("*Make sure you're ready to publish*")
        
        # Get current newsletter data
        checklist_outline = st.session_state.get('generator_edited_outline') or {}
        newsletter_data = {
            'headline': checklist_outline.get('headline') if isinstance(checklist_outline, dict) else None,
            'preview': checklist_outline.get('preview') if isinstance(checklist_outline, dict) else None,
            'content': st.session_state.get('generator_final'),
            'image_url': st.session_state.get('generator_image_url')
        }
        
        checklist = get_publishing_checklist(newsletter_data)
        
        # Display checklist
        completed = 0
        for item in checklist:
            col1, col2 = st.columns([0.1, 0.9])
            
            with col1:
                # Use checkboxes that update session state
                key = f"checklist_{item['id']}"
                is_complete = item['status'] == 'complete' or st.session_state.get(key, False)
                checked = st.checkbox("", value=is_complete, key=key, label_visibility="collapsed")
                if checked:
                    completed += 1
            
            with col2:
                if checked:
                    st.markdown(f"~~{item['title']}~~")
                else:
                    st.markdown(f"**{item['title']}**")
                st.caption(item['description'])
        
        # Progress
        st.markdown("---")
        progress = completed / len(checklist)
        st.progress(progress)
        st.caption(f"{completed}/{len(checklist)} items complete")
        
        if progress == 1.0:
            st.success("You're ready to publish!")
            st.balloons()
        elif progress >= 0.7:
            st.info("Almost there! Complete the remaining items before publishing.")
        else:
            st.warning("Complete more items before publishing.")
        
        # Quick actions
        st.markdown("### Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Generate Social Posts", use_container_width=True):
                st.session_state['active_pub_tab'] = 1  # Switch to social tab
                st.rerun()
        
        with col2:
            if st.button("View Optimal Timing", use_container_width=True):
                st.session_state['active_pub_tab'] = 0  # Switch to timing tab
                st.rerun()


def main():
    """Main app entry point."""
    
    # Header
    st.markdown("""
        <div class="letter-header">
            <span class="letter-logo">L+</span>
            <span class="letter-title">Letter+</span>
            <p class="letter-tagline">Newsletter creation studio trained on your writing style</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Create tabs (Publishing merged into Library)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Ideas",
        "Knowledge Base",
        "Write",
        "Library",
        "Training",
        "Settings"
    ])
    
    with tab1:
        render_idea_generator_tab()
    
    with tab2:
        render_knowledge_base_tab()
    
    with tab3:
        render_generator_tab()
    
    with tab4:
        render_library_tab()
    
    with tab5:
        render_training_tab()
    
    with tab6:
        render_settings_tab()
    
    # Footer
    st.divider()
    st.markdown(
        "<div style='text-align: center; color: var(--text-muted); font-size: 0.75rem; padding: 1rem 0;'>"
        "Letter+ by Develop AI"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

