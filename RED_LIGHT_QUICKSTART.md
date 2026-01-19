# Alibi Red Light Enforcement - Quick Start

## 🚀 Quick Start (3 Steps)

### 1. Configure Traffic Camera

Edit `alibi/data/traffic_cameras.json`:

```json
{
  "cameras": [
    {
      "camera_id": "traffic_cam_001",
      "location": "Main St & 1st Ave",
      "traffic_light_roi": [50, 50, 100, 150],
      "stop_line": [[100, 400], [540, 400]],
      "intersection_roi": [0, 200, 640, 280],
      "traffic_direction": "up",
      "enabled": true
    }
  ]
}
```

### 2. Start Video Worker

```bash
python -m alibi.video.worker
```

The red light detector is automatically loaded for configured cameras.

### 3. Review Violations in Console

1. Open console: `http://localhost:3000`
2. Look for incidents with **orange "POSSIBLE RED LIGHT VIOLATION" banner**
3. Review annotated snapshot showing stop line and vehicle
4. Confirm or dismiss

## 📋 Configuration Guide

### Finding ROI Coordinates

Use this helper script to find coordinates:

```python
import cv2

# Load a frame from your camera
frame = cv2.imread("sample_frame.jpg")

# Display frame with coordinates
def show_coords(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Clicked: ({x}, {y})")

cv2.namedWindow("Frame")
cv2.setMouseCallback("Frame", show_coords)
cv2.imshow("Frame", frame)
cv2.waitKey(0)
```

### Configuration Parameters

| Parameter | What to Measure | Example |
|-----------|-----------------|---------|
| `traffic_light_roi` | Rectangle around traffic light | `[50, 50, 100, 150]` |
| `stop_line` | Two points defining the line | `[[100, 400], [540, 400]]` |
| `intersection_roi` | Area where vehicles appear | `[0, 200, 640, 280]` |
| `traffic_direction` | Direction vehicles move | `"up"` |

### Traffic Directions

- `"up"` - Vehicles moving toward top of frame
- `"down"` - Vehicles moving toward bottom
- `"left"` - Vehicles moving toward left
- `"right"` - Vehicles moving toward right

## 🧪 Testing

```bash
# Run all red light enforcement tests
pytest tests/test_red_light_enforcement.py -v

# Should see: 13 passed
```

## 🔧 Troubleshooting

### Traffic Light Not Detected?

1. **Check ROI position**: Light must be fully in ROI
2. **Verify lighting**: HSV works best in good light
3. **Adjust colors**: May need to tune HSV ranges

```python
# In light_state.py, adjust:
red_lower = [0, 100, 100]    # Increase first value if light appears orange
green_lower = [40, 50, 50]   # Adjust hue range
```

### Vehicles Not Detected?

1. **Check intersection ROI**: Must cover vehicle paths
2. **Wait for background learning**: First 500 frames
3. **Adjust contour sizes**:

```python
# In vehicle_detect.py:
min_contour_area = 1000   # Decrease for smaller vehicles
max_contour_area = 50000  # Increase for larger vehicles
```

### False Positives?

1. **Increase confidence threshold**: Edit settings
2. **Adjust stop line position**: Ensure correct placement
3. **Verify traffic direction**: Must match actual flow

## 🚨 Important

- **NEVER** issue citations without human review
- **ALWAYS** verify annotated snapshot before confirming
- **REQUIRE** supervisor approval for citations
- **PRESERVE** all evidence for legal proceedings

## 📊 Event Structure

Red light violation events look like this:

```json
{
  "event_type": "red_light_violation",
  "confidence": 0.85,
  "severity": 4,
  "snapshot_url": "/evidence/snapshots/red_light_cam001_20260118_120000.jpg",
  "metadata": {
    "light_state": "red",
    "light_confidence": 0.85,
    "camera_location": "Main St & 1st Ave",
    "vehicle_id": 42,
    "direction": "up",
    "requires_verification": true
  }
}
```

## 📁 Key Files

- **Configuration**: `alibi/data/traffic_cameras.json`
- **Annotated Snapshots**: `alibi/data/evidence/snapshots/`
- **Video Clips**: `alibi/data/evidence/clips/`
- **Tests**: `tests/test_red_light_enforcement.py`

## ✅ Production Checklist

- [ ] Camera positioned with clear view of light and stop line
- [ ] Configuration tested with sample frames
- [ ] Background subtraction learning period completed (500 frames)
- [ ] Human review workflow established
- [ ] Supervisor approval process in place
- [ ] Evidence storage and retention policy defined
- [ ] Operator training on verification requirements

## 📞 Support

See `RED_LIGHT_ENFORCEMENT_COMPLETE.md` for complete documentation.
