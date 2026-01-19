# Alibi Quick Start Guide

## What is Alibi?

Alibi is an AI-assisted incident alert management system for security camera networks. It analyzes camera events, validates recommendations against hard safety rules, and generates alerts for human operators.

## 🚀 Get Started in 3 Minutes

### 1. Verify Installation

```bash
PYTHONPATH=. python verify_alibi.py
```

You should see: ✅ ALL VERIFICATION TESTS PASSED

### 2. Run the Demo

```bash
PYTHONPATH=. python alibi/demo.py
```

This shows 6 scenarios demonstrating the safety rules in action.

### 3. Run the Tests

```bash
pytest tests/test_alibi_engine_validation.py -v
```

All 23 tests should pass.

## 📝 Simple Example

```python
from datetime import datetime
from alibi import (
    CameraEvent,
    Incident,
    IncidentStatus,
    build_incident_plan,
    validate_incident_plan,
    compile_alert,
)

# Create event
event = CameraEvent(
    event_id="evt_001",
    camera_id="cam_entrance",
    ts=datetime.utcnow(),
    zone_id="zone_main",
    event_type="person_detected",
    confidence=0.85,
    severity=3,
    clip_url="https://storage.example.com/clip.mp4",
)

# Create incident
incident = Incident(
    incident_id="inc_001",
    status=IncidentStatus.NEW,
    created_ts=datetime.utcnow(),
    updated_ts=datetime.utcnow(),
    events=[event],
)

# Process incident
plan = build_incident_plan(incident)
validation = validate_incident_plan(plan, incident)

if validation.passed:
    alert = compile_alert(plan, incident)
    print(f"Alert: {alert.title}")
    print(f"Action: {plan.recommended_next_step.value}")
```

## 🔒 Key Safety Rules

### Rule 1: No Accusations
- ❌ "suspect", "criminal", "perpetrator"
- ✅ "possible", "appears", "may indicate"

### Rule 2: Low Confidence → Monitor
- If confidence < 0.75 → only "monitor" allowed
- No notifications or dispatch

### Rule 3: High Risk → Human Approval
- If severity ≥ 4 OR watchlist match
- Human approval REQUIRED
- Action must be "dispatch_pending_review"

### Rule 4: Evidence Required
- "notify" or "dispatch" actions
- Must reference evidence OR state "no clip available"

## 📁 File Structure

```
alibi/
├── __init__.py           # Package exports
├── schemas.py            # Data models
├── alibi_engine.py       # Core processing
├── validator.py          # Safety rules
├── llm_service.py        # Optional LLM
├── config.py             # Configuration
├── demo.py               # Full demo
├── example.py            # Simple example
└── data/
    └── incident_processing.jsonl  # Audit log

tests/
└── test_alibi_engine_validation.py  # 23 tests
```

## 🔧 Configuration

```bash
# Set thresholds (optional)
export ALIBI_MIN_CONFIDENCE_NOTIFY="0.75"
export ALIBI_HIGH_SEVERITY_THRESHOLD="4"

# Enable LLM text generation (optional)
export OPENAI_API_KEY="sk-..."
```

## 📊 Data Flow

```
1. CameraEvent(s) → Incident
2. Incident → build_incident_plan() → IncidentPlan
3. IncidentPlan → validate_incident_plan() → ValidationResult
4. If valid → compile_alert() → AlertMessage
5. All steps logged to incident_processing.jsonl
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/test_alibi_engine_validation.py -v

# Run specific test
pytest tests/test_alibi_engine_validation.py::TestValidationRules -v

# Run verification
PYTHONPATH=. python verify_alibi.py
```

## 📚 Documentation

- **README.md** - Overview and quick start
- **alibi/README.md** - Full API reference
- **ALIBI_CONVERSION_COMPLETE.md** - Detailed conversion notes
- **verify_alibi.py** - System verification script

## 🎯 Common Use Cases

### Low Confidence Detection
```python
event = CameraEvent(..., confidence=0.60, severity=3)
plan = build_incident_plan(incident)
# Result: recommended_next_step = "monitor"
```

### High Severity Incident
```python
event = CameraEvent(..., confidence=0.90, severity=5)
plan = build_incident_plan(incident)
# Result: requires_human_approval = True
#         recommended_next_step = "dispatch_pending_review"
```

### Watchlist Match
```python
event = CameraEvent(..., metadata={"watchlist_match": True})
plan = build_incident_plan(incident)
# Result: requires_human_approval = True
#         recommended_next_step = "dispatch_pending_review"
```

## ⚠️ Important Notes

1. **LLM is Optional**: System works without OpenAI API key
2. **Fail-Safe Design**: Degrades gracefully on errors
3. **Audit Trail**: All decisions logged to JSONL
4. **No Exceptions**: Safety rules enforced strictly

## 🆘 Troubleshooting

### Import Error
```bash
# Use PYTHONPATH
PYTHONPATH=. python your_script.py
```

### Tests Fail
```bash
# Check Python version (requires 3.8+)
python --version

# Reinstall dependencies
pip install -r requirements.txt
```

### No JSONL Log
```bash
# Create data directory
mkdir -p alibi/data
```

## 📞 Support

- Read full docs: `alibi/README.md`
- Run demo: `PYTHONPATH=. python alibi/demo.py`
- Check tests: `pytest tests/ -v`

---

**Ready to use Alibi for responsible AI-assisted security operations!**
