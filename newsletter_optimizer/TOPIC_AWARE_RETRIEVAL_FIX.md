# Topic-Aware Fact Retrieval Fix

## Problem: Wrong Facts in Prompts

Despite implementing topic relevance filtering, the generated prompts still contained **irrelevant facts**:

```
# FACTS AND DATA TO USE
1. We like to complain about 'AI slop'... (Instagram article)
2. OpenAI shows employees save an hour... (AI Labor)
6. OpenAI offering $5,000 to $100,000... (Grantwashing)
```

**For a Grok deepfakes newsletter!** These facts had nothing to do with Grok, deepfakes, or non-consensual imagery.

## Root Cause

**The retrieval order was wrong**:

1. ❌ Retrieve facts via semantic search (12 facts)
   - Queries: "AI ethics", "platform accountability" (too broad)
   - Matches: Instagram trust, AI labor, OpenAI grants
2. ❌ Build topic signature AFTER facts retrieved
3. ❌ Try to filter facts - but irrelevant ones already selected

**Flow was**: `semantic_search()` → `filter()` → ❌ Too late!

## Solution: Topic-Aware Retrieval

**New order**:

1. ✅ Build compiler outline (has headline, preview, sources)
2. ✅ Build topic signature EARLY (entities, keywords from theme/provided sources)
3. ✅ Retrieve LARGER pool via semantic search (48 facts instead of 12)
4. ✅ Filter immediately by topic signature
5. ✅ Return top 12 relevant facts

**Flow is now**: `topic_sig()` → `semantic_search(large_pool)` → `filter()` → ✅ Relevant facts!

## Implementation Changes

### 1. Reordered `build_prompt()` Flow

**Before**:
```python
analysis = self.analyze_outline(outline)
facts = self.get_relevant_facts(analysis)  # Gets 12 facts
# ...later...
topic_sig = build_topic_signature(...)
facts, metrics = self.filter_facts_by_topic(facts, topic_sig, ...)  # Too late!
```

**After**:
```python
analysis = self.analyze_outline(outline)
compiler_outline = self.compile_outline(...)  # Build early
topic_sig = build_topic_signature(...)         # Build early
facts = self.get_relevant_facts(analysis, topic_sig=topic_sig, provided_sources=sources)  # Filter during retrieval
```

### 2. Enhanced `get_relevant_facts()`

**Before**: Retrieved 12 facts total
**After**: Retrieves 48 facts, filters by topic, returns top 12

```python
def get_relevant_facts(self, analysis, max_facts=12, topic_sig=None, provided_sources=None):
    # Retrieve LARGER pool (4x desired)
    retrieval_pool_size = max_facts * 4  # 48 instead of 12
    
    # Get more results per query
    results_per_query = 8  # Instead of 5
    
    # Semantic search returns ~48 facts
    # ...
    
    # TOPIC-AWARE FILTERING during retrieval
    if topic_sig and provided_sources is not None:
        filtered_facts, metrics = self.filter_facts_by_topic(
            all_facts[:retrieval_pool_size],
            topic_sig,
            provided_sources
        )
        self.last_fact_filter_metrics = metrics  # Store for metadata
        return filtered_facts[:max_facts]
```

### 3. Stricter Relevance Scoring

**Thresholds increased**:
```python
FACT_MIN_RELEVANCE_SCORE = 3.0  # Was 2.0
KB_MIN_RELEVANCE_SCORE = 3.0    # Was 2.0
```

**Dual requirement**: Facts must:
- Score >= 3.0 (entity +3, keywords +1-5, exclude -6)
- **AND** mention at least ONE topic term (entity or keyword)

```python
mentions_topic = any(term in fact_lower for term in topic_terms)

if score >= 3.0 and mentions_topic:
    relevant_facts.append(fact)
else:
    dropped.append(fact)
    print(f"Dropped fact (low score {score:.1f}): {source_title[:50]}")
```

## Results

### Console Output Shows Filtering

