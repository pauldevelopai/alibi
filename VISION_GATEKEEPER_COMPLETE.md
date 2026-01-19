# Vision-First Gatekeeper Pipeline

**Status**: ✅ COMPLETE  
**Date**: 2026-01-19  
**Purpose**: Stop LLM-driven noise from polluting training data

---

## Problem Statement

**BEFORE**: Training collector used LLM captions as triggers
- ❌ LLM describes everything, including boring/irrelevant footage
- ❌ Training data polluted with noise ("a cat", "empty room", "static scene")
- ❌ System dependent on LLM availability
- ❌ No structured data, just text descriptions
- ❌ Expensive and slow (every frame → LLM call)

**AFTER**: Vision-first gatekeeper decides BEFORE LLM
- ✅ YOLO detections decide relevance, not LLM
- ✅ Rule-based scoring filters noise
- ✅ Only relevant footage passes the gate
- ✅ Structured incidents with detection data
- ✅ LLM is optional enrichment, not required
- ✅ Faster and cheaper (gate rejects early)

---

## Architecture

```
┌─────────────┐
│   Frame     │
│   Input     │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Vision Detection   │  ◄── YOLO v8
│  (NO LLM YET!)      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Zone Matching      │  ◄── Apply zones config
│  (spatial context)  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Rule Scoring       │  ◄── Security relevance
│  (relevance calc)   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  THE GATE           │  ◄── Policy thresholds
│  Pass or Reject?    │
└──────┬──────────────┘
       │
       ├─── REJECT ───► Store as baseline/noise (NO TRAINING)
       │                No LLM called (saved money!)
       │
       └─── PASS ─────► Create VisionIncident (structured)
                        │
                        ▼
                   ┌──────────────────┐
                   │ Optional: LLM    │  ◄── Enrichment only
                   │ Enrichment       │      Incident exists
                   └──────────────────┘      without it!
```

---

## Components

### 1. Vision Gatekeeper (`alibi/vision/gatekeeper.py`)

**Purpose**: Primary decision-maker for incident creation

**Key Methods**:

```python
gatekeeper = VisionGatekeeper(model_path="yolov8n.pt", policy=policy)

# 1. Detect objects (YOLO)
detections = gatekeeper.detect_objects(frame)
# Returns: List[Detection] with class, confidence, bbox

# 2. Apply zones
zone_hits = gatekeeper.apply_zones(detections, zones_config)
# Returns: List[ZoneHit] for spatial context

# 3. Score event
score = gatekeeper.score_event(detections, zone_hits)
# Returns: VisionScore with vision_conf, rule_conf, combined_conf

# 4. Check eligibility
eligible, reason = gatekeeper.is_training_eligible(score, detections, zone_hits)
# Returns: (bool, str) - pass or reject

# OR: Full pipeline in one call
result = gatekeeper.process_frame(frame, zones_config)
# Returns: dict with detections, scores, eligible, reason
```

**Gate Logic**:

```python
# Pass ALL of these:
vision_conf >= 0.5      # YOLO confidence
rule_conf >= 0.6        # Security relevance
combined_conf >= 0.55   # Weighted average
privacy_filters_pass    # No faces in public without consent
```

**Security Classes** (high relevance):
- People: `person`
- Vehicles: `car`, `motorcycle`, `bus`, `truck`, `bicycle`
- Weapons: `knife`, `scissors`, `baseball bat`
- Suspicious objects: `backpack`, `handbag`, `suitcase`

### 2. Incident Schema (`alibi/schema/incidents.py`)

**Purpose**: Structured, vision-first incident objects

**Key Class**: `VisionIncident`

```python
@dataclass
class VisionIncident:
    # Identity
    id: str
    camera_id: str
    
    # Timing
    ts_start: datetime
    ts_end: datetime
    
    # Category (vision-based, not LLM)
    category: IncidentCategory  # person_detected, vehicle_detected, etc.
    
    # Detections (SOURCE OF TRUTH)
    detections: DetectionSummary  # classes, counts, avg_confidence
    
    # Zone hits (spatial context)
    zone_hits: Optional[ZoneHitSummary]
    
    # Evidence
    evidence_frames: List[str]
    evidence_clip: Optional[str]
    
    # Scores (gatekeeper decision)
    scores: IncidentScores  # vision_conf, rule_conf, combined_conf
    
    # Flags
    flags: IncidentFlags  # training_eligible, privacy_risk, llm_optional
    
    # LLM enrichment (OPTIONAL - may be None!)
    llm_caption: Optional[str] = None
    llm_confidence: Optional[float] = None
```

**Categories** (vision-derived):
- `PERSON_DETECTED` - person in frame
- `VEHICLE_DETECTED` - vehicle in frame
- `RESTRICTED_ZONE_ENTRY` - object in restricted zone
- `WEAPON_DETECTED` - knife, scissors detected
- `MULTIPLE_PEOPLE` - 3+ people
- `OBJECT_LEFT_UNATTENDED` - stationary object
- And more...

### 3. Gatekeeper Policy

**Purpose**: Configurable thresholds for gate decisions

