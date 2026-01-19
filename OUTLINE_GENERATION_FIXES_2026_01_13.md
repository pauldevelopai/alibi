# Outline Generation Fixes - January 13, 2026

## Issues Reported

The user reported two critical problems during **Step 2 (Outline Creation)**:

1. **Fake URLs being generated** - The system was creating invented article URLs like:
   - `https://arstechnica.com/ai/2026/01/google-removes-some-ai-health-summaries...`
   - `https://www.buzzfeed.com/daveyalba/google-ai-health-checks-errors`
   - `https://www.nytimes.com/2025/11/10/health/ai-health-google.html`
   
   These URLs don't exist and are hallucinated.

2. **Generic story structure** - The structure was showing generic template text instead of topic-specific guidance:
   - "Opening: Hook with a specific example or anecdote"
   - "Context: Why this matters now"
   - "Analysis: The deeper issue or trend"
   - etc.

## Root Causes

### Issue 1: Fake URLs
- The prompt didn't have strong enough warnings against inventing URLs
- No explicit examples of what NOT to do
- No clear instruction to leave sources empty if none are provided

### Issue 2: Generic Structure
- Lines 538-543 and 639-644 in `newsletter_generator.py` had a hardcoded generic template
- The AI was just copying this template instead of generating topic-specific structure points

## Fixes Applied

### Fix 1: Strengthened Anti-Hallucination Warnings for Sources

**Location:** `newsletter_generator.py`, lines ~688-704

**Before:**
```python
🚨 CRITICAL - DO NOT LIE 🚨
- Do NOT invent news, statistics, or specific claims
- Use "[TOPIC]" and "[USER TO ADD]" placeholders where the user needs to add real information
- Suggest search terms to help user find real sources
```

**After:**
```python
🚨 CRITICAL - DO NOT INVENT SOURCES OR URLs 🚨

**SOURCES - CRITICAL RULES:**
1. **DO NOT INVENT URLs** - NEVER create fake article URLs like "https://techcrunch.com/2025/..." or "https://wired.com/ai-health"
2. **DO NOT INVENT ARTICLE TITLES** - NEVER create fake article headlines
3. **ONLY USE PROVIDED SOURCES** - If Knowledge Base or sources are provided above, use ONLY those URLs
4. **IF NO SOURCES PROVIDED** - Set "sources": [] (empty array) or use "suggested_links" with search terms ONLY
5. **FORMAT FOR SOURCES** - If sources ARE provided above with URLs, use them. Otherwise leave sources empty.

**Example of WRONG (inventing URLs):**
❌ "sources": [{"title": "Google removes AI health summaries", "url": "https://techcrunch.com/2025/12/google-ai-health"}]

**Example of CORRECT (no sources provided):**
✅ "sources": []
✅ "suggested_links": ["Search: 'Google AI health summaries removed 2025'", "Search: 'AI healthcare accuracy issues'"]

**IF YOU DON'T HAVE A REAL URL FROM THE KNOWLEDGE BASE OR PROVIDED SOURCES ABOVE, DO NOT CREATE ONE.**
```

### Fix 2: Made Story Structure Topic-Specific

**Location:** `newsletter_generator.py`, lines ~538-550 and ~639-651

**Before (Generic Template):**
```json
"structure": [
    "Opening: Hook with a specific example or anecdote",
    "Context: Why this matters now",
    "Analysis: The deeper issue or trend", 
    "Examples: 2-3 specific cases or data points",
    "Global South angle: How this affects Africa/developing world",
    "Takeaway: What readers should do or think about"
],
"key_points": [
    "Key insight 1 to develop",
    "Key insight 2 to develop",
    "Key insight 3 to develop"
]
```

**After (Topic-Specific Prompts):**
```json
"structure": [
    "Opening: [Specific hook for THIS story - not generic]",
    "Context: [Why THIS specific issue/topic matters now]",
    "Analysis": [The specific angle or insight for THIS story]", 
    "Examples: [What specific examples/data will illustrate THIS point]",
    "Impact: [How THIS affects readers/industry/region]",
    "Takeaway: [What readers should specifically do or think about THIS]"
],
"key_points": [
    "Key insight 1 specific to THIS idea",
    "Key insight 2 specific to THIS idea",
    "Key insight 3 specific to THIS idea"
]
```

**Changes:**
1. Replaced generic labels with placeholders that demand specificity: `[Specific hook for THIS story]`
2. Added emphasis on "THIS story", "THIS idea", "THIS specific issue"
3. Changed "Global South angle" to "Impact" (more general, less prescriptive)
4. Made it clear these are PROMPTS for the AI to fill in, not template text to copy

## Impact

**Before:**
- AI would copy generic template → User sees "Opening: Hook with a specific example or anecdote"
- AI would invent URLs → User sees fake sources like `https://techcrunch.com/fake-article`

**After:**
- AI must generate topic-specific structure → User sees "Opening: Start with Google's announcement about removing AI health summaries after accuracy issues"
- AI warned NOT to invent URLs → If no sources provided, leaves sources empty or uses search suggestions only

## Testing

To verify these fixes work:

1. **Restart the app:**
   ```bash
   cd /Users/paulmcnally/Developai\ Dropbox/Paul\ McNally/DROPBOX/ONMAC/PYTHON\ 2025/substack/newsletter_optimizer
   ./stop_app.sh
   ./start_app.sh
   ```

2. **Test Story Structure:**
   - Go to Write tab → Step 1
   - Enter a topic (e.g., "AI health summaries removed by Google")
   - Click "Generate Outline"
   - Check that the structure is specific to the topic, not generic template text

3. **Test Fake URLs:**
   - Generate an outline WITHOUT adding sources first
   - Check that "sources" array is empty OR uses "suggested_links" with search terms
   - NO invented URLs should appear

## Files Modified

- `newsletter_optimizer/newsletter_generator.py` - Both fixes applied

## Related Issues

- This fixes **outline generation** (Step 2)
- Previous fixes addressed **newsletter generation** (Step 3)
- These are two separate stages with different prompts

---

**Status:** ✅ Fixed - Awaiting testing after app restart
**Date:** January 13, 2026
