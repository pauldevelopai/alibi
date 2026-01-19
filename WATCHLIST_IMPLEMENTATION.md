# Alibi Watchlist System - Implementation Complete

## Overview

The Alibi Watchlist system enables face detection and matching against a City Police wanted list with **strict human verification requirements**. This implementation follows the principle: **NEVER claim identity, ALWAYS require verification**.

## ✅ Implementation Status

### Core Components

1. **✅ Watchlist Storage** (`alibi/watchlist/watchlist_store.py`)
   - JSONL-based append-only storage
   - Stores person_id, label, embeddings, timestamps, source references
   - Audit trail for all enrollments

2. **✅ Face Detection** (`alibi/watchlist/face_detect.py`)
   - OpenCV DNN-based face detection (lightweight)
   - Falls back to Haar Cascades if DNN unavailable
   - Face extraction with configurable padding

3. **✅ Face Embedding** (`alibi/watchlist/face_embed.py`)
   - Supports `face_recognition` library (dlib-based, 128-d embeddings)
   - Falls back to HOG features if `face_recognition` not installed
   - Normalized embeddings for consistent matching

4. **✅ Face Matching** (`alibi/watchlist/face_match.py`)
   - Cosine similarity-based matching
   - Configurable threshold and top-k candidates
   - Returns match confidence scores

5. **✅ Watchlist Detector** (`alibi/video/detectors/watchlist_detector.py`)
   - Integrated into video worker pipeline
   - Periodic face checking (configurable interval)
   - Automatic watchlist reloading
   - Evidence capture (face crops, snapshots, clips)

6. **✅ Enrollment CLI** (`alibi/watchlist/enroll.py`)
   - Command-line tool for enrolling faces
   - Validates face detection before enrollment
   - Audit logging for all enrollments

### Safety & Validation

7. **✅ Validator Safety Rules** (`alibi/validator.py`)
   - Blocks identity-claiming language
   - Enforces "possible match" language
   - Requires human approval for all watchlist matches
   - Requires verification language in alerts

8. **✅ API Endpoints** (`alibi/alibi_api.py`)
   - `GET /watchlist` - List watchlist entries (supervisor+ only)
   - Audit logging for watchlist access
   - Evidence serving via `/evidence/face_crops/`

### Frontend Integration

9. **✅ Console UI** (`alibi/console/src/pages/IncidentDetailPage.tsx`)
   - Prominent "VERIFY VISUALLY" banner for watchlist matches
   - Displays top candidates with similarity scores
   - Face crop image display
   - Supervisor-only "Confirm Match" button
   - Audit trail for confirmations

### Testing

10. **✅ Comprehensive Tests** (`tests/test_watchlist.py`)
    - Storage tests (CRUD operations)
    - Face detection tests
    - Embedding generation tests
    - Matching tests (exact, threshold, top-k)
    - Detector initialization tests
    - Validation safety rule tests
    - **All 15 tests passing**

## 📋 Configuration

### Settings (`alibi/data/alibi_settings.json`)

```json
{
  "watchlist": {
    "enabled": true,
    "match_threshold": 0.6,
    "face_confidence": 0.5,
    "check_interval_seconds": 5.0,
    "reload_interval_seconds": 300,
    "top_k_candidates": 3
  }
}
```

### Parameters

- **`match_threshold`**: Minimum cosine similarity for match (0.0-1.0)
  - Default: 0.6 (conservative)
  - Higher = fewer false positives, more false negatives
  
- **`face_confidence`**: Minimum face detection confidence
  - Default: 0.5
  
- **`check_interval_seconds`**: How often to check faces in video
  - Default: 5.0 seconds (not every frame, for performance)
  
- **`reload_interval_seconds`**: How often to reload watchlist from disk
  - Default: 300 seconds (5 minutes)
  
- **`top_k_candidates`**: Number of top matches to return
  - Default: 3

## 🚀 Usage

### 1. Enroll a Face