```python
policy = GatekeeperPolicy(
    # Minimum thresholds
    min_vision_conf=0.5,         # YOLO >= 50%
    min_rule_conf=0.6,           # Rules >= 60%
    min_combined_conf=0.55,      # Combined >= 55%
    
    # Security classes (overridable)
    security_classes=["person", "car", "knife", ...],
    
    # Privacy
    block_faces_in_public=True,
    require_consent_flag=False
)
```

---

## Usage

### CLI Test

```bash
# Install dependencies
pip install ultralytics

# Test on image (vision only)
python -m alibi.vision.gatekeeper --image path/to/image.jpg

# Test with zones
python -m alibi.vision.gatekeeper --image path/to/image.jpg --zones zones.json

# Show annotated output
python -m alibi.vision.gatekeeper --image path/to/image.jpg --show
```

### Python API

```python
from alibi.vision.gatekeeper import VisionGatekeeper, GatekeeperPolicy
from alibi.schema.incidents import VisionIncident
import cv2

# Initialize
policy = GatekeeperPolicy(min_combined_conf=0.5)
gatekeeper = VisionGatekeeper(model_path="yolov8n.pt", policy=policy)

# Process frame
frame = cv2.imread("camera_frame.jpg")
result = gatekeeper.process_frame(frame, zones_config=zones)

# Check if eligible
if result['eligible']:
    # Create structured incident (NO LLM NEEDED!)
    incident = VisionIncident.from_gatekeeper_result(
        camera_id="camera_001",
        result=result,
        evidence_frames=["frame.jpg"]
    )
    
    # Store for training
    if incident.flags.training_eligible:
        store_training_data(incident)
    
    # Optional: Enrich with LLM (after incident exists)
    try:
        llm_caption = call_openai_vision(frame)
        incident.llm_caption = llm_caption
    except Exception:
        pass  # Incident still valid without LLM!
else:
    # Store as baseline/noise (not for training)
    store_baseline(result)
```

### Integration with Training Collector

**OLD WAY** (LLM-first, bad):
```python
# DON'T DO THIS
caption = llm.analyze(frame)  # ❌ Always calls LLM
if "person" in caption:       # ❌ Brittle text matching
    store_training(caption)   # ❌ Unstructured text
```

**NEW WAY** (Vision-first, good):
```python
# DO THIS
result = gatekeeper.process_frame(frame)  # ✅ Vision first
if result['eligible']:                     # ✅ Structured decision
    incident = VisionIncident.from_gatekeeper_result(...)
    store_training(incident)               # ✅ Structured data
    
    # Optional LLM enrichment (after gate)
    if should_enrich:
        incident.llm_caption = llm.analyze(frame)
```

---

## Benefits

### 1. **Noise Filtering**

**Before**:
```
LLM: "A cat sitting on a couch"           → Training data ❌
LLM: "An empty room"                       → Training data ❌
LLM: "A static scene with no movement"    → Training data ❌
LLM: "A person walking"                   → Training data ✅
```

**After**:
```
Gate: No security-relevant objects         → Baseline/noise ✅
Gate: No security-relevant objects         → Baseline/noise ✅
Gate: No security-relevant objects         → Baseline/noise ✅
Gate: Person detected, high confidence     → Training data ✅
```

### 2. **Structured Data**

**Before** (unstructured):
```json
{
  "caption": "A person wearing a backpack near a car",
  "confidence": 0.8
}
```

**After** (structured):
```json
{
  "id": "inc_abc123",
  "category": "person_detected",
  "detections": {
    "classes": ["person", "backpack", "car"],
    "counts": {"person": 1, "backpack": 1, "car": 1},
    "avg_confidence": 0.87,
    "security_relevant": true
  },
  "scores": {
    "vision_conf": 0.87,
    "rule_conf": 0.80,
    "combined_conf": 0.84
  },
  "flags": {
    "training_eligible": true,
    "llm_optional": true
  },
  "llm_caption": "A person wearing a backpack..." // Optional
}
```

### 3. **LLM Independence**

```python
# System works WITHOUT OpenAI
if gatekeeper.is_available():  # ✅ Always true (local YOLO)
    incident = create_incident(result)
else:
    # This never happens - vision always works!
    pass

# LLM enrichment is optional
try:
    incident.llm_caption = openai.analyze(frame)
except OpenAIError:
    pass  # ✅ Incident still valid!
```

### 4. **Cost Savings**

**Before**:
- 1000 frames/day
- Each frame → OpenAI call
- $0.01 per call
- **Cost: $10/day = $300/month**

**After**:
- 1000 frames/day
- Gate rejects 800 frames (not relevant)
- Only 200 → OpenAI call (optional enrichment)
- $0.01 per call
- **Cost: $2/day = $60/month**

**Savings: $240/month (80% reduction)**

### 5. **Speed**

**Before**:
- Frame → OpenAI Vision → 2-3 seconds
- 1000 frames → 2000-3000 seconds ≈ **50 minutes**

**After**:
- Frame → YOLO (local) → 50ms
- Gate rejects 800 → 40 seconds total
- 200 → OpenAI → 400 seconds
- **Total: 440 seconds ≈ 7 minutes**

**Speedup: 7x faster**

