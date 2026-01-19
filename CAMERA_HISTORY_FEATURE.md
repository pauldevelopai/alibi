# 📸 Camera History Feature

**Visual gallery of AI-analyzed camera snapshots with smart storage management**

---

## ✨ Overview

The Camera History feature provides a visual gallery to browse all camera snapshots that have been analyzed by AI, complete with descriptions, detected objects, and safety alerts.

**Key Innovation**: Stores only **snapshots** (images), NOT videos - keeping storage manageable while providing complete audit trail.

---

## 🎯 Features

### Gallery View
- **Grid layout** with thumbnails
- **AI descriptions** on each card
- **Timestamp** and user info
- **Safety concerns** highlighted with red border
- **Responsive design** for mobile and desktop

### Filtering
- **All** - Show all snapshots
- **Today** - Only today's snapshots
- **Safety Concerns** - Only flagged items
- **This Week** - Last 7 days

### Statistics Dashboard
- Total snapshots count
- Safety concerns count
- Today's snapshot count

### Full View Modal
- Click any snapshot to see full-size image
- Complete analysis details
- All detected objects and activities
- Confidence score and method used

### Storage Management
- **Auto-cleanup**: Deletes snapshots older than 7 days
- **Manual cleanup**: "🗑️ Cleanup" button
- **Smart compression**: JPEG with optimized quality
- **Thumbnails**: Fast loading 400px previews

---

## 📱 How to Access

### Desktop
```
https://McNallyMac.local:8000/
→ Login
→ Tap "📸 Camera History" card
```

### iPhone
```
https://McNallyMac.local:8000/
→ Login  
→ Tap "📸 Camera History" (under Operations section)
```

### Direct URL
```
https://McNallyMac.local:8000/camera/history
```

---

## 💾 Storage Management

### What Gets Stored

✅ **Snapshots** (full-size images)
- JPEG format, 85% quality
- ~50-200 KB per image
- Location: `alibi/data/camera_snapshots/`

✅ **Thumbnails** (preview images)
- JPEG format, 70% quality
- Max 400px width
- ~10-30 KB per image
- Location: `alibi/data/camera_snapshots/thumbnails/`

✅ **Metadata** (AI analysis)
- JSONL format (one record per line)
- ~1 KB per analysis
- Location: `alibi/data/camera_analysis.jsonl`

❌ **NO VIDEOS STORED** (keeps storage minimal!)

### Storage Estimates

| Usage Level | Snapshots/Day | Storage/Day | Weekly Total |
|-------------|---------------|-------------|--------------|
| **Light** | 50 | ~5 MB | ~35 MB |
| **Normal** | 200 | ~20 MB | ~140 MB |
| **Heavy** | 500 | ~50 MB | ~350 MB |

**Result**: Even heavy use only needs ~350 MB for a full week!

### Retention Policy

**Default**: 7 days auto-delete

Files older than 7 days are automatically removed:
- Snapshot images
- Thumbnail images
- JSONL metadata records

**Configurable**: Edit `retention_days` in `CameraAnalysisStore` initialization

```python
from alibi.camera_analysis_store import CameraAnalysisStore

store = CameraAnalysisStore(retention_days=14)  # Keep 14 days
```

### Manual Cleanup

**Via UI**:
- Go to Camera History page
- Tap "🗑️ Cleanup" button
- Confirms before deleting

**Via API**:
```bash
curl -X POST https://McNallyMac.local:8000/camera/cleanup \
  -H "Authorization: Bearer $TOKEN"
```

**Returns**:
```json
{
  "deleted": 234,
  "message": "Cleaned up 234 old files"
}
```

---

## 🔧 Technical Details

### API Endpoints

**Get Recent Analyses**
```
GET /camera/analysis/recent?hours=168&limit=500
```
Returns list of camera analyses with snapshot paths

**Cleanup Old Files**
```
POST /camera/cleanup
```
Deletes files older than retention policy

### File Structure

```
alibi/data/
├── camera_snapshots/
│   ├── 20260119_101530_abc123.jpg     # Full snapshot
│   ├── 20260119_101535_def456.jpg
│   └── thumbnails/
│       ├── 20260119_101530_abc123.jpg # Thumbnail
│       └── 20260119_101535_def456.jpg
└── camera_analysis.jsonl              # Metadata
```

### Snapshot Naming

Format: `YYYYMMDD_HHMMSS_analysisid.jpg`

Example: `20260119_153042_550e8400-e29b-41d4-a716-446655440000.jpg`

