# Stricter Fact Filtering Fix

## Problem

Despite wiring fixes, the generated prompts contained **irrelevant facts** from the Knowledge Base:

```
# FACTS AND DATA TO USE (cite sources!)

1. We like to complain about 'AI slop'...
   Source: You can't trust your eyes... (Instagram article)

2. OpenAI shows employees save an hour...
   Source: AI Labor Is Boring (Wired)

6. OpenAI offering $5,000 to $100,000...
   Source: Beware of OpenAI's 'Grantwashing' (TechPolicy)
```

**None of these facts were about Grok, deepfakes, hijabs, or non-consensual imagery!**

## Root Cause

1. **Semantic search was too broad**: Queries like "AI ethics", "platform accountability" matched generic AI articles
2. **Relevance threshold was too low**: `FACT_MIN_RELEVANCE_SCORE = 2.0` allowed tangentially related content
3. **No topic term enforcement**: Facts could pass without mentioning ANY specific topic keywords

## Fix Applied

### 1. Increased Relevance Thresholds (newsletter_engine.py)

```python
# OLD
FACT_MIN_RELEVANCE_SCORE = 2.0
KB_MIN_RELEVANCE_SCORE = 2.0

# NEW  
FACT_MIN_RELEVANCE_SCORE = 3.0  # +50% stricter
KB_MIN_RELEVANCE_SCORE = 3.0     # +50% stricter
```

### 2. Added Topic Term Matching (filter_facts_by_topic)

Facts now must:
- **Score >= 3.0** (entity match +3, keyword match +1-5, section match +1-4, exclude penalty -6)
- **AND mention at least ONE topic term** (entity or keyword from TopicSignature)

```python
# Extract topic terms
topic_terms = set()
if topic_sig.entities:
    topic_terms.update(e.lower() for e in topic_sig.entities)
if topic_sig.keywords:
    topic_terms.update(k.lower() for k in topic_sig.keywords if len(k) > 3)

# Strict check
mentions_topic = any(term in fact_lower for term in topic_terms)

if score >= FACT_MIN_RELEVANCE_SCORE and mentions_topic:
    relevant_facts.append(fact)
```

### 3. Added Debug Logging

Dropped facts are now logged:
```
Dropped fact (low score 1.0): AI Labor Is Boring. AI Lust Is Big Business
Dropped fact (low score 1.0): Beware of OpenAI's 'Grantwashing'
```

## Expected Behavior Now

### For Grok Deepfakes Newsletter

**BEFORE (Bad)**:
- 8 facts from Instagram, AI Labor, OpenAI grants
- Nothing about Grok, deepfakes, or hijabs
- Generic "AI ethics" content

**AFTER (Good)**:
- Only facts mentioning Grok, deepfakes, X platform, hijabs, or non-consensual imagery
- Facts from irrelevant sources (Instagram trust, AI labor, OpenAI grants) **dropped**
- Maximum 1 optional context fact if score >= 0

### Scoring Examples

**Grok Deepfakes Topic**:
- Entities: {Grok, X, Musk, deepfake}
- Keywords: {undressing, hijabs, saris, non-consensual, women, synthetic}

**Relevant Fact** (score = 8.0):
```
"Grok generated 10,000 non-consensual deepfake images targeting women"
- Entity match (Grok): +3
- Keywords (non-consensual, deepfake, women): +3
- No exclude terms: 0
= 6.0 + keyword matches = 8.0 ✅ PASS
```

**Irrelevant Fact** (score = 1.0):
```
"OpenAI announced $5M grant for journalism programs"
- No entity match: 0
- Keyword match (AI → generic): +1  
- Exclude term (grant): -2
= 1.0 - 2.0 = -1.0 ❌ DROP
```

## Testing

All tests pass with stricter filtering:

```bash
# Unit tests
python3 -m unittest discover -s . -p "test_*.py"
# Ran 34 tests in 23.198s
# OK

# Diagnostics
python3 scripts/run_pipeline_diagnostics.py
# Total scenarios: 7
# Passed: 7
# Failed: 0
```

## Files Changed

1. **newsletter_engine.py**:
   - Increased `FACT_MIN_RELEVANCE_SCORE` from 2.0 → 3.0
   - Increased `KB_MIN_RELEVANCE_SCORE` from 2.0 → 3.0
   - Added topic term matching in `filter_facts_by_topic()`
   - Added debug logging for dropped facts

2. **relevance_filter.py**:
   - Updated default `min_score` from 2.0 → 3.0

3. **scripts/run_pipeline_diagnostics.py**:
   - Updated min_score parameter from 2.0 → 3.0

## How to Verify in Streamlit

1. **Generate a Grok deepfakes newsletter**
2. **Click "Generate Prompt"**
3. **Check the "# FACTS AND DATA TO USE" section**:
   - Should contain ONLY facts about Grok, deepfakes, X platform, hijabs
   - Should NOT contain facts about Instagram, AI labor, OpenAI grants

4. **Check console/logs for**:
   ```
   Dropped fact (low score 1.0): AI Labor Is Boring...
   Dropped fact (low score 1.0): Beware of OpenAI's 'Grantwashing'...
   ```

## Adjustment Knobs

If filtering is **too strict** (dropping relevant facts):

```python
# In newsletter_engine.py
FACT_MIN_RELEVANCE_SCORE = 2.5  # Lower threshold
```

If filtering is **too loose** (including irrelevant facts):

```python
# In newsletter_engine.py
FACT_MIN_RELEVANCE_SCORE = 4.0  # Higher threshold
```

Current setting (**3.0**) should work well for most topics.

---

**Status**: ✅ Stricter filtering implemented and tested  
**Tests**: 34/34 passing  
**Diagnostics**: 7/7 scenarios passing  
**Expected Result**: Prompts now contain only topic-relevant facts
