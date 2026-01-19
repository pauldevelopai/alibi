# Alibi Storage Layer and API - COMPLETE ✅

**Date**: January 18, 2026  
**Status**: COMPLETE - Full storage layer and REST API operational

## What Was Implemented

### 1. Storage Layer (`alibi/alibi_store.py`) ✅

Append-only JSONL storage with full CRUD operations:

**Files Created:**
- `alibi/data/events.jsonl` - All camera events
- `alibi/data/incidents.jsonl` - All incidents (versioned, append-only)
- `alibi/data/decisions.jsonl` - All operator decisions
- `alibi/data/audit.jsonl` - Audit trail

**Functions Implemented:**
- ✅ `append_event(event)` - Store camera event
- ✅ `upsert_incident(incident, metadata)` - Store/update incident with plan/alert/validation
- ✅ `append_decision(decision)` - Store operator decision
- ✅ `append_audit(action, data)` - Store audit entry
- ✅ `list_incidents(status, limit)` - List incidents with filters
- ✅ `get_incident(incident_id)` - Get latest incident version
- ✅ `get_incident_with_metadata(incident_id)` - Get incident with plan/alert/validation
- ✅ `list_decisions(incident_id, limit)` - List decisions
- ✅ `get_events_by_ids(event_ids)` - Retrieve events by IDs

**Key Features:**
- Append-only design (audit-friendly)
- Versioned incidents (every update creates new version)
- Metadata preservation (plan/alert/validation persists across updates)
- Efficient lookups (latest version retrieval)

### 2. Settings Management (`alibi/settings.py`) ✅

Centralized configuration from `alibi/data/alibi_settings.json`:

```json
{
  "incident_grouping": {
    "merge_window_seconds": 300,
    "dedup_window_seconds": 30,
    "compatible_event_types": {
      "loitering": ["loitering", "suspicious_behavior"],
      "breach": ["breach", "unauthorized_access", "forced_entry"],
      "person_detected": ["person_detected", "person_loitering"],
      "vehicle_detected": ["vehicle_detected", "vehicle_loitering"]
    }
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

**Functions:**
- ✅ `get_settings()` - Get global settings instance
- ✅ `are_event_types_compatible(type1, type2)` - Check grouping compatibility
- ✅ Property accessors for all settings

### 3. Incident Grouping Logic (`alibi/incident_grouper.py`) ✅

Deterministic rules for grouping events into incidents:

**Deduplication Rule:**
- Same `camera_id` + `zone_id` + `event_type` within 30 seconds
- → Attach to existing incident (don't create new)

**Grouping Rule:**
- Same `camera_id` + `zone_id`
- Compatible `event_type` (configurable groups)
- Within 5-minute merge window
- → Merge into existing incident

**New Incident Rule:**
- If no dedup or grouping match
- → Create new incident

**Functions:**
- ✅ `process_camera_event(event, store, settings)` - Main entry point
- ✅ `IncidentGrouper.process_event(event)` - Core grouping logic
- ✅ `_find_duplicate_incident(event)` - Dedup check
- ✅ `_find_mergeable_incident(event)` - Grouping check
- ✅ `_generate_incident_id(event)` - Deterministic ID generation

### 4. FastAPI REST API (`alibi/alibi_api.py`) ✅

Full RESTful API with 7 endpoints:

#### Endpoints

**1. `GET /` - API Root**
```bash
curl http://localhost:8000/
```
Returns service info and version.

**2. `GET /health` - Health Check**
```bash
curl http://localhost:8000/health
```
Returns health status and timestamp.

**3. `POST /webhook/camera-event` - Receive Camera Event**
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
    "clip_url": "https://storage.example.com/clip.mp4"
  }'
```

**Processing Pipeline:**
1. Validates schema
2. Stores event
3. Groups into incident (or creates new)
4. Builds IncidentPlan
5. Validates plan
6. Compiles AlertMessage
7. Stores incident with metadata
8. Returns incident summary

**4. `GET /incidents` - List Incidents**
```bash
curl "http://localhost:8000/incidents?status=new&limit=10"
```

Returns summary list with:
- incident_id, status, timestamps
- event_count, max_severity, avg_confidence
- recommended_action, requires_approval