```bash
# Using the enrollment CLI
python -m alibi.watchlist.enroll \
  --person_id SUSPECT_001 \
  --label "John Doe (Alias: JD)" \
  --image /path/to/photo.jpg \
  --source "Warrant #2024-1234"

# Or use the sample enrollment script
python scripts/enroll_sample_face.py
```

### 2. Start the Video Worker

The watchlist detector is automatically loaded when the worker starts:

```bash
python -m alibi.video.worker
```

### 3. Monitor Incidents

When a face match is detected:

1. **Incident Created**: `event_type="watchlist_match"`
2. **Evidence Attached**:
   - Face crop image
   - Full frame snapshot
   - Video clip
3. **Metadata Included**:
   - Top 3 candidates with similarity scores
   - Match confidence
   - Detection method used

### 4. Operator Workflow

1. **Incident appears in console** with yellow "VERIFY VISUALLY" banner
2. **Operator reviews**:
   - Face crop from detection
   - Top candidates from watchlist
   - Similarity scores
   - Full snapshot and video clip
3. **Supervisor confirms or dismisses**:
   - "Confirm Match" button (supervisor only)
   - Recorded in audit log
   - Never claims identity automatically

## 🔒 Safety Rules

### Hard-Coded Validator Rules

1. **Language Requirements**:
   - ❌ FORBIDDEN: "identified as", "confirmed as", "is John Doe"
   - ✅ REQUIRED: "possible match", "requires verification"

2. **Approval Requirements**:
   - ALL watchlist matches MUST set `requires_human_approval=True`
   - Recommended action MUST be `dispatch_pending_review` (not automatic dispatch)

3. **Evidence Requirements**:
   - Face crop MUST be attached
   - Snapshot and clip MUST be available
   - Top candidates MUST be listed

### Frontend Safeguards

- Prominent warning banner
- Supervisor-only confirmation
- Visual comparison required
- Audit trail for all actions

## 📊 API Reference

### Enroll Face (CLI)

```bash
python -m alibi.watchlist.enroll \
  --person_id <ID> \
  --label <NAME> \
  --image <PATH> \
  [--source <REFERENCE>] \
  [--watchlist <PATH>]
```

### Get Watchlist (API)

```http
GET /watchlist
Authorization: Bearer <token>
```

**Permissions**: Supervisor or Admin

**Response**:
```json
{
  "entries": [
    {
      "person_id": "SUSPECT_001",
      "label": "John Doe",
      "added_ts": "2026-01-18T12:00:00",
      "source_ref": "Warrant #2024-1234",
      "metadata": {}
    }
  ],
  "total": 1
}
```

Note: Embeddings are NOT returned for security.

### Watchlist Match Event

```json
{
  "event_id": "evt_abc123",
  "event_type": "watchlist_match",
  "confidence": 0.85,
  "severity": 4,
  "snapshot_url": "/evidence/snapshots/snapshot_cam1_20260118_120000.jpg",
  "clip_url": "/evidence/clips/clip_cam1_20260118_120000.mp4",
  "metadata": {
    "match_score": 0.85,
    "top_candidates": [
      {
        "person_id": "SUSPECT_001",
        "label": "John Doe",
        "score": 0.85
      },
      {
        "person_id": "SUSPECT_042",
        "label": "Jane Smith",
        "score": 0.72
      }
    ],
    "face_crop_url": "/evidence/face_crops/face_20260118_120000_123456.jpg",
    "detection_method": "face_recognition",
    "requires_verification": true,
    "warning": "POSSIBLE MATCH - HUMAN VERIFICATION REQUIRED"
  }
}
```

## 🧪 Testing

### Run Tests

```bash
# All watchlist tests
pytest tests/test_watchlist.py -v

# Specific test class
pytest tests/test_watchlist.py::TestWatchlistStore -v

# Specific test
pytest tests/test_watchlist.py::TestWatchlistValidation::test_watchlist_alert_language -v
```

### Test Coverage

