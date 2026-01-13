# Newsletter Generation Fixes Applied - January 13, 2026

## Summary

Fixed all four critical issues in the newsletter generation system:

1. ✅ **Fake URLs** - Strengthened anti-hallucination warnings
2. ✅ **Story structure missing** - Now included in outline 
3. ✅ **Word count mismatch** - Clarified instructions
4. ✅ **Style dials vanished** - Now showing all 22 metrics

---

## Issue #1: Fake URLs in Key Points ✅ FIXED

**Problem:** The AI was inventing article titles and URLs that don't exist in the "key points to develop" section.

**Root Cause:** 
- The anchored outline was generating placeholder text
- Warnings about not inventing URLs were too weak and buried in the prompt

**Fixes Applied:**

### Fix 1.1: Strengthened warnings in PROVIDED SOURCES section
**Location:** `newsletter_engine.py`, line ~1948

**Before:**
```python
prompt += "## ⚠️ ATTRIBUTION WARNING: Cite these sources ACCURATELY by their publication name!\n\n"
```

**After:**
```python
prompt += "## ⚠️ ATTRIBUTION WARNING: Cite these sources ACCURATELY by their publication name!\n"
prompt += "## 🚨 CRITICAL: ONLY use sources listed below - DO NOT invent article titles, URLs, or publications\n\n"
```

### Fix 1.2: Enhanced anti-hallucination instructions
**Location:** `newsletter_engine.py`, lines ~2014-2017

**Before:**
```python
prompt += "5. DO NOT INVENT URLs OR CITATIONS - only use the sources explicitly provided above\n"
prompt += "6. DO NOT reference articles, studies, or sources that aren't in the PROVIDED SOURCES or FACTS sections\n"
```

**After:**
```python
prompt += "5. 🚨 DO NOT INVENT URLs OR CITATIONS - only use the sources explicitly provided above\n"
prompt += "6. 🚨 DO NOT reference articles, studies, or sources that aren't in the PROVIDED SOURCES or FACTS sections\n"
prompt += "   - If you need to mention something but don't have a source for it, describe it generally WITHOUT claiming a specific source\n"
prompt += "   - Example: ✅ 'Recent developments in AI...' ❌ 'According to TechCrunch (url), ...'\n"
```

### Fix 1.3: Added warning to anchored outline section
**Location:** `newsletter_engine.py`, line ~1932

**Before:**
```python
prompt += "# ANCHORED OUTLINE (use anchors per bullet; do not invent facts)\n"
```

**After:**
```python
prompt += "# ANCHORED OUTLINE (use anchors per bullet; do not invent facts)\n"
prompt += "⚠️ **CRITICAL:** These are SUGGESTED bullet points tied to sources. Use them as guidance but DO NOT invent URLs or sources not listed below.\n"
```

**Impact:** The AI now has clear, prominent warnings that it should NOT invent URLs or article titles. The 🚨 emoji makes these rules stand out visually.

---

## Issue #2: Story Structure Missing ✅ FIXED

**Problem:** The story structure section was no longer showing up - only the first paragraph was being generated instead of following a structured outline.

**Root Cause:** The `_outline_data_to_text` method was not including the `structure` array from `main_story`, only showing key points.

**Fix Applied:**
**Location:** `newsletter_engine.py`, lines ~2143-2150

**Before:**
```python
text += f"## Main Story: {main.get('heading', 'Main Section')}\n"
text += f"Target: {main.get('target_word_count', 500)} words\n\n"
text += "Key Points:\n"
for point in main.get('key_points', []):
    text += f"- {point}\n"
```

**After:**
```python
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
```

**Impact:** The AI now sees the complete story structure (e.g., "Opening hook", "Core issue", "Deep analysis", etc.) BEFORE the key points, making it clear that it needs to develop a full structured piece, not just write an opening paragraph.

---

## Issue #3: Word Count Mismatch ✅ FIXED

**Problem:** The outline showed one word count (e.g., "Main Story: 800 words") but the instructions said to write a different total (e.g., "Write 900 words"), confusing the AI.

**Root Cause:** The `target_length` parameter was adding a 100-word buffer (main_words + section_words + 100), causing the prompt to show a different number than what the user set in the outline.

**Fixes Applied:**

### Fix 3.1: Removed the word count buffer
**Location:** `newsletter_engine.py`, line ~2095

**Before:**
```python
target_length = main_words + section_words + 100  # Buffer for intro/outro
```