**5. `GET /incidents/{incident_id}` - Get Incident Details**
```bash
curl http://localhost:8000/incidents/inc_20260118_150000_ae9b33c9
```

Returns full incident with:
- All events (with clip URLs)
- IncidentPlan (summary, severity, confidence, recommended action)
- AlertMessage (title, body, operator actions)
- ValidationResult (status, violations, warnings)

**6. `POST /incidents/{incident_id}/decision` - Record Decision**
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

Updates incident status and preserves metadata.

**7. `GET /decisions` - List Decisions**
```bash
curl "http://localhost:8000/decisions?incident_id=inc_001"
```

Returns operator decisions with notes and timestamps.

### 5. CLI Runner (`alibi/__main__.py`) ✅

Start API server with:
```bash
python -m alibi.alibi_api
```

Reads settings from `alibi/data/alibi_settings.json` for host/port.

### 6. Comprehensive Tests (`tests/test_grouping_and_dedupe.py`) ✅

**17 passing tests** covering:

**Deduplication Tests (5):**
- ✅ Same camera+zone+type within 30s → same incident
- ✅ Events 31s apart → separate incidents
- ✅ Different camera → no dedup
- ✅ Different zone → no dedup
- ✅ Different type → no dedup

**Grouping Tests (6):**
- ✅ Compatible types merge within window
- ✅ Same type always merges
- ✅ Events 6min apart → separate incidents
- ✅ Different camera → no grouping
- ✅ Different zone → no grouping
- ✅ Breach types group together (configured)

**Incident Creation Tests (4):**
- ✅ First event creates incident
- ✅ Incident ID format correct
- ✅ Timestamps match event
- ✅ Updated timestamp changes on merge

**Integration Tests (2):**
- ✅ Main entry point works
- ✅ Multiple events sequence processes correctly

### 7. End-to-End Validation (`test_api_curl.sh`) ✅

**8 test scenarios, all passing:**

1. ✅ API health check
2. ✅ POST camera event → incident created
3. ✅ GET incidents list → shows summary
4. ✅ GET incident details → has plan+alert+validation
5. ✅ POST second event → merges into same incident
6. ✅ POST operator decision → recorded
7. ✅ GET decisions → shows decision
8. ✅ Verify metadata preserved after decision

## Architecture

```
Camera Event → API Webhook
                  ↓
            Store Event (events.jsonl)
                  ↓
            Grouping Logic
            (dedup/merge/new)
                  ↓
              Incident
                  ↓
        build_incident_plan()
                  ↓
        validate_incident_plan()
                  ↓
          compile_alert()
                  ↓
    Store Incident + Metadata (incidents.jsonl)
                  ↓
            Audit Log (audit.jsonl)
```

## Key Design Decisions

### 1. Append-Only Storage
- Every incident update creates new version
- Never delete or overwrite
- Enables full audit trail
- Latest version retrieved by reading forward

### 2. Metadata Preservation
- Plan/alert/validation stored as `_metadata` in incident
- Preserved across status updates
- Enables full incident history

### 3. Deterministic Grouping
- Rules-based (no ML)
- Configurable windows and compatibility
- Predictable behavior
- Testable

### 4. Fail-Safe Pipeline
- Each step independent
- Validation failures don't block storage
- LLM failures fall back to deterministic text
- System always operational

## Configuration

### Settings File: `alibi/data/alibi_settings.json`

```json
{
  "incident_grouping": {
    "merge_window_seconds": 300,      // 5 minutes
    "dedup_window_seconds": 30,       // 30 seconds
    "compatible_event_types": {
      "loitering": ["loitering", "suspicious_behavior"],
      "breach": ["breach", "unauthorized_access", "forced_entry"]
    }
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

### Environment Variables

```bash
OPENAI_API_KEY=sk-...  # Optional for LLM text generation
```

## Running the System

### Start API Server

```bash
# Method 1: Using module
python -m alibi.alibi_api

# Method 2: Direct
cd alibi && python alibi_api.py
```

Server starts on `http://localhost:8000`

API docs available at: `http://localhost:8000/docs`

### Run Tests

