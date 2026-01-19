# Training Data Pipeline - Complete End-to-End Flow

**Status**: ✅ COMPLETE  
**Date**: 2026-01-19  
**Missing Step**: ✅ IMPLEMENTED

---

## The Complete Flow (NOW WORKING)

```
┌─────────────────────────────────────────────────────────────────┐
│  1. CAMERA DETECTS SOMETHING                                    │
│     • YOLO object detection                                     │
│     • Multi-object tracking (ByteTrack)                         │
│     • Persistent track IDs across frames                        │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. RULES TRIGGER                                               │
│     • Loitering (dwell time > threshold)                        │
│     • Restricted zone entry                                     │
│     • Object left unattended                                    │
│     • Rapid movement / Aggression                               │
│     • Crowd formation                                           │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. INCIDENT LIFECYCLE                                          │
│     • OPEN: Rule becomes true for track                         │
│     • UPDATE: Rule stays true (duration increases)              │
│     • CLOSE: Rule becomes false OR track lost                   │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. AUTO-CONVERT TO TRAINING INCIDENT ✅ NEW!                   │
│     • IncidentToTrainingConverter                               │
│     • Converts closed incident → TrainingIncident               │
│     • Checks for privacy risks (faces)                          │
│     • Infers category from rules                                │
│     • Stores in TrainingDataStore                               │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. TRAINING DATA REVIEW PAGE                                   │
│     • Shows pending incidents for review                        │
│     • Statistics by status (pending/confirmed/rejected)         │
│     • Review buttons: Confirm / Reject / Needs Review           │
│     • Privacy handling: Redact Faces button                     │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. HUMAN REVIEW                                                │
│     • Operator reviews incident                                 │
│     • Confirms if good training data                            │
│     • Rejects with reason if bad data                           │
│     • Flags for supervisor if unsure                            │
│     • Redacts faces if privacy risk                             │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. EXPORT FOR FINE-TUNING                                      │
│     • Admin triggers export (≥100 confirmed required)           │
│     • OpenAI JSONL format                                       │
│     • COCO annotations format                                   │
│     • Manifest with full provenance                             │
│     • ONLY confirmed + privacy-safe incidents                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## What Was Missing (Now Fixed)

### **Before:**
- ✅ Steps 1-3 existed (detection → tracking → incidents)
- ✅ Steps 5-7 existed (review UI → human review → export)
- ❌ **Step 4 was MISSING** (incident → TrainingIncident)

### **After:**
- ✅ **ALL steps connected**
- ✅ Automatic conversion when incidents close
- ✅ No manual intervention needed
- ✅ Real camera data flows into training pipeline

---

## The Missing Link: IncidentToTrainingConverter

### **Location**: `alibi/training/incident_converter.py`

### **Purpose**: 
Automatically converts closed incidents from the tracking system into TrainingIncidents ready for human review.

### **How It Works**:

```python
# When incident closes
incident = {
    "incident_id": "inc_0042",
    "status": "closed",
    "class_name": "person",
    "triggered_rules": ["loitering_in_entrance"],
    "reason": "person loitering in entrance for 45s",
    "duration_seconds": 45.0,
    "max_confidence": 0.87,
    "zone_presence": {"entrance": 45.0},
    "start_time": datetime(...),
    "end_time": datetime(...)
}

# Converter creates TrainingIncident
converter = IncidentToTrainingConverter()
training_incident = converter.convert_incident(
    incident,
    camera_id="camera_001",
    evidence_frames=["frame_001.jpg", "frame_002.jpg"],
    evidence_clip="clip_042.mp4"
)

