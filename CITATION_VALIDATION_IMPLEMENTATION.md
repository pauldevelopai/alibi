# Citation Validation & Repair Loop Implementation - January 13, 2026

## Summary

Implemented deterministic citation validation and one-retry repair loop to ensure generated newsletters properly cite evidence from the Evidence Pack, with no hallucinated citation IDs.

## What Was Implemented

### 1. Deterministic Citation Validators (No Model Calls)

#### `validate_citations(draft_text, evidence_ids)` ✅

Checks for two types of citation issues:

**Invalid Citation IDs:**
- Extracts all `[ID]` citations using regex
- Identifies IDs not in the allowed `evidence_ids` list
- Returns list of invalid IDs

**Missing Citations:**
- Splits text into sentences
- Flags sentences containing factual markers WITHOUT citations
- Factual markers: "according to", "report", "study", "%", "million", "billion", "survey", "data", "researchers", "found", "statistics"
- Returns list of problematic sentences

**Returns:**
```python
{
    'missing_citations_sentences': List[str],
    'invalid_citation_ids': List[str],
    'citation_count': int,  # Valid citations only
    'passed': bool  # True if no issues
}
```

**Location:** `newsletter_engine.py`, line ~42

#### `validate_ps_citations(draft_text, must_use_min)` ✅

Validates minimum required provided-source (PS_*) citations:

- Counts unique `[PS_*]` citations
- Compares to `must_use_min` requirement
- Returns pass/fail status

**Returns:**
```python
{
    'ps_citation_count': int,
    'ps_required': int,
    'ps_passed': bool
}
```

**Location:** `newsletter_engine.py`, line ~93

### 2. One-Retry Repair Loop in `NewsletterGenerator.generate()` ✅

**Flow:**

1. **Generate initial draft**
2. **Run citation validators:**
   - `validate_citations(content, evidence_ids)`
   - `validate_ps_citations(content, must_use_min)` (if applicable)
3. **If validation fails:**
   - Build repair prompt with:
     - Evidence Pack (re-rendered with IDs)
     - Failing draft
     - Audit reports (specific issues found)
     - Fix-only instructions
   - Make ONE additional model call
   - Re-validate repaired output
   - Log results
4. **Store audit in metadata:**
   ```python
   metadata['citation_audit'] = {
       'citations': citation_audit,
       'ps': ps_audit,  # if applicable
       'repaired': bool
   }
   ```

**Console Output Example:**
```
⚠️  Citation validation failed - attempting repair...
   - Invalid citation IDs: ['FAKE_1', 'MADE_UP_2']
   - Missing citations: 3 sentences
   - PS citations: 0/2
✅ Repair complete - Citations now valid: True
   PS citations: 2/2
```

**Location:** `newsletter_engine.py`, line ~2373 (in `generate()` method)

### 3. Repair Prompt Builder ✅

#### `_build_repair_prompt()` 

Constructs targeted repair prompt that includes:

1. **Evidence Pack** - Re-rendered with IDs and snippets
2. **Problems Found** - Specific issues from validators:
   - Invalid IDs with names
   - Missing citation sentences (up to 3 examples)
   - PS citation shortfall
3. **Failing Draft** - Original generated text
4. **Fix-Only Instructions:**
   - Use only IDs from Evidence Pack
   - Add missing citations
   - Replace/remove invalid citations
   - Meet PS requirement
   - DON'T change content otherwise

**Location:** `newsletter_engine.py`, line ~2323

### 4. Regression Tests ✅

#### `test_citation_validation.py` - 8 Tests

All tests pass ✅:

1. **test_invalid_citation_id_detected** - `[FAKE_1]` is flagged when not in evidence_ids
2. **test_missing_citation_sentence_flagged** - "According to a report, X" without citation is flagged
3. **test_factual_sentence_with_citation_passes** - "According to [PS_1], X" passes
4. **test_multiple_factual_markers** - All factual indicators detected
5. **test_ps_citation_requirement** - PS count validation works
6. **test_ps_citation_unique_count** - Duplicate [PS_1] counts as 1
7. **test_citation_count_valid_only** - Only valid IDs counted
8. **test_no_issues_passes** - Properly cited text passes all checks

**Usage:**
```bash
cd newsletter_optimizer
python test_citation_validation.py
```

**Result:**
```
✅ ALL 8 TESTS PASSED
```

#### `test_prompt_wiring_regression.py` - Added Evidence Pack Test

**New test:** `test_evidence_pack_present_in_compiled_prompt`