- ✅ Storage (create, load, query)
- ✅ Face detection
- ✅ Embedding generation
- ✅ Matching (exact, threshold, top-k)
- ✅ Detector initialization
- ✅ Validation rules
- ✅ Language enforcement

## 📁 File Structure

```
alibi/
├── watchlist/
│   ├── __init__.py
│   ├── watchlist_store.py      # JSONL storage
│   ├── face_detect.py           # OpenCV face detection
│   ├── face_embed.py            # Face embeddings
│   ├── face_match.py            # Cosine similarity matching
│   └── enroll.py                # CLI enrollment tool
├── video/
│   └── detectors/
│       └── watchlist_detector.py  # Video pipeline integration
├── data/
│   ├── watchlist.jsonl          # Watchlist storage
│   ├── evidence/
│   │   └── face_crops/          # Detected face images
│   └── sample_faces/            # Test images
└── validator.py                 # Safety rules

tests/
└── test_watchlist.py            # Comprehensive tests

scripts/
└── enroll_sample_face.py        # Sample enrollment

alibi/console/src/pages/
└── IncidentDetailPage.tsx       # UI with verification banner
```

## 🔧 Dependencies

### Required
- `opencv-python>=4.8.0` (already in requirements.txt)
- `numpy>=1.24.0` (already in requirements.txt)

### Optional (Recommended)
- `face-recognition` - For accurate face embeddings
  ```bash
  pip install face-recognition
  ```
  
  Without this, system falls back to HOG features (less accurate but functional).

## 🚨 Important Notes

### For Namibia Police Deployment

1. **Legal Compliance**:
   - Watchlist enrollment MUST have legal basis (warrant, case number)
   - All enrollments are logged with timestamps and source references
   - Audit trail is append-only

2. **Operator Training**:
   - Operators MUST understand: system provides suggestions, NOT identifications
   - Visual verification is MANDATORY
   - Supervisors MUST review before any action

3. **Data Protection**:
   - Watchlist file (`watchlist.jsonl`) contains sensitive data
   - Embeddings are NOT exposed via API
   - Access is role-restricted (supervisor+ only)

4. **Performance**:
   - Face checking is rate-limited (default: every 5 seconds)
   - Watchlist reloads periodically (default: every 5 minutes)
   - Adjust `check_interval_seconds` based on camera load

5. **Accuracy**:
   - Match threshold of 0.6 is conservative
   - Higher threshold = fewer false positives, more false negatives
   - Test and tune for your specific use case

## 📈 Future Enhancements

### Not Implemented (Out of Scope)

- ❌ Vehicle tracking/ANPR (explicitly excluded per user request)
- ❌ Traffic monitoring (explicitly excluded per user request)
- ❌ Heavy ML models (keeping lightweight for now)

### Potential Improvements

- 🔮 Better face recognition models (DeepFace, FaceNet)
- 🔮 Multi-face tracking across cameras
- 🔮 Face quality assessment
- 🔮 Liveness detection (anti-spoofing)
- 🔮 Watchlist management UI (add/remove via console)

## ✅ Acceptance Criteria Met

- [x] Enroll faces via CLI
- [x] Detect faces in video
- [x] Match against watchlist
- [x] Emit "possible match" events
- [x] ALWAYS require human verification
- [x] ALWAYS attach evidence (face crop + snapshot + clip)
- [x] NEVER claim identity
- [x] Validator enforces safety rules
- [x] API endpoint for watchlist access
- [x] Console shows verification banner
- [x] Supervisor-only confirmation
- [x] Full audit trail
- [x] Comprehensive tests

## 🎉 Summary

The Alibi Watchlist system is **production-ready** for the Namibia Police pilot. It provides:

1. **Accurate face matching** with configurable thresholds
2. **Strict safety rules** enforced at multiple levels
3. **Complete audit trail** for accountability
4. **Evidence-based workflow** with face crops, snapshots, and clips
5. **Role-based access control** (supervisor approval required)
6. **Comprehensive testing** (15/15 tests passing)

The system is designed for **oversight and accountability**, not automated decision-making. Human judgment remains central to the process.
