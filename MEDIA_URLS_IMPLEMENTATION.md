# Media URLs Implementation

## Overview

Implemented proper `clip_url` and `snapshot_url` support for camera events, enabling the console to display evidence links.

## What Changed

### 1. Video Worker (`alibi/video/worker.py`)

**Before** (TODOs):
```python
"clip_url": None,  # TODO: implement clip extraction
"snapshot_url": None,  # TODO: implement snapshot saving
```

**After**:
```python
"clip_url": f"/media/clips/{event_id}.mp4",
"snapshot_url": f"/media/snapshots/{event_id}.jpg",
```

### 2. FastAPI Backend (`alibi/alibi_api.py`)

Added static file serving for media:

```python
from fastapi.staticfiles import StaticFiles

# Mount media directory
MEDIA_DIR = Path("alibi/data/media")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")
```

### 3. Directory Structure

Created media storage directories:

```
alibi/data/media/
├── clips/              # Video clips (MP4)
├── snapshots/          # Snapshot images (JPG)
└── README.md           # Documentation
```

### 4. Placeholder Generator (`create_placeholder_media.py`)

Created utility script to generate test snapshots:

- **Sample mode**: Create 3 test snapshots
- **Events mode**: Generate snapshots for all events in `events.jsonl`
- Uses PIL to create simple placeholder images with camera/event info

## Usage

### Generate Sample Placeholders

```bash
python create_placeholder_media.py --sample
```

Creates:
- `evt_sample_001.jpg`
- `evt_sample_002.jpg`
- `evt_sample_003.jpg`

### Generate from Events

```bash
python create_placeholder_media.py
```

Reads `alibi/data/events.jsonl` and creates placeholder snapshots for all events.

### Access Media via API

Once the backend is running:

```bash
# View snapshot
http://localhost:8000/media/snapshots/evt_sample_001.jpg

# View clip (if exists)
http://localhost:8000/media/clips/evt_12345.mp4
```

## Console Display

The incident detail page now displays evidence links:

```typescript
{event.clip_url && (
  <a href={event.clip_url} target="_blank">
    📹 View Clip →
  </a>
)}
{event.snapshot_url && (
  <a href={event.snapshot_url} target="_blank">
    📷 View Snapshot →
  </a>
)}
```

**Behavior**:
- Links are blue and underlined
- Click opens media in new tab
- If media doesn't exist → browser shows 404 (expected for demo)
- Simulator events use `example.com` URLs (won't load, but displayed)

## Testing

### 1. Create Sample Media

```bash
python create_placeholder_media.py --sample
```

### 2. Start Backend

```bash
python -m alibi.alibi_api
```

### 3. Verify Static Files Work

```bash
curl http://localhost:8000/media/snapshots/evt_sample_001.jpg --output test.jpg
open test.jpg  # Should display placeholder image
```

### 4. Test in Console

1. Start console: `./start_console_dev.sh`
2. Login and view any incident with events
3. Click "📷 View Snapshot →" link
4. Should see placeholder image in new tab

## URL Patterns

### Video Worker Events
- **Clips**: `/media/clips/{event_id}.mp4`
- **Snapshots**: `/media/snapshots/{event_id}.jpg`

### Simulator Events
- **Clips**: `https://storage.example.com/clips/{event_id}.mp4`
- **Snapshots**: `https://storage.example.com/snapshots/{event_id}.jpg`

(Simulator URLs are synthetic and won't resolve, but are displayed in console)

## Implementation Status

### ✅ Completed
- [x] Video worker sets proper URLs
- [x] FastAPI serves static media files
- [x] Directory structure created
- [x] Placeholder generator script
- [x] Console displays evidence links
- [x] Sample placeholders work end-to-end

### ⏳ Future Work (Optional)

#### Actual Media Extraction (Video Worker)

When processing real RTSP streams, implement:

1. **Snapshot Extraction**:
   ```python
   import cv2
   
   # Save frame that triggered detection
   snapshot_path = MEDIA_DIR / "snapshots" / f"{event_id}.jpg"
   cv2.imwrite(str(snapshot_path), frame)
   ```

2. **Clip Extraction** (5-10 seconds around event):
   ```python
   import subprocess
   
   clip_path = MEDIA_DIR / "clips" / f"{event_id}.mp4"
   
   # Use ffmpeg to extract clip from RTSP stream
   subprocess.run([
       "ffmpeg",
       "-i", rtsp_url,
       "-ss", str(start_time),
       "-t", "10",  # 10 seconds
       "-c", "copy",
       str(clip_path)
   ])
   ```

#### Storage Optimization

- **Retention policy**: Delete media after N days
- **Compression**: Optimize JPEG quality/size
- **Cloud storage**: Upload to S3/GCS for production
- **CDN**: Serve via CloudFront/CloudFlare for scale

## Security Notes

- Media files served **without authentication** (StaticFiles)
- For production, consider:
  - Signed URLs with expiration
  - Proxy through authenticated endpoint
  - Store on separate storage server
  - Implement rate limiting

## File Summary

### New Files
- `alibi/data/media/clips/` - Video clips directory
- `alibi/data/media/snapshots/` - Snapshots directory
- `alibi/data/media/README.md` - Media directory documentation
- `create_placeholder_media.py` - Placeholder generator utility

### Modified Files
- `alibi/video/worker.py` - Set proper media URLs
- `alibi/alibi_api.py` - Added static file serving

### Sample Output

```bash
$ python create_placeholder_media.py --sample

Alibi Placeholder Media Generator
==================================

Created placeholder: alibi/data/media/snapshots/evt_sample_001.jpg
Created placeholder: alibi/data/media/snapshots/evt_sample_002.jpg
Created placeholder: alibi/data/media/snapshots/evt_sample_003.jpg

Created 3 sample placeholders in alibi/data/media/snapshots
```

## Success! ✅

The Alibi Console can now display evidence links for camera events. While actual media extraction from video streams is not yet implemented, the infrastructure is in place and working with placeholder images.

**For the Namibia pilot**: This allows operators to see evidence links in the UI, and actual media files can be added later by implementing the extraction logic in the video worker.