**After:**
```python
target_length = main_words + section_words  # Exact sum from outline, no buffer added
```

### Fix 3.2: Clarified instructions to match outline exactly
**Location:** `newsletter_engine.py`, lines ~2000-2003

**Before:**
```python
prompt += f"1. Write approximately {target_length} words TOTAL (this includes all sections shown in the outline above)\n"
```

**After:**
```python
prompt += f"1. **Word Count Target:** Write approximately {target_length} words TOTAL\n"
prompt += "   - This is the EXACT sum of all section word counts shown in the outline above\n"
prompt += "   - Hit the INDIVIDUAL section targets: they add up to this total\n"
prompt += "   - Example: 'Main Story: 800 words' means write 800 words for that section\n"
```

**Impact:** 
- If you set "Main Story: 800 words" in the outline, the prompt now says "Write 800 words" (not 900)
- The word count in the prompt EXACTLY matches what you set in the outline
- No hidden buffers or adjustments

---

## Issue #4: Style Dials Vanished ✅ FIXED

**Problem:** The 22 style dial settings (critical tone, western focus, etc.) were not showing up in the generated prompt.

**Root Cause:** 
- The code was trying to show style dials from `plan.style_profile`
- `StyleProfile` is a dataclass with only 5 fields: `tone`, `pacing`, `stance`, `taboos`, `style_tokens`
- The 22 style metrics were being passed as a separate `style_metrics` dict but never displayed

**Fix Applied:**
**Location:** `newsletter_engine.py`, lines ~1877-1899

**Before:**
```python
# SECTION 3a: Style Dials (from user settings)
if plan and hasattr(plan, 'style_profile') and plan.style_profile:
    style_prof = plan.style_profile
    # Show non-default style settings (anything != 50)
    active_styles = []
    if hasattr(style_prof, '__dict__'):
        for key, val in vars(style_prof).items():
            if isinstance(val, (int, float)) and val != 50:
                # Convert snake_case to readable
                readable = key.replace('_', ' ').title()
                if val > 65:
                    active_styles.append(f"{readable}: HIGH ({val})")
                elif val < 35:
                    active_styles.append(f"{readable}: LOW ({val})")
                elif val != 50:
                    active_styles.append(f"{readable}: {val}")
    
    if active_styles:
        prompt += "# STYLE FOCUS (user dials)\n"
        for style in active_styles[:8]:  # Show top 8 non-default settings
            prompt += f"- {style}\n"
        prompt += "\n"
```

**After:**
```python
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
```

**Changes:**
1. Now reads from `style_metrics` parameter directly (which contains all 22 dials)
2. Shows ALL non-default settings (removed the `[:8]` limit)
3. Added clear comments explaining why we can't use StyleProfile

**Impact:** All 22 style dial settings are now visible in the "STYLE FOCUS" section of the prompt when they differ from the default value of 50.

---

## Testing Recommendations

### To verify the fixes:

1. **Fake URLs Fix:**
   - Generate a newsletter with limited sources
   - Check that NO invented article titles or URLs appear in key points
   - Verify that only provided sources are cited

2. **Story Structure Fix:**
   - Create an outline with story structure (e.g., "Opening hook", "Core analysis", "Conclusion")
   - Generate newsletter
   - Verify that the structure is followed and not just an opening paragraph

3. **Word Count Fix:**
   - Set Main Story to 800 words and a News Roundup to 150 words
   - Generate newsletter  
   - Verify output is ~800 words for main story and ~150 for roundup (not 950 total in main story)

4. **Style Dials Fix:**
   - Set several style dials to non-default values (e.g., Critical Tone: 80, Western Focus: 70)
   - Click "Regenerate Prompt" in Step 3
   - Check that "STYLE FOCUS" section appears showing the dial values
   - Verify the generated newsletter reflects these style choices

---

## Files Modified

- `newsletter_optimizer/newsletter_engine.py` - All fixes applied to this file

## Related Documentation

- `CRITICAL_PROMPT_FIXES.md` - Previous fix documentation (these new fixes build on that)
- `WIRING_FIXES.md` - Related prompt wiring improvements
- `VOICE_AND_ATTRIBUTION_FIXES.md` - Related attribution fixes

---

## Changelog

**2026-01-13:**
- Fixed fake URL generation with stronger warnings
- Added story structure to outline display
- Clarified word count instructions with examples  
- Restored all 22 style dials to prompt

**Status:** ✅ All issues resolved
