# Alibi Video Worker - Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies

```bash
pip install opencv-python>=4.8.0
```

All other dependencies should already be installed from `requirements.txt`.

### 2. Create Test Video (Optional)

```bash
python create_test_video.py
```

This creates `alibi/data/test_video.mp4` with simulated motion.

### 3. Configure Cameras

Edit `alibi/data/cameras.json`:

```json
{
  "cameras": [
    {
      "camera_id": "cam_entrance_main",
      "input": "alibi/data/test_video.mp4",
      "zone_id": "zone_entrance",
      "enabled": true,
      "sample_fps": 1.0
    }
  ]
}
```

**For RTSP streams**, use:
```json
{
  "input": "rtsp://192.168.1.10:554/stream1"
}
```

### 4. Start the API

Terminal 1:
```bash
python -m alibi.alibi_api
```

Wait for:
```
🔒 Starting Alibi API server...
   Host: 0.0.0.0
   Port: 8000
```

### 5. Start the Video Worker

Terminal 2:
```bash
python -m alibi.video.worker \
  --config alibi/data/cameras.json \
  --api http://localhost:8000
```

Expected output:
```
============================================================
Alibi Video Worker Starting
============================================================
API URL: http://localhost:8000
Cameras: 1
Zones: 7
Detectors: 2
Throttle: 30s
============================================================

[Worker] Starting camera: cam_entrance_main
[RTSPReader] Opened: alibi/data/test_video.mp4
[Worker] ✓ Event sent: motion_in_zone → incident_xxx
```

### 6. View Incidents

**Option A: Browser**
```bash
# Start console (Terminal 3)
cd alibi/console
npm run dev

# Open browser
open http://localhost:5173/incidents
```

**Option B: API**
```bash
curl http://localhost:8000/incidents | jq
```

## Docker Quick Start

### 1. Build and Run

```bash
docker-compose up
```

This starts:
- `alibi_api` on port 8000
- `alibi_worker` processing videos
- `alibi_console` on port 5173

### 2. View Logs

```bash
# Worker logs
docker-compose logs -f alibi_worker

# API logs
docker-compose logs -f alibi_api
```

### 3. Stop

```bash
docker-compose down
```

## Common Scenarios

### Scenario 1: Test with Local MP4

```json
{
  "camera_id": "cam_test",
  "input": "/path/to/video.mp4",
  "zone_id": "zone_entrance",
  "sample_fps": 2.0
}
```

### Scenario 2: RTSP Camera

```json
{
  "camera_id": "cam_entrance",
  "input": "rtsp://192.168.1.10:554/stream1",
  "zone_id": "zone_entrance",
  "sample_fps": 1.0
}
```

### Scenario 3: Multiple Cameras

```json
{
  "cameras": [
    {
      "camera_id": "cam_entrance",
      "input": "rtsp://192.168.1.10/stream",
      "zone_id": "zone_entrance"
    },
    {
      "camera_id": "cam_parking",
      "input": "rtsp://192.168.1.11/stream",
      "zone_id": "zone_parking"
    }
  ]
}
```

### Scenario 4: After-Hours Monitoring

Automatically enabled! The `PresenceAfterHoursDetector` runs 24/7 and triggers `perimeter_breach` events between 22:00-06:00 by default.

To customize times, modify the detector configuration in `worker.py`:

```python
PresenceAfterHoursDetector(
    name="after_hours",
    config={
        'after_hours_start': '20:00',  # 8 PM
        'after_hours_end': '08:00',    # 8 AM
    }
)
```

## Troubleshooting

### Issue: "opencv-python not found"

```bash
pip install opencv-python>=4.8.0
```

### Issue: "Failed to open RTSP stream"

1. Test RTSP URL:
```bash
ffplay rtsp://192.168.1.10/stream
```

2. Check network:
```bash
ping 192.168.1.10
```

3. Verify credentials (if required):
```
rtsp://username:password@192.168.1.10/stream
```

### Issue: "No motion detected"

1. Lower threshold:
```python
# In worker.py
MotionDetector(
    config={'threshold': 15, 'min_area': 200}
)
```

2. Check zone coverage:
```python
# Visualize zones
from alibi.video.zones import ZoneManager
manager = ZoneManager("alibi/data/zones.json")
# Draw zones on frame and inspect
```

### Issue: "Too many events"

Increase throttle:
```json
{
  "event_throttle_seconds": 60
}
```

### Issue: "Worker crashes on video file"

Video file might be corrupted or unsupported format. Try:
```bash
# Re-encode with ffmpeg
ffmpeg -i input.mp4 -c:v libx264 -c:a aac output.mp4
```

## Configuration Reference

### Camera Config

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `camera_id` | string | Unique camera identifier | `"cam_entrance"` |
| `input` | string | RTSP URL or file path | `"rtsp://..."` or `"/path/to/video.mp4"` |
| `zone_id` | string | Associated zone ID | `"zone_entrance"` |
| `enabled` | boolean | Enable/disable camera | `true` |
| `sample_fps` | float | Frames to process per second | `1.0` |

### Worker Config

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `event_throttle_seconds` | int | Seconds between duplicate events | `30` |
| `api_timeout` | int | API request timeout | `10` |
| `api_retry_max` | int | Max retry attempts | `3` |
| `api_retry_delay` | float | Initial retry delay (exponential) | `2.0` |

### Zone Config

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `zone_id` | string | Unique zone identifier | `"zone_entrance"` |
| `name` | string | Human-readable name | `"Main Entrance"` |
| `polygon` | array | List of [x, y] points | `[[100, 100], [200, 100], ...]` |
| `enabled` | boolean | Enable/disable zone | `true` |

## Testing

### Run Unit Tests

```bash
pytest tests/test_video_processing.py -v
```

Expected: 27 tests pass

### End-to-End Test

```bash
# 1. Create test video
python create_test_video.py

# 2. Start API
python -m alibi.alibi_api &

# 3. Wait 5 seconds
sleep 5

# 4. Start worker
python -m alibi.video.worker \
  --config alibi/data/cameras.json \
  --api http://localhost:8000

# 5. Check incidents
curl http://localhost:8000/incidents | jq '. | length'

# Expected: At least 1 incident
```

## Performance Tuning

### Reduce CPU Usage

```json
{
  "sample_fps": 0.5
}
```

Processes 1 frame every 2 seconds instead of every second.

### Increase Detection Sensitivity

```python
MotionDetector(config={
    'threshold': 15,      # Lower threshold
    'min_area': 200,      # Smaller minimum area
    'activity_threshold': 0.005  # Lower activity threshold
})
```

### Decrease Detection Sensitivity

```python
MotionDetector(config={
    'threshold': 35,      # Higher threshold
    'min_area': 1000,     # Larger minimum area
    'activity_threshold': 0.02  # Higher activity threshold
})
```

## Next Steps

1. **Deploy with Real Cameras**: Replace test video with RTSP URLs
2. **Tune Zones**: Adjust polygon coordinates to match camera views
3. **Monitor Performance**: Track CPU usage, event rates
4. **Add Custom Detectors**: Extend `Detector` base class
5. **Scale Up**: Run multiple workers for different camera groups

## Support

- **Full Documentation**: [VIDEO_WORKER_COMPLETE.md](VIDEO_WORKER_COMPLETE.md)
- **API Docs**: http://localhost:8000/docs
- **Tests**: `pytest tests/test_video_processing.py -v`