```bash
# Grouping and dedup tests
pytest tests/test_grouping_and_dedupe.py -v

# Validation tests
pytest tests/test_alibi_engine_validation.py -v

# All tests
pytest tests/ -v
```

### End-to-End Test

```bash
# Start server first
python -m alibi.alibi_api &

# Run curl tests
./test_api_curl.sh
```

## Example Usage

### 1. Send Camera Event

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
    "clip_url": "https://storage.example.com/clips/evt_001.mp4",
    "snapshot_url": "https://storage.example.com/snapshots/evt_001.jpg"
  }'
```

Response:
```json
{
  "incident_id": "inc_20260118_150000_ae9b33c9",
  "status": "new",
  "event_count": 1,
  "validation_passed": true,
  "recommended_action": "notify"
}
```

### 2. Get Incident Details

```bash
curl http://localhost:8000/incidents/inc_20260118_150000_ae9b33c9
```

Response includes:
- Events with clip URLs
- Plan with severity/confidence/recommended action
- Alert with title/body/operator actions
- Validation with warnings/violations

### 3. Record Operator Decision

```bash
curl -X POST http://localhost:8000/incidents/inc_20260118_150000_ae9b33c9/decision \
  -H "Content-Type: application/json" \
  -d '{
    "action_taken": "confirmed",
    "operator_notes": "Verified legitimate access",
    "was_true_positive": true
  }'
```

## File Structure

```
alibi/
├── alibi_store.py           # Storage layer (JSONL)
├── alibi_api.py             # FastAPI REST API
├── incident_grouper.py      # Grouping/dedup logic
├── settings.py              # Settings manager
├── __main__.py              # CLI entry point
├── data/
│   ├── alibi_settings.json  # Configuration
│   ├── events.jsonl         # All events
│   ├── incidents.jsonl      # All incidents (versioned)
│   ├── decisions.jsonl      # All decisions
│   └── audit.jsonl          # Audit trail

tests/
├── test_grouping_and_dedupe.py      # 17 tests
└── test_alibi_engine_validation.py  # 23 tests

test_api_curl.sh             # End-to-end curl tests
```

## Test Results

### Unit Tests
- **Grouping/Dedup**: 17/17 passing ✅
- **Validation**: 23/23 passing ✅
- **Total**: 40/40 passing ✅

### Integration Tests
- **End-to-End API**: 8/8 scenarios passing ✅

## Acceptance Criteria - ALL MET ✅

1. ✅ **Append-only JSONL storage** - events.jsonl, incidents.jsonl, decisions.jsonl, audit.jsonl
2. ✅ **Storage helpers** - append_event, upsert_incident, append_decision, list_incidents, get_incident
3. ✅ **FastAPI endpoints** - 7 endpoints implemented
4. ✅ **POST /webhook/camera-event** - Validates, stores, groups, builds plan, validates, compiles alert
5. ✅ **GET /incidents** - Lists with summary
6. ✅ **GET /incidents/{id}** - Returns full incident with plan+alert+validation
7. ✅ **POST /incidents/{id}/decision** - Records decision with status update
8. ✅ **Incident grouping** - Same camera+zone, compatible type, 5min window
9. ✅ **Deduplication** - Same camera+zone+type, 30sec window
10. ✅ **Every incident create/update** - Rebuilds plan, validates, compiles alert, stores metadata
11. ✅ **Settings file** - alibi_settings.json with thresholds and windows
12. ✅ **CLI runner** - `python -m alibi.alibi_api` starts on port 8000
13. ✅ **Tests** - test_grouping_and_dedupe.py with 17 tests
14. ✅ **curl POST event → GET /incidents shows plan+alert** - Verified ✅

## Summary

✅ **Complete Storage Layer**: Append-only JSONL with versioning and metadata preservation

✅ **Complete REST API**: 7 endpoints with full incident lifecycle management

✅ **Deterministic Grouping**: Rules-based dedup and merge with configurable windows

✅ **Full Pipeline Integration**: Event → Group → Plan → Validate → Alert → Store

✅ **Comprehensive Testing**: 40 unit tests + 8 integration tests, all passing

✅ **Production Ready**: Fail-safe design, audit trail, metadata preservation

---

**The Alibi system spine is complete and operational. All acceptance criteria met.**