- Date/time: Easy sorting and cleanup
- Analysis ID: Link to metadata record
- JPEG: Universal format

### Image Quality

**Full Snapshots**:
- JPEG quality: 85%
- Original resolution (from camera)
- Good quality for evidence
- ~50-200 KB depending on content

**Thumbnails**:
- JPEG quality: 70%
- Max width: 400px (height scaled proportionally)
- Fast loading for gallery
- ~10-30 KB per thumbnail

---

## 📊 Use Cases

### 1. Review Past Detections
Browse chronologically to see what cameras detected over time.

### 2. Audit Safety Concerns
Filter by safety concerns to review all flagged incidents.

### 3. Training & Validation
See what AI is detecting to validate accuracy and identify patterns.

### 4. Incident Correlation
Link camera captures to incidents for timeline reconstruction.

### 5. Shift Reports
Visual summary of key detections during a shift.

### 6. Evidence Gathering
Export snapshots for reports or legal proceedings.

---

## 🔒 Security

- ✅ **Authentication Required**: JWT token needed
- ✅ **Role-Based Access**: All authenticated roles can view
- ✅ **Audit Trail**: User recorded for each snapshot
- ✅ **Secure Storage**: Files stored in protected directory
- ✅ **Auto-Cleanup**: Prevents long-term data retention issues

---

## 🎨 UI Design

### Mobile-First
- Responsive grid layout
- Touch-friendly cards
- Smooth animations
- Native iOS feel

### Color Coding
- **White cards**: Normal snapshots
- **Red border**: Safety concerns
- **Purple gradient**: Background
- **Blue/green**: Interactive elements

### Performance
- Thumbnails load fast
- Lazy loading for large galleries
- Smooth scrolling
- Instant filtering

---

## 🚀 Getting Started

### Step 1: Use Camera
```
https://McNallyMac.local:8000/camera/mobile-stream
```
Point camera at various objects for 1-2 minutes

### Step 2: View History
```
https://McNallyMac.local:8000/camera/history
```
Browse your captured snapshots

### Step 3: Explore Features
- Try different filters
- Click snapshots for full view
- Check statistics bar
- Test cleanup button

---

## 📈 Monitoring Storage

### Check Current Usage

```bash
# Snapshot directory size
du -sh alibi/data/camera_snapshots/

# Count files
find alibi/data/camera_snapshots/ -name "*.jpg" | wc -l

# Metadata file size
ls -lh alibi/data/camera_analysis.jsonl
```

### Automated Monitoring

Set up a cron job to run cleanup daily:

```bash
# Daily cleanup at 2 AM
0 2 * * * curl -X POST http://localhost:8000/camera/cleanup \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔧 Configuration

### Change Retention Period

Edit `alibi/camera_analysis_store.py`:

```python
def __init__(self, 
             store_file: str = "alibi/data/camera_analysis.jsonl",
             snapshots_dir: str = "alibi/data/camera_snapshots",
             retention_days: int = 14):  # Change from 7 to 14
```

### Change Image Quality

Edit `save_snapshot` method:

```python
# Full snapshot quality (default: 85)
cv2.imwrite(str(snapshot_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

# Thumbnail quality (default: 70)
cv2.imwrite(str(thumbnail_path), thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 80])
```

### Change Thumbnail Size

Edit `save_snapshot` method:

```python
# Change from 400 to 600
if width > 600:
    scale = 600 / width
    new_width = 600
    # ...
```

---

## ✅ Benefits

### For Operators
- ✅ Quick visual review of past detections
- ✅ Easy filtering and search
- ✅ Evidence gathering
- ✅ Mobile-friendly interface

### For Supervisors
- ✅ Audit safety concerns
- ✅ Validate AI accuracy
- ✅ Training data collection
- ✅ Shift summaries

### For Admins
- ✅ System monitoring
- ✅ Storage management
- ✅ Pattern analysis
- ✅ Report generation

### For System
- ✅ Minimal storage footprint
- ✅ Auto-cleanup prevents bloat
- ✅ Fast loading (thumbnails)
- ✅ Scalable architecture

---

## 🎯 Summary

**Camera History provides a complete visual audit trail of AI camera analysis while keeping storage minimal through smart snapshot-only storage and auto-cleanup.**

**Key Stats**:
- 📸 Snapshots only (no videos!)
- 🗑️ Auto-cleanup after 7 days
- 💾 ~70 MB for full week (normal use)
- ⚡ Fast loading with thumbnails
- 🔒 Secure and authenticated
- 📱 Mobile-optimized interface

**Perfect for Namibia pilot deployment!** 🇳🇦✨
