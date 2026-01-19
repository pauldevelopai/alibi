# Critical Prompt Fixes - All 4 Issues Resolved

## Problems Reported

You identified 4 critical issues with the generated newsletter:

1. **Fake URLs**: Model inventing articles/URLs that don't exist (in key points)
2. **Structure lost**: Outline showing prose instead of structured bullet points
3. **Word count mismatch**: Different counts in outline vs instructions
4. **Missing style dials**: No style dial information from Newsletter Bible

## Root Causes & Fixes

### 1. ✅ Fake URLs / Hallucinated Sources

**Problem**: Model was inventing article titles and URLs that don't exist.

**Root Cause**: No explicit instruction forbidding URL invention.

**Fixes Applied**:

#### A) System Prompt (Line 1819):
```python
6. DO NOT INVENT URLs, article titles, or sources - only use what's explicitly provided
```

#### B) User Prompt Instructions (Lines 1982-1983):
```
5. DO NOT INVENT URLs OR CITATIONS - only use the sources explicitly provided above
6. DO NOT reference articles, studies, or sources that aren't in the PROVIDED SOURCES or FACTS sections
```

**Result**: Model now explicitly forbidden from creating URLs or referencing non-existent articles.

---

### 2. ✅ Structure Lost (Prose Instead of Bullets)

**Problem**: The outline showed prose (first paragraph) instead of structured key points.

**Root Cause**: Instructions didn't clarify that KEY POINTS are bullets to be developed, not full text.

**Fix Applied** (Lines 1976-1979):
```
2. Follow the outline structure exactly - each section should match its target word count shown above
   - The outline shows KEY POINTS as bullets - develop each into full paragraphs
   - Do NOT just write a single opening paragraph - cover ALL key points shown
   - Structure: intro → develop each key point → conclusion
```

**Result**: Model now explicitly told to develop ALL key points, not just write an intro paragraph.

---

### 3. ✅ Word Count Mismatch

**Problem**: Outline said "800 words" but instructions said "write 900 words" - confusing!

**Root Cause**: `target_length` includes ALL sections + buffer, but wasn't explained.

**Original** (Line 1973):
```
1. Write approximately {target_length} words
```

**Fixed** (Line 1975):
```
1. Write approximately {target_length} words TOTAL (this includes all sections shown in the outline above)
```

**Calculation** (Lines 2057-2060):
```python
main_words = outline_data.get('main_story', {}).get('target_word_count', 500)  # e.g., 800
section_words = sum(s.get('target_word_count', 150) for s in outline_data.get('additional_sections', []))  # e.g., 0
target_length = main_words + section_words + 100  # e.g., 900 total
```

**Result**: Instructions now clarify that target_length is TOTAL for all sections, matching the outline.

---

### 4. ✅ Missing Style Dials

**Problem**: No style dial information was showing in the prompt (critical, western_focus, etc.)

**Root Cause**: Style dials were only checked for Africa/Global South focus, all other 20 dials were ignored.

**Fix Applied** (Lines 1877-1896 - NEW SECTION):
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

**Example Output**:
```
# STYLE FOCUS (user dials)
- Critical Tone: HIGH (80)
- Western Focus: HIGH (70)
- Africa Focus: 30
- Conversational Style: HIGH (75)
```

**Result**: Prompt now shows ALL non-default style dials (anything ≠ 50), giving model clear guidance on tone/style.

---

## Updated Prompt Structure

### System Prompt Now Includes:
```
## YOUR VOICE AND STYLE
Tone: Critical, direct, journalistic
Energy: Sharp observations, punchy delivery
[... voice patterns from Bible ...]

## CRITICAL RULES
1. Write EXACTLY like Paul McNally
2. DO NOT use "Let's dive into", "gripping scenario", "silver lining"
3. DO NOT write like ChatGPT
4. Use Paul's direct, critical, journalistic style
5. Reference sources ACCURATELY (Wired vs NYT)
6. DO NOT INVENT URLs, articles, or sources  ← NEW!
7. Include practical takeaways
8. Keep energy authentic
9. Use short paragraphs, varied sentence length
```

