# Newsletter Pipeline Diagnostics

End-to-end validation script for the newsletter generation pipeline.

## Purpose

Validates that the newsletter pipeline maintains critical invariants across diverse topics:
- **No drift**: KB and facts are topic-relevant, not generic/unrelated
- **Must-use sources**: Provided sources are anchored in generated outlines
- **Semantic outlines**: Bullets are specific, not placeholders
- **Safe hooks**: Visual prompts sanitized to prevent harmful imagery

## Usage

```bash
# Run all 7 scenarios
python3 scripts/run_pipeline_diagnostics.py

# Run with verbose output (shows per-check details)
python3 scripts/run_pipeline_diagnostics.py --verbose

# Run a single scenario
python3 scripts/run_pipeline_diagnostics.py --scenario "Climate"
python3 scripts/run_pipeline_diagnostics.py --scenario "adversarial"

# Output results as JSON
python3 scripts/run_pipeline_diagnostics.py --json
```

## Test Scenarios

1. **AI Policy**: EU AI Act enforcement and newsroom compliance
2. **Climate**: Flood early-warning systems in Mozambique
3. **Health**: Antibiotic resistance and informal pharmacies
4. **Politics**: Election disinformation via synthetic media
5. **Business**: Mobile money fraud rings and prevention
6. **Culture**: Streaming platforms reshaping local music scenes
7. **Grok Deepfakes (Adversarial)**: Tests drift prevention with unrelated KB/facts + unsafe hook sanitization

## Exit Codes

- `0`: All checks passed
- `1`: One or more checks failed

## What It Checks

### A. TopicSignature Quality
- Ensures topic signatures have >= 6 non-generic terms
- Rejects stopwords and generic AI terms

### B. KB Drift Gating
- Verifies KB sources are filtered by relevance
- Checks unrelated KB items don't leak into prompts

### C. Facts Drift Gating
- Confirms irrelevant facts are dropped
- Enforces optional context cap (max 1)
- Validates facts in prompt are relevant

### D. Must-Use Provided Sources
- Checks anchored outlines use required number of provided sources
- Verifies prompt includes "MUST USE" instruction
- Confirms provided source URLs appear in prompt

### E. Semantic Bullet Validation
- Rejects placeholder bullets ("key point 1", "TBD", etc.)
- Requires >= 75% of bullets contain topic keywords/entities
- Ensures bullets reference concrete mechanisms/actors/harms

### F. Hook Safety
- Detects unsafe terms (undress/strip/nude) + gender terms
- Validates sanitized hooks don't contain unsafe content
- Confirms safe alternative phrases are used

## No External Calls

This script stubs out all external API calls:
- OpenAI API (chat completions, image generation)
- Network retrieval

All checks run deterministically using in-memory test data.

## Integration

This script imports and uses the same pipeline components as the live app:
- `newsletter_engine.py`: PromptConstructor, NewsletterPlan, etc.
- `topic_signature.py`: build_topic_signature
- `relevance_filter.py`: filter_editorial_sources_by_topic
- `image_service.py`: _sanitize_visual_prompt

Changes to these modules are automatically tested.
