# Alibi Video Package

Real-time CCTV ingestion pipeline with CPU-based detectors.

## Overview

The `alibi.video` package provides a complete video processing pipeline for security camera streams. It reads from RTSP cameras or local files, applies zone-based detection, and posts events to the Alibi API.

## Quick Start

```bash
# Install dependencies
pip install opencv-python>=4.8.0

# Start worker
python -m alibi.video.worker \
  --config alibi/data/cameras.json \
  --api http://localhost:8000
```

## Components

- **`rtsp_reader.py`**: Video stream reader (RTSP + local files)
- **`frame_sampler.py`**: Configurable FPS sampling
- **`zones.py`**: Polygon zone management
- **`worker.py`**: Main processing loop
- **`detectors/`**: Modular detector implementations
  - `base.py`: Abstract detector interface
  - `motion_detector.py`: Frame differencing motion detection
  - `presence_after_hours.py`: After-hours breach detection

## Configuration

### cameras.json

```json
{
  "cameras": [
    {
      "camera_id": "cam_entrance",
      "input": "rtsp://192.168.1.10/stream",
      "zone_id": "zone_entrance",
      "enabled": true,
      "sample_fps": 1.0
    }
  ]
}
```

### zones.json

```json
{
  "zones": [
    {
      "zone_id": "zone_entrance",
      "name": "Main Entrance",
      "polygon": [[100, 100], [500, 100], [500, 400], [100, 400]],
      "enabled": true
    }
  ]
}
```

## Usage Examples

### Read RTSP Stream

```python
from alibi.video.rtsp_reader import RTSPReader

reader = RTSPReader("rtsp://camera.local/stream")

for frame in reader.frames():
    # Process frame
    print(f"Frame shape: {frame.shape}")
```

### Sample Frames

```python
from alibi.video.frame_sampler import FrameSampler, SamplerConfig

config = SamplerConfig(target_fps=1.0)
sampler = FrameSampler(config)

for frame in sampler.sample(reader.frames()):
    # Process 1 frame per second
    pass
```

### Zone Masking

```python
from alibi.video.zones import Zone

zone = Zone(
    zone_id="test",
    name="Test Zone",
    polygon=[(100, 100), (200, 100), (200, 200), (100, 200)]
)

mask = zone.create_mask(640, 480)
```

### Motion Detection

```python
from alibi.video.detectors.motion_detector import MotionDetector

detector = MotionDetector()

result = detector.detect(frame, timestamp, zone=zone)

if result and result.detected:
    print(f"Motion detected: {result.event_type}")
    print(f"Confidence: {result.confidence}")
    print(f"Severity: {result.severity}")
```

### Custom Detector

```python
from alibi.video.detectors.base import Detector, DetectionResult

class MyDetector(Detector):
    def detect(self, frame, timestamp, **kwargs):
        # Your detection logic here
        
        if something_detected:
            return DetectionResult(
                detected=True,
                event_type="my_event",
                confidence=0.9,
                severity=3,
                metadata={"key": "value"}
            )
        
        return None
```

## CLI

```bash
# Basic usage
python -m alibi.video.worker \
  --config cameras.json \
  --api http://localhost:8000

# Custom zones file
python -m alibi.video.worker \
  --config cameras.json \
  --api http://localhost:8000 \
  --zones my_zones.json
```

## Docker

```bash
# Build worker image
docker build -f Dockerfile.worker -t alibi_worker .

# Run worker
docker run -v $(pwd)/alibi/data:/app/alibi/data alibi_worker \
  python -m alibi.video.worker \
  --config alibi/data/cameras.json \
  --api http://alibi_api:8000
```

## Testing

```bash
# Run all tests
pytest tests/test_video_processing.py -v

# Run specific test class
pytest tests/test_video_processing.py::TestMotionDetector -v
```

## Performance

- **CPU Usage**: ~10-15% per camera at 1 FPS sampling
- **Memory**: ~50MB per camera stream
- **Latency**: <100ms from frame to API post
- **Scalability**: 4-8 cameras per worker (CPU-dependent)

## Event Flow

```
Camera Frame
    ↓
RTSP Reader
    ↓
Frame Sampler (1 FPS)
    ↓
Motion Detector → DetectionResult
    ↓
Event Throttler
    ↓
API Client (POST /webhook/camera-event)
    ↓
Alibi Incident Created
```

## Detectors

### Motion Detector

- **Algorithm**: Frame differencing with morphological operations
- **Event Type**: `motion_in_zone`
- **Confidence**: Based on activity ratio
- **Severity**: 1-3 (depends on motion area)

### After-Hours Detector

- **Algorithm**: Motion detection during configured time window
- **Event Type**: `perimeter_breach`
- **Confidence**: 0.85+ (high)
- **Severity**: 4-5 (high)
- **Default Window**: 22:00-06:00

## Troubleshooting

### RTSP Connection Issues

```bash
# Test with ffplay
ffplay rtsp://camera.local/stream

# Check network
ping camera.local
```

### High CPU Usage

Reduce sampling rate:
```json
{
  "sample_fps": 0.5
}
```

### No Motion Detected

Lower thresholds:
```python
MotionDetector(config={
    'threshold': 15,
    'min_area': 200
})
```

## Dependencies

- `opencv-python>=4.8.0`
- `numpy>=1.24.0`
- `requests>=2.31.0`

## Documentation

- [VIDEO_WORKER_COMPLETE.md](../../VIDEO_WORKER_COMPLETE.md): Full documentation
- [VIDEO_WORKER_QUICKSTART.md](../../VIDEO_WORKER_QUICKSTART.md): Quick start guide

## License

Part of the Alibi incident management system.
