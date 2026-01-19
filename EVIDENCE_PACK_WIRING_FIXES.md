# Evidence Pack Wiring Fixes - January 13, 2026

## Summary

Implemented complete evidence-pack wiring so that retrieved evidence (sources, KB facts, RAG examples) reaches the model with proper citation IDs.

## Changes Made

### 1. Fixed undefined `relevance_brief` usage in `_build_user_prompt()`

**Problem:** The method referenced `relevance_brief` inside a try/except block (`rb = relevance_brief`) even though it wasn't passed as a parameter, causing potential NameErrors.

**Fix:** 
- Added `relevance_brief: Optional[RelevanceBrief] = None` parameter to `_build_user_prompt()`
- Added `retrieval_pack: Optional[RetrievalPack] = None` parameter  
- Removed the try/except workaround and directly use the parameter
- Changed all references from `rb` to `relevance_brief`

**Location:** `newsletter_engine.py`, line ~1827

### 2. Added "EVIDENCE PACK" section to user prompt

**What:** New section that displays up to 12 evidence excerpts with stable bracket IDs like `[PS_1]`, `[VP_2]`, `[KB_3]`.

**Format:**
```
# EVIDENCE PACK (cite with IDs like [PS_1], [VP_2], etc.)

Use these evidence items in your newsletter. Cite them using their bracket IDs.

[PS_1] AI Adoption in African Media | provided_source | https://example.com/...
Snippet: African newsrooms are increasingly adopting AI tools...

[VP_2] opening_hook | past_newsletter
Snippet: A opening hook that frames AI strategies...
```

**Location:** `newsletter_engine.py`, line ~1950 (SECTION 3.7)

**Features:**
- Shows up to 12 excerpts from `retrieval_pack.excerpts`
- Each has a bracket ID: `[<excerpt.id>]`
- Shows source, source_type, URL (if present)
- Truncates text to ~500 chars
- Provided sources appear as `PS_*` IDs

### 3. Added explicit citation rules to prompt instructions

**What:** Added instruction #7 with explicit rules about citing from Evidence Pack.

**Rules:**
- Every factual claim MUST end with citation like `[PS_1]` or `[KB_3]`
- If cannot cite from Evidence Pack, write "needs verification" or omit claim
- Do NOT invent URLs, publications, or studies
- Use at least N citations (where N = max(3, plan.must_use_provided_sources_min))

**Location:** `newsletter_engine.py`, line ~2035

### 4. Store retrieval pack + evidence IDs in metadata

**What:** Added to metadata dictionary:
- `retrieval_pack`: Full serialized RetrievalPack (asdict)
- `evidence_ids`: List of all excerpt IDs like `['PS_1', 'PS_2', 'VP_1', ...]`

**Why:** Enables downstream auditing and debugging. Always present (empty list if no pack).

**Location:** `newsletter_engine.py`, line ~1723

### 5. Fixed audit usage in `NewsletterGenerator.generate()`

**Problem:** Was incorrectly passing `anchored_outline` to `audit_coverage(pack=...)`, but the audit function expects a RetrievalPack to inspect excerpts.

**Fix:**
```python
# Extract correct objects for audit
pack_for_audit = metadata.get('retrieval_pack', {})
anchored_outline_for_audit = metadata.get('anchored_outline', {})

audit_report = self.prompt_constructor.audit_coverage(
    plan=metadata.get('newsletter_plan', {}),
    pack=pack_for_audit,  # Now passes retrieval_pack, not anchored_outline
    outline=outline,
    draft_text=content
)
```

**Location:** `newsletter_engine.py`, line ~2275

### 6. Created demo script to verify wiring

**File:** `scripts/demo_prompt_evidence_pack.py`

**What it does:**
- Builds a prompt from minimal outline + 2 provided sources
- Runs without OpenAI API calls
- Checks for:
  - `# RELEVANCE BRIEF` section presence
  - `# EVIDENCE PACK` section presence
  - Evidence IDs like `[PS_1]`, `[PS_2]`
  - `metadata['retrieval_pack']` present
  - `metadata['evidence_ids']` present
- Prints sample of Evidence Pack section
- Exits with code 0 if all checks pass

**Usage:**
```bash
cd newsletter_optimizer
python scripts/demo_prompt_evidence_pack.py
```

**Output:**
```
✅ RELEVANCE BRIEF section present: True
✅ EVIDENCE PACK section present: True
✅ Evidence ID [PS_1] found: True
✅ Evidence ID [PS_2] found: True
✅ metadata['retrieval_pack'] present: True
✅ metadata['evidence_ids'] present: True
✅ ALL CHECKS PASSED - Evidence pack wiring is working correctly!
```

## Testing Results

Demo script ran successfully on first try:
- All 6 checks passed ✅
- Evidence Pack section renders correctly
- Bracket IDs appear as expected: `[PS_1]`, `[PS_2]`, `[VP_1]`, etc.
- Metadata contains retrieval_pack and evidence_ids
- No NameErrors or undefined variable issues

## Benefits

1. **Traceable citations:** Model can now cite sources with IDs like `[PS_1]` that map back to specific evidence
2. **No URL hallucination:** Model has explicit IDs to cite instead of inventing URLs
3. **Auditable:** All evidence IDs stored in metadata for post-generation verification
4. **Correct audit flow:** audit_coverage() now receives retrieval_pack to properly inspect excerpts
5. **No undefined variables:** relevance_brief properly passed through call chain

## Files Modified

- `newsletter_optimizer/newsletter_engine.py` - All 5 code fixes
- `newsletter_optimizer/scripts/demo_prompt_evidence_pack.py` - New demo script

## Backward Compatibility

- All parameters are optional (default to `None`)
- Existing tests should continue to work
- If `retrieval_pack` is None, EVIDENCE PACK section simply won't appear
- Metadata always has `evidence_ids` (empty list if none)

## Next Steps

Consider:
1. Add post-generation verification that checks if output contains expected citation IDs
2. Update audit_coverage() to validate that excerpts were actually used
3. Add warning if fewer than required citations appear in output
4. Track citation usage stats in metadata

---

**Status:** ✅ Complete and tested
**Date:** January 13, 2026
