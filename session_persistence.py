"""
Session Persistence - Save work-in-progress state to disk

Persists the generator form fields so users don't lose their work when:
- The page refreshes
- The browser is closed
- The app restarts

The state is saved automatically as users type and make changes.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Any

DATA_DIR = Path(__file__).parent / "data"
SESSION_FILE = DATA_DIR / "work_in_progress.json"


def load_session() -> dict:
    """Load the persisted session state."""
    if not SESSION_FILE.exists():
        return get_default_session()
    
    try:
        with open(SESSION_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure all required keys exist
            default = get_default_session()
            for key in default:
                if key not in data:
                    data[key] = default[key]
            return data
    except (json.JSONDecodeError, Exception):
        return get_default_session()


def save_session(session_data: dict):
    """Save the session state to disk."""
    DATA_DIR.mkdir(exist_ok=True)
    session_data['last_saved'] = datetime.now().isoformat()
    
    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False, default=str)


def get_default_session() -> dict:
    """Return default session state."""
    return {
        # Step 1 - Idea
        'idea': '',
        'idea_angle': '',
        'story_type': 'news_analysis',
        'selected_sections': [],
        'idea_sources': [],
        
        # Step 1 - Metrics/Dials
        'metrics': {},
        
        # Step 1 - Images
        'images': [],
        
        # Step 2 - Outline
        'outline': None,
        'edited_outline': None,
        'outline_text': '',
        
        # Step 3 - Generated content
        'generated_headline': '',
        'generated_preview': '',
        'generated_content': '',
        
        # Workflow state
        'current_step': 1,
        'newsletter_id': None,  # If editing an existing newsletter
        
        # Timestamps
        'started_at': datetime.now().isoformat(),
        'last_saved': datetime.now().isoformat(),
    }


def update_field(field: str, value: Any):
    """Update a single field and save."""
    session = load_session()
    session[field] = value
    save_session(session)


def update_fields(**kwargs):
    """Update multiple fields and save."""
    session = load_session()
    for key, value in kwargs.items():
        session[key] = value
    save_session(session)


def clear_session():
    """Clear all work in progress (start fresh)."""
    save_session(get_default_session())


def get_field(field: str, default: Any = None) -> Any:
    """Get a single field value."""
    session = load_session()
    return session.get(field, default)


def has_work_in_progress() -> bool:
    """Check if there's unsaved work."""
    session = load_session()
    idea = session.get('idea') or ''
    generated_content = session.get('generated_content') or ''
    return bool(
        idea.strip() or
        session.get('outline') or
        generated_content.strip()
    )


def get_work_summary() -> dict:
    """Get a summary of current work in progress."""
    session = load_session()
    
    # Safely get string values (could be None)
    generated_content = session.get('generated_content') or ''
    idea = session.get('idea') or ''
    
    # Determine stage
    if generated_content.strip():
        stage = 'newsletter'
        stage_icon = '📄'
    elif session.get('outline') or session.get('edited_outline'):
        stage = 'outline'
        stage_icon = '📋'
    elif idea.strip():
        stage = 'idea'
        stage_icon = '💡'
    else:
        stage = 'empty'
        stage_icon = '🆕'
    
    return {
        'stage': stage,
        'stage_icon': stage_icon,
        'idea_preview': (session.get('idea', '')[:80] + '...') if len(session.get('idea', '')) > 80 else session.get('idea', ''),
        'headline': session.get('generated_headline', ''),
        'last_saved': session.get('last_saved', ''),
        'current_step': session.get('current_step', 1),
    }


# ============================================================================
# Integration helpers for Streamlit
# ============================================================================