# Now appears on Training Data page for human review!
```

### **Features**:

1. **Category Inference**:
   - Analyzes triggered rules
   - Maps to standard categories
   - Examples: `loitering`, `restricted_zone_entry`, `object_left_unattended`

2. **Privacy Checking**:
   - Automatically checks evidence frames for faces
   - Sets `faces_detected` flag
   - Requires redaction before confirmation

3. **Data Structuring**:
   - Converts incident dict → TrainingIncident dataclass
   - Includes full provenance (camera, timestamp, method)
   - Stores all metadata for audit trail

4. **Error Handling**:
   - Failures logged but don't break incident processing
   - Graceful degradation if conversion fails

---

## Integration with IncidentManager

### **Location**: `alibi/vision/simulate.py`

### **Changes**:

```python
# OLD (before)
class IncidentManager:
    def __init__(self, rule_evaluator):
        self.rule_evaluator = rule_evaluator
        # When incidents close, they just sit in a list
        self.closed_incidents = []

# NEW (after)
class IncidentManager:
    def __init__(
        self,
        rule_evaluator,
        auto_convert_to_training=True,  # NEW!
        camera_id="unknown"              # NEW!
    ):
        self.rule_evaluator = rule_evaluator
        self.auto_convert_to_training = auto_convert_to_training
        self.camera_id = camera_id
        self.converter = get_converter() if auto_convert_to_training else None
        
    def update(self, tracks, frame_number, timestamp):
        # ... incident logic ...
        
        # When incident closes
        if self.converter:
            self.converter.convert_incident(
                closed_incident,
                camera_id=self.camera_id
            )
        # Now automatically becomes TrainingIncident!
```

### **What Happens**:

1. **Incident Opens**: Track starts triggering rules
2. **Incident Updates**: Duration increases each frame
3. **Incident Closes**: Rules stop triggering
4. **Auto-Convert**: Converter creates TrainingIncident
5. **Store**: Saved to `alibi/data/training_incidents.jsonl`
6. **Review**: Appears on Training Data page

---

## Usage Examples

### **Example 1: Video Simulation**

```bash
# Run tracking + rules on a video
python -m alibi.vision.simulate --video sample.mp4

# Output:
🟢 OPEN  | Frame 0045 | ID: inc_0001 | person loitering
🔴 CLOSE | Frame 0267 | Duration: 48.0s
✅ Converted to TrainingIncident: inc_0001

# Now check Training Data page:
# http://localhost:8000/camera/training
# → Shows "Pending Review: 1"
```

### **Example 2: Mobile Camera**

```python
# In mobile camera stream
from alibi.vision.tracking import MultiObjectTracker
from alibi.rules.events import RuleEvaluator
from alibi.vision.simulate import IncidentManager

# Initialize with auto-conversion
tracker = MultiObjectTracker()
evaluator = RuleEvaluator(zones_config, rules_config)
incident_manager = IncidentManager(
    evaluator,
    auto_convert_to_training=True,
    camera_id="mobile_001"
)

# Process frames
for frame in camera_stream:
    results = yolo_model.track(frame, persist=True)
    tracks = tracker.update(results, zones_config, timestamp)
    updates = incident_manager.update(tracks, frame_num, timestamp)
    
    # Closed incidents automatically become TrainingIncidents!
    if updates["closed"]:
        print(f"✅ {len(updates['closed'])} incidents → Training Data")
```

### **Example 3: Manual Conversion**

```python
# If you have existing incidents
from alibi.training import get_converter

converter = get_converter()

# Convert one incident
training_incident = converter.convert_incident(
    incident_dict,
    camera_id="camera_001",
    evidence_frames=["frame1.jpg", "frame2.jpg"],
    evidence_clip="clip.mp4"
)

# Or batch convert
count = converter.process_closed_incidents(
    incident_manager.closed_incidents,
    camera_id="camera_001",
    evidence_dir=Path("alibi/data/evidence")
)
print(f"✅ Converted {count} incidents")
```

---

## Data Flow Diagram

```
Real Camera Detection:
┌─────────────┐
│   Frame     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    YOLO     │ ◄── yolov8n.pt (object detection)
│  Detection  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Tracker   │ ◄── ByteTrack (persistent IDs)
│   Update    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Rule     │ ◄── loitering, restricted_zone, etc.
│ Evaluation  │
└──────┬──────┘
       │
       ├─ Rule TRUE → OPEN incident
       ├─ Rule TRUE → UPDATE incident
       └─ Rule FALSE → CLOSE incident
                       ↓
                  ┌─────────────┐
                  │  Converter  │ ◄── NEW! Auto-conversion
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │  Training   │ ◄── Stored in training_incidents.jsonl
                  │  Incident   │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │   Review    │ ◄── http://localhost:8000/camera/training
                  │     UI      │
                  └──────┬──────┘
                         │
                    Human Review
                         │
                    ┌────┴────┐
                    ▼         ▼
                CONFIRM   REJECT
                    │         │
                    ▼         ▼
              Fine-Tune   Discarded
              Eligible