Verifies:
- `# EVIDENCE PACK` section exists in compiled prompt
- Bracketed IDs like `[PS_1]`, `[VP_2]` are present (regex: `\[[A-Z]+_\d+\]`)
- `metadata['evidence_ids']` exists and contains list
- IDs in prompt match IDs in metadata

**Usage:**
```bash
python -m unittest test_prompt_wiring_regression.PromptWiringRegressionTests.test_evidence_pack_present_in_compiled_prompt -v
```

**Result:**
```
✅ OK
✅ Evidence Pack wiring verified:
   - Found 13 bracketed IDs in prompt
   - Metadata contains 9 evidence IDs
   - Sample IDs: ['VP_2', 'VP_1', 'VP_3', 'VP_4', 'VP_5']
```

## Acceptance Criteria - All Met ✅

### 1. ✅ Tests Pass
- `test_citation_validation.py`: 8/8 tests pass
- `test_prompt_wiring_regression.py`: Evidence pack test passes
- No linter errors

### 2. ✅ Draft with `[FAKE_1]` Triggers Repair
When `generate()` produces draft containing invalid citation IDs:
- Repair loop activates automatically
- Console shows warning with specific issues
- One repair attempt made
- Re-validation runs
- Final output either fixed or flagged

### 3. ✅ Metadata Includes `citation_audit`
```python
result.metadata['citation_audit'] = {
    'citations': {
        'missing_citations_sentences': [...],
        'invalid_citation_ids': [...],
        'citation_count': int,
        'passed': bool
    },
    'ps': {  # if must_use_min > 0
        'ps_citation_count': int,
        'ps_required': int,
        'ps_passed': bool
    },
    'repaired': bool
}
```

## Key Design Decisions

### 1. Hard-Capped at 1 Retry
- No infinite loops
- If repair fails, keep repaired attempt (even if not perfect)
- Log clearly shows repair status

### 2. Deterministic Validation (No Model Calls)
- Fast - regex and string operations only
- Reliable - no LLM uncertainty
- Testable - predictable outputs

### 3. Sentence-Level Granularity
- Simple split on `.!?` is sufficient
- Catches most factual claims
- False positives are acceptable (better than missing citations)

### 4. PS Citations Counted Uniquely
- `[PS_1]` used 3 times = 1 unique citation
- Prevents gaming the counter
- Matches semantic intent

### 5. Repair Prompt is Fix-Only
- Explicitly forbids adding new facts
- Explicitly forbids adding new URLs
- Shows same Evidence Pack as original
- Clear instructions on what's wrong

## Usage Example

```python
from newsletter_engine import NewsletterGenerator

generator = NewsletterGenerator()

# Generate with automatic citation validation + repair
result = generator.generate(
    outline="...",
    target_length=800,
    model="gpt-4o"
)

# Check citation audit
audit = result.metadata.get('citation_audit', {})
if audit.get('repaired'):
    print("⚠️ Draft was repaired for citation issues")

if not audit['citations']['passed']:
    print(f"⚠️ Still has issues:")
    print(f"  Invalid IDs: {audit['citations']['invalid_citation_ids']}")
    print(f"  Missing: {len(audit['citations']['missing_citations_sentences'])} sentences")
```

## Future Enhancements

Consider:
1. Track repair success rate over time
2. Add stricter post-repair validation (fail hard if still broken)
3. Extract factual sentences using NER instead of regex
4. Validate that cited evidence is relevant to claim
5. Check for citation density (too many citations is also bad)

## Files Modified

- `newsletter_optimizer/newsletter_engine.py`
  - Added `validate_citations()` function
  - Added `validate_ps_citations()` function
  - Added `_build_repair_prompt()` method
  - Modified `generate()` method with repair loop
- `newsletter_optimizer/test_citation_validation.py` - New file (8 tests)
- `newsletter_optimizer/test_prompt_wiring_regression.py` - Added evidence pack test

## Testing Results

### Citation Validation Tests
```
✅ test_invalid_citation_id_detected passed
✅ test_missing_citation_sentence_flagged passed
✅ test_factual_sentence_with_citation_passes passed
✅ test_multiple_factual_markers passed
✅ test_ps_citation_requirement passed
✅ test_ps_citation_unique_count passed
✅ test_citation_count_valid_only passed
✅ test_no_issues_passes passed

✅ ALL 8 TESTS PASSED
```

### Prompt Wiring Regression Test
```
✅ test_evidence_pack_present_in_compiled_prompt ... ok
✅ Evidence Pack wiring verified:
   - Found 13 bracketed IDs in prompt
   - Metadata contains 9 evidence IDs
```

---

**Status:** ✅ Complete and tested
**Date:** January 13, 2026
**No new dependencies required**