```
Dropped fact (low score 0.0): You can't trust your eyes... (Instagram)
Dropped fact (low score -4.0): AI Labor Is Boring...
Dropped fact (low score -2.0): Beware of OpenAI's 'Grantwashing'...
Dropped fact (low score -2.0): Investors predict AI is coming for labor...
Dropped fact (low score 0.0): How Bari Keenam made job rejections...
```

### Tests Confirm Clean Prompts

```bash
python3 -m unittest discover -s . -p "test_*.py"
# Ran 34 tests in 27s
# OK

python3 scripts/run_pipeline_diagnostics.py
# Total scenarios: 7
# Passed: 7
# Failed: 0
```

### Demonstration Script

```bash
python3 demo_strict_filtering.py
```

**Output**:
```
FACTS BEFORE FILTERING: 5
FACTS AFTER FILTERING: 2

1. Grok generated 10,000 non-consensual deepfake images...
2. X platform lacks verification for synthetic media...

✅ SUCCESS: Irrelevant facts were filtered out!

Dropped facts:
  - You can't trust your eyes anymore (Instagram)
  - Beware of OpenAI's Grantwashing
  - AI Labor Is Boring
```

## Expected Behavior in Streamlit

### When you generate a Grok deepfakes newsletter:

**Before**:
- 8 facts about Instagram, AI labor, OpenAI grants, college dropouts
- Only 1-2 facts about Grok/deepfakes

**After**:
- Maximum 8 facts, ALL about Grok, deepfakes, X platform, synthetic media, hijabs
- Irrelevant facts dropped (you'll see console messages)
- Opening hook automatically sanitized if unsafe

### Console Output During Generation

```
⚠️ Opening hook sanitized for safety
Dropped fact (low score 0.0): You can't trust your eyes...
Dropped fact (low score -4.0): Beware of OpenAI's 'Grantwashing'...
Dropped fact (low score -2.0): AI Labor Is Boring...
```

## How It Works with Diverse KB

Your Knowledge Base contains articles on:
- African tech entrepreneurship
- AI ethics and grantwashing  
- Platform accountability
- Deepfakes and verification
- Health, climate, business topics

**For each newsletter**:
1. Topic signature identifies key entities/keywords (e.g., "Grok", "deepfake", "hijabs")
2. Semantic search retrieves ~48 candidate facts
3. Filter scores each fact against topic (needs entity OR keyword match + score >= 3.0)
4. Only top 12 relevant facts returned

**Result**: Grok newsletter gets Grok facts, climate newsletter gets climate facts, etc.

## Adjustment Knobs

If too strict (relevant facts dropped):
```python
FACT_MIN_RELEVANCE_SCORE = 2.5  # Lower threshold
```

If too loose (irrelevant facts included):
```python
FACT_MIN_RELEVANCE_SCORE = 4.0  # Higher threshold
retrieval_pool_size = max_facts * 6  # Retrieve even more for filtering
```

Current settings (3.0 threshold, 4x pool) work well for diverse KB.

## Files Changed

1. **newsletter_engine.py**:
   - Reordered `build_prompt()` to build topic_sig before retrieving facts
   - Modified `get_relevant_facts()` to accept topic_sig and filter during retrieval
   - Increased pool size from 12 → 48 facts for better filtering
   - Store filtering metrics in `self.last_fact_filter_metrics`

2. **test_prompt_wiring_regression.py** (NEW):
   - Verifies facts filtered in actual compiled prompts
   - Confirms hook sanitization applied
   - All 4 tests passing

3. **demo_strict_filtering.py** (NEW):
   - Demonstrates filtering in action
   - Shows dropped facts with scores

4. **TOPIC_AWARE_RETRIEVAL_FIX.md** (this doc):
   - Complete explanation and verification

---

**Status**: ✅ Topic-aware retrieval working  
**Tests**: 34/34 passing  
**Diagnostics**: 7/7 scenarios passing  
**Result**: KB can contain 1000s of diverse articles, each newsletter gets only relevant facts