```

---

## What You'll See Now

### **On Training Data Page**:

After running the camera and detecting REAL events:

1. **Statistics Update**:
   ```
   Pending Review: 5  ← Real incidents waiting for review
   Confirmed: 0
   Rejected: 0
   Needs Review: 0
   ```

2. **Incident List**:
   ```
   ┌─────────────────────────────────────────────────┐
   │ inc_0001                    [Pending Review]    │
   ├─────────────────────────────────────────────────┤
   │ Category: loitering                             │
   │ Reason: person loitering in entrance for 45s    │
   │ Camera: camera_001                              │
   │ Duration: 45.0s                                 │
   │ Confidence: 87%                                 │
   │ Rules: loitering_in_entrance                    │
   │                                                 │
   │ [✅ Confirm] [❌ Reject] [⚠️ Needs Review]      │
   └─────────────────────────────────────────────────┘
   ```

3. **After Review**:
   ```
   Confirmed: 1  ← Moved to confirmed after clicking "Confirm"
   Fine-Tune Ready: 1/100
   ```

---

## Testing the Flow

### **Step 1: Run Video Simulation**

```bash
cd alibi
python -m alibi.vision.simulate \
    --video sample.mp4 \
    --zones alibi/data/config/zones.json \
    --rules alibi/data/config/rules.yaml
```

**Expected Output**:
```
🟢 OPEN  | Frame 0045 | ID: inc_0001 | person
         Reason: person in restricted zone
✅ Converted to TrainingIncident: inc_0001

🔴 CLOSE | Frame 0189 | Duration: 4.8s
```

### **Step 2: Check Training Data Page**

```bash
# Open browser
open http://localhost:8000/camera/training
```

**Expected**:
- Pending Review: 1 (or more)
- Incident list shows inc_0001 with full details

### **Step 3: Review Incident**

1. Click **"✅ Confirm"**
2. Statistics update: Confirmed: 1
3. Incident disappears from pending list

### **Step 4: Export (when ≥100 confirmed)**

1. Click **"📦 Export Training Dataset"**
2. Creates 3 files:
   - `exports/training_dataset_YYYYMMDD_HHMMSS.jsonl`
   - `exports/coco_annotations_YYYYMMDD_HHMMSS.json`
   - `exports/manifest_YYYYMMDD_HHMMSS.json`

---

## Benefits

### **For Users**:
- ✅ **Zero manual data collection** - automatic from camera
- ✅ **Real data only** - no test/dummy data
- ✅ **Privacy-safe** - face detection + redaction
- ✅ **Full audit trail** - every decision recorded

### **For Developers**:
- ✅ **Clean integration** - one line of code
- ✅ **Error resilient** - failures don't break incidents
- ✅ **Extensible** - easy to add new rules/categories
- ✅ **Testable** - works with simulation

### **For Compliance**:
- ✅ **Provenance** - know where every example came from
- ✅ **Consent** - human confirms before fine-tuning
- ✅ **Privacy** - PII automatically detected
- ✅ **Audit** - full chain of custody

---

## Summary

**The missing step is now COMPLETE!**

```
✅ Camera detects (YOLO + tracking)
✅ Rules trigger (time-based)
✅ Incidents open/update/close
✅ Auto-convert to TrainingIncident  ← NEW!
✅ Appears on review page
✅ Human reviews
✅ Export for fine-tuning
```

**No more gaps. The pipeline flows end-to-end.**

**Real camera data → Real training data → Human-validated → Privacy-safe → Defensible export**

---

**All systems operational!** 🎉