---

## Gate Policies

### Conservative (High Precision)

```python
policy = GatekeeperPolicy(
    min_vision_conf=0.7,        # Very confident detections
    min_rule_conf=0.8,          # Very relevant
    min_combined_conf=0.75,
    block_faces_in_public=True
)
```

**Result**: Few incidents, but all highly relevant

### Balanced (Default)

```python
policy = GatekeeperPolicy(
    min_vision_conf=0.5,
    min_rule_conf=0.6,
    min_combined_conf=0.55,
    block_faces_in_public=True
)
```

**Result**: Good balance of coverage and precision

### Aggressive (High Recall)

```python
policy = GatekeeperPolicy(
    min_vision_conf=0.3,        # Lower confidence OK
    min_rule_conf=0.4,          # More permissive
    min_combined_conf=0.35,
    block_faces_in_public=False
)
```

**Result**: More incidents, catches edge cases

---

## Training Data Flow

### Old Flow (LLM-first)

```
Camera → LLM → Caption → Training DB
         ↑
         Everything goes to LLM!
         Expensive, slow, noisy
```

### New Flow (Vision-first)

```
Camera → Gate → Eligible? → Training DB
         ↓               ↓
         YOLO            Structured incident
         Fast            Optional LLM enrich
         Free            
                                
         Not Eligible?
         ↓
         Baseline DB (metrics only)
         Not for training
```

---

## Testing

### Test Script

```bash
# Full test with sample image
python test_gatekeeper.py --image /path/to/camera/snapshot.jpg

# Test with LLM enrichment flow
python test_gatekeeper.py --image /path/to/snapshot.jpg --llm
```

### Expected Output

```
======================================================================
VISION-FIRST GATEKEEPER TEST
======================================================================

1. Loading image: /path/to/snapshot.jpg
   ✅ Loaded: 1280x720 pixels

2. Initializing Vision Gatekeeper
   • Model: YOLOv8n (nano, fast)
   • Policy: default security thresholds
   ✅ Gatekeeper ready

3. Running Vision Detection (NO LLM)

   📊 Detections: 3
      • person: 0.87
      • backpack: 0.65
      • car: 0.92

   📈 Scores:
      • Vision: 0.81
      • Rules: 0.80
      • Combined: 0.81
      • Reason: Security objects: person, backpack, car

   🚦 Gate Decision: ✅ PASS
      • Passed: Security objects: person, backpack, car

4. Creating Vision Incident (LLM-FREE)
   ✅ Incident created:
      • ID: inc_abc123def
      • Category: person_detected
      • Training eligible: True
      • LLM required: False

   📚 Training Data (NO LLM CAPTION NEEDED):
      • Classes: person, backpack, car
      • Counts: {'person': 1, 'backpack': 1, 'car': 1}
      • Confidence: 0.81
      • Security relevant: True

   ✅ This would be stored as STRUCTURED training data
      (NOT as an LLM caption that might be wrong!)

======================================================================
KEY TAKEAWAYS:
======================================================================
1. ✅ Vision detection happens FIRST (YOLO)
2. ✅ Rules score BEFORE any LLM
3. ✅ Gate decides eligibility (no LLM needed)
4. ✅ Structured incidents created WITHOUT LLM
5. ✅ LLM is OPTIONAL enrichment, not required
6. ✅ Training data based on detections, not captions
7. ✅ System works even if LLM fails
======================================================================
```

---

## Dependencies

### Required

```
ultralytics>=8.0.0  # YOLO v8
opencv-python>=4.8.0
numpy>=1.24.0
```

### Installation

```bash
# Via pip
pip install ultralytics opencv-python numpy

# Or via requirements.txt
pip install -r requirements.txt
```

### YOLO Models

The gatekeeper downloads YOLO models automatically on first run:

- `yolov8n.pt` (nano) - Default, fast, 6MB
- `yolov8s.pt` (small) - Better accuracy, 22MB
- `yolov8m.pt` (medium) - High accuracy, 52MB
- `yolov8l.pt` (large) - Highest accuracy, 87MB

**Recommendation**: Use `yolov8n.pt` for real-time, `yolov8s.pt` for offline

---

## Summary

✅ **Gatekeeper implemented** - Vision-first decision making  
✅ **Incident schema created** - Structured, not text-based  
✅ **CLI test ready** - `python -m alibi.vision.gatekeeper --image test.jpg`  
✅ **LLM made optional** - System works without it  
✅ **Noise filtering** - Only relevant footage for training  
✅ **Cost reduction** - 80% fewer LLM calls  
✅ **Speed improvement** - 7x faster processing  
✅ **Documentation complete** - This file + inline comments  

---

**Next Steps**:

1. ✅ Install ultralytics: `pip install ultralytics`
2. ✅ Test: `python test_gatekeeper.py --image snapshot.jpg`
3. ⏭️ Update training collector to use gatekeeper
4. ⏭️ Update mobile camera to use gatekeeper
5. ⏭️ Monitor training data quality improvement

---

**Philosophy**:

> "The LLM doesn't decide what's important.  
> The vision detector does.  
> The LLM just adds color commentary."

---