def sync_to_streamlit(st):
    """
    Load persisted session into Streamlit session_state.
    Call this once at app startup.
    """
    session = load_session()
    
    # Only load if Streamlit state is empty (first load)
    if 'session_loaded' not in st.session_state:
        st.session_state.session_loaded = True
        
        # Step 1 - Idea and configuration
        if 'generator_idea' not in st.session_state or not st.session_state.generator_idea:
            st.session_state.generator_idea = session.get('idea', '')
        if 'generator_angle' not in st.session_state or not st.session_state.get('generator_angle'):
            st.session_state.generator_angle = session.get('idea_angle', '')
        if 'generator_story_type' not in st.session_state:
            st.session_state.generator_story_type = session.get('story_type', 'news_analysis')
        if 'generator_sections' not in st.session_state:
            st.session_state.generator_sections = session.get('selected_sections', [])
        if 'generator_idea_sources' not in st.session_state:
            st.session_state.generator_idea_sources = session.get('idea_sources', [])
        if 'generator_metrics' not in st.session_state:
            st.session_state.generator_metrics = session.get('metrics', {})
        if 'generator_images' not in st.session_state:
            st.session_state.generator_images = session.get('images', [])
        
        # Step 2 - Outline
        if 'generator_outline' not in st.session_state:
            st.session_state.generator_outline = session.get('outline')
        if 'generator_edited_outline' not in st.session_state:
            st.session_state.generator_edited_outline = session.get('edited_outline')
        
        # Step 3 - Final content
        if 'generator_final' not in st.session_state:
            st.session_state.generator_final = session.get('generated_content')
        
        # Workflow
        if 'generator_step' not in st.session_state:
            st.session_state.generator_step = session.get('current_step', 1)
        if 'current_newsletter_id' not in st.session_state:
            st.session_state.current_newsletter_id = session.get('newsletter_id')


def sync_from_streamlit(st):
    """
    Save Streamlit session_state to disk.
    Call this after any changes.
    """
    # Handle sections - could be dicts or strings
    sections = st.session_state.get('generator_sections', [])
    serializable_sections = []
    for s in sections:
        if isinstance(s, dict):
            serializable_sections.append(s)
        else:
            serializable_sections.append({'key': str(s)})
    
    session_data = {
        # Step 1
        'idea': st.session_state.get('generator_idea', ''),
        'idea_angle': st.session_state.get('generator_angle', ''),
        'story_type': st.session_state.get('generator_story_type', 'news_analysis'),
        'selected_sections': serializable_sections,
        'idea_sources': st.session_state.get('generator_idea_sources', []),
        'metrics': st.session_state.get('generator_metrics', {}),
        'images': st.session_state.get('generator_images', []),
        
        # Step 2
        'outline': st.session_state.get('generator_outline'),
        'edited_outline': st.session_state.get('generator_edited_outline'),
        
        # Step 3
        'generated_content': st.session_state.get('generator_final', ''),
        
        # Workflow
        'current_step': st.session_state.get('generator_step', 1),
        'newsletter_id': st.session_state.get('current_newsletter_id'),
    }
    
    save_session(session_data)


def clear_and_reset_streamlit(st):
    """Clear persisted session and reset Streamlit state."""
    clear_session()
    
    # Reset Streamlit state
    st.session_state.generator_idea = ''
    st.session_state.generator_angle = ''
    st.session_state.generator_story_type = 'news_analysis'
    st.session_state.generator_sections = []
    st.session_state.generator_metrics = {}
    st.session_state.generator_images = []
    st.session_state.generator_outline = None
    st.session_state.generator_edited_outline = None
    st.session_state.generator_idea_sources = []
    st.session_state.generator_final = None
    st.session_state.generator_step = 1
    st.session_state.current_newsletter_id = None
    st.session_state.session_loaded = False


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    print("Session Persistence Test")
    print("=" * 50)
    
    # Test save/load
    test_session = get_default_session()
    test_session['idea'] = "Test idea about AI in African newsrooms"
    test_session['story_type'] = 'news_analysis'
    
    save_session(test_session)
    print("✓ Session saved")
    
    loaded = load_session()
    print(f"✓ Session loaded: {loaded['idea'][:50]}...")
    
    print(f"\nHas work in progress: {has_work_in_progress()}")
    print(f"Work summary: {get_work_summary()}")
    
    print("\n" + "=" * 50)
    print("Session persistence ready!")