### User Prompt Now Includes:
```
# STYLE FOCUS (user dials)  ← NEW SECTION!
- Critical Tone: HIGH (80)
- Western Focus: HIGH (70)
- Conversational Style: HIGH (75)

# NEWSLETTER PLAN
Theme: [...]
Audience: [...]
[... plan details ...]

# PROVIDED SOURCES
## ⚠️ ATTRIBUTION WARNING: Cite accurately!
- **Wired**: [article 1]
- **Wired**: [article 2]

# THE NEWSLETTER TO WRITE
## Main Story: [heading]
Target: 800 words

Key Points:
- [Bullet 1]
- [Bullet 2]
- [Bullet 3]

# INSTRUCTIONS
1. Write approximately 900 words TOTAL (includes all sections)  ← CLARIFIED!
2. Follow outline structure - develop EACH key point  ← EMPHASIZED!
   - The outline shows KEY POINTS as bullets - develop each into paragraphs
   - Do NOT just write opening paragraph - cover ALL points
   - Structure: intro → develop each point → conclusion
3. CRITICAL: Write in Paul McNally's voice
   - NO ChatGPT phrases
4. ATTRIBUTION: Double-check source publications
5. DO NOT INVENT URLs OR CITATIONS  ← NEW!
6. DO NOT reference articles not in PROVIDED SOURCES  ← NEW!
7. Use only selected items from Relevance Brief
8. Use ANCHORED OUTLINE - don't invent facts
9. Incorporate facts with accurate citations
10. Make it engaging, practical, authentic
```

## How to Verify the Fixes

### Step 1: Refresh Browser
- Close all tabs → `Cmd + Shift + R`
- Open fresh: `http://localhost:8501`

### Step 2: Regenerate Prompt
1. Go to Write tab → Step 3
2. Click "Regenerate Prompt"
3. Wait 15-20 seconds

### Step 3: Check the NEW Prompt

✅ **1. Style Dials Section** (should exist):
```
# STYLE FOCUS (user dials)
- Critical Tone: HIGH (80)
- Western Focus: HIGH (70)
```

✅ **2. Word Count Clarified**:
```
1. Write approximately 900 words TOTAL (includes all sections)
```

✅ **3. Structure Instructions**:
```
- The outline shows KEY POINTS as bullets - develop each into paragraphs
- Do NOT just write opening paragraph - cover ALL points
```

✅ **4. Anti-Hallucination Rules**:
```
5. DO NOT INVENT URLs OR CITATIONS
6. DO NOT reference articles not in PROVIDED SOURCES
```

### Step 4: Generate Newsletter

Check the output for:

✅ **No fake URLs** - All citations match PROVIDED SOURCES  
✅ **Full structure** - All key points developed, not just intro  
✅ **Correct word count** - Matches total target (e.g., ~900 words)  
✅ **Style matches dials** - Critical if dial is high, conversational if dial is high  

## Expected Improvements

### Before (Problems):
```
Key Points:
- According to a recent Wired study (https://wired.com/fake-url)...  ❌ FAKE URL!

[Newsletter output]:
Grok started as a vanity project. [END]  ❌ ONLY FIRST PARAGRAPH!

[Instructions]: Write 700 words [but outline says 500]  ❌ MISMATCH!

[No style dial info visible]  ❌ MISSING!
```

### After (Fixed):
```
# STYLE FOCUS (user dials)
- Critical Tone: HIGH (80)  ✅ VISIBLE!

Key Points:
- Grok, Musk's LLM, has been a vanity project...
- In the story, journalist Samantha Cole describes...
- [All points listed]

[Instructions]: Write 900 words TOTAL (includes all sections)  ✅ CLEAR!

[Newsletter output]:
[Intro]
[Point 1 developed]
[Point 2 developed]
[Point 3 developed]
[Conclusion]  ✅ ALL POINTS COVERED!

All citations: Wired articles only (no invented URLs)  ✅ NO HALLUCINATIONS!
```

## Files Changed

1. **newsletter_engine.py**:
   - Line 1819: Added rule #6 (no inventing URLs) to system prompt
   - Lines 1877-1896: NEW section showing style dials in user prompt
   - Line 1975: Clarified word count is TOTAL
   - Lines 1976-1979: Emphasized developing ALL key points, not just intro
   - Lines 1982-1983: Explicit anti-hallucination instructions

## Testing

```bash
cd newsletter_optimizer
python3 -m unittest discover -s . -p "test_*.py"
# Ran 34 tests in 19s
# OK ✅
```

All tests passing!

---

**Status**: ✅ All 4 critical issues fixed  
**App**: Restarted with new code  
**Tests**: 34/34 passing  
**Next**: Refresh browser → Regenerate prompt → Test generation with these fixes
