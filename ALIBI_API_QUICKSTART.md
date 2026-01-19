# Alibi API Quick Start

## Start the Server

```bash
python -m alibi.alibi_api
```

Server runs on `http://localhost:8000`

API docs: `http://localhost:8000/docs`

## Send a Camera Event

```bash
curl -X POST http://localhost:8000/webhook/camera-event \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_001",
    "camera_id": "cam_entrance",
    "ts": "2026-01-18T15:00:00",
    "zone_id": "zone_main",
    "event_type": "person_detected",
    "confidence": 0.87,
    "severity": 3,
    "clip_url": "https://storage.example.com/clips/evt_001.mp4"
  }'
```

## List Incidents

```bash
curl http://localhost:8000/incidents
```

## Get Incident Details

```bash
curl http://localhost:8000/incidents/inc_20260118_150000_ae9b33c9
```

Returns:
- Events (with clip URLs)
- Plan (severity, confidence, recommended action)
- Alert (title, body, operator actions)
- Validation (warnings, violations)

## Record Operator Decision

```bash
curl -X POST http://localhost:8000/incidents/inc_001/decision \
  -H "Content-Type: application/json" \
  -d '{
    "action_taken": "confirmed",
    "operator_notes": "Verified legitimate access",
    "was_true_positive": true
  }'
```

Valid actions: `confirmed`, `dismissed`, `escalated`, `closed`

## Run Tests

```bash
# All tests
pytest tests/ -v

# Grouping tests (17 tests)
pytest tests/test_grouping_and_dedupe.py -v

# Validation tests (23 tests)
pytest tests/test_alibi_engine_validation.py -v

# End-to-end API test
./test_api_curl.sh
```

## Configuration

Edit `alibi/data/alibi_settings.json`:

```json
{
  "incident_grouping": {
    "merge_window_seconds": 300,
    "dedup_window_seconds": 30
  },
  "thresholds": {
    "min_confidence_for_notify": 0.75,
    "high_severity_threshold": 4
  },
  "api": {
    "port": 8000,
    "host": "0.0.0.0"
  }
}
```

## Data Files

All stored in `alibi/data/`:
- `events.jsonl` - All camera events
- `incidents.jsonl` - All incidents (versioned)
- `decisions.jsonl` - All operator decisions
- `audit.jsonl` - Audit trail

## Grouping Rules

**Dedup** (30 seconds):
- Same camera + zone + event_type → attach to existing incident

**Merge** (5 minutes):
- Same camera + zone + compatible event_type → merge into incident

**Compatible Types** (configurable):
- `loitering` ↔ `suspicious_behavior`
- `breach` ↔ `unauthorized_access` ↔ `forced_entry`
- `person_detected` ↔ `person_loitering`

## Safety Rules

Every incident automatically:
1. Builds IncidentPlan (severity, confidence, recommended action)
2. Validates against hard safety rules
3. Compiles AlertMessage (neutral language)
4. Stores with full metadata

**Hard Rules:**
- Low confidence → recommend "monitor" only
- High severity or watchlist → requires human approval
- No accusatory language allowed
- Actions must reference evidence

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| POST | `/webhook/camera-event` | Receive event |
| GET | `/incidents` | List incidents |
| GET | `/incidents/{id}` | Get incident details |
| POST | `/incidents/{id}/decision` | Record decision |
| GET | `/decisions` | List decisions |

---

**For full documentation, see `ALIBI_API_COMPLETE.md`**
