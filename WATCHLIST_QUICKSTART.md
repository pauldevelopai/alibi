# Alibi Watchlist - Quick Start Guide

## 🚀 Quick Start (3 Steps)

### 1. Enroll a Face

```bash
python -m alibi.watchlist.enroll \
  --person_id SUSPECT_001 \
  --label "John Doe" \
  --image /path/to/photo.jpg \
  --source "Warrant #2024-1234"
```

Or use the sample enrollment:

```bash
python scripts/enroll_sample_face.py
```

### 2. Start the Video Worker

```bash
python -m alibi.video.worker
```

The watchlist detector is automatically active.

### 3. Review Matches in Console

1. Open console: `http://localhost:3000`
2. Look for incidents with **yellow "VERIFY VISUALLY" banner**
3. Review face crop, candidates, and evidence
4. Supervisor confirms or dismisses

## 📋 Configuration

Edit `alibi/data/alibi_settings.json`:

```json
{
  "watchlist": {
    "enabled": true,
    "match_threshold": 0.6,        // Higher = stricter matching
    "face_confidence": 0.5,        // Face detection threshold
    "check_interval_seconds": 5.0, // How often to check faces
    "reload_interval_seconds": 300,// How often to reload watchlist
    "top_k_candidates": 3          // Number of matches to return
  }
}
```

## 🔒 Safety Rules

### Automatic Enforcement

- ✅ "Possible match" language required
- ✅ Human approval required
- ✅ Evidence attached (face crop + snapshot + clip)
- ✅ Supervisor-only confirmation
- ❌ Identity claims blocked
- ❌ Automatic dispatch blocked

### Operator Workflow

1. **Incident Alert**: Yellow banner appears
2. **Visual Review**: Compare face crop to candidates
3. **Supervisor Decision**: Confirm or dismiss
4. **Audit Log**: All actions recorded

## 🧪 Testing

```bash
# Run all watchlist tests
pytest tests/test_watchlist.py -v

# Should see: 15 passed
```

## 📊 API Quick Reference

### Get Watchlist (Supervisor+)

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/watchlist
```

### Watchlist Match Event Structure

```json
{
  "event_type": "watchlist_match",
  "confidence": 0.85,
  "severity": 4,
  "metadata": {
    "match_score": 0.85,
    "top_candidates": [
      {"person_id": "SUSPECT_001", "label": "John Doe", "score": 0.85}
    ],
    "face_crop_url": "/evidence/face_crops/face_xxx.jpg",
    "requires_verification": true
  }
}
```

## 🚨 Important

- **NEVER** assume identity from automated match
- **ALWAYS** require visual verification
- **SUPERVISOR** approval required for confirmation
- **AUDIT LOG** records all actions

## 📁 Key Files

- **Watchlist Data**: `alibi/data/watchlist.jsonl`
- **Face Crops**: `alibi/data/evidence/face_crops/`
- **Settings**: `alibi/data/alibi_settings.json`
- **Tests**: `tests/test_watchlist.py`

## 🔧 Troubleshooting

### No faces detected?

- Check face image quality (well-lit, frontal view)
- Lower `face_confidence` threshold
- Verify OpenCV installation: `python -c "import cv2; print(cv2.__version__)"`

### Low match accuracy?

- Install `face-recognition` for better embeddings:
  ```bash
  pip install face-recognition
  ```
- Adjust `match_threshold` (higher = stricter)

### Performance issues?

- Increase `check_interval_seconds` (check less frequently)
- Reduce number of cameras processed simultaneously

## ✅ Production Checklist

- [ ] Legal basis for watchlist enrollment (warrants, case numbers)
- [ ] Operator training on verification requirements
- [ ] Supervisor approval workflow tested
- [ ] Audit logging verified
- [ ] Evidence capture working (face crops, snapshots, clips)
- [ ] Role-based access control configured
- [ ] Test with sample faces before live deployment

## 📞 Support

See `WATCHLIST_IMPLEMENTATION.md` for complete documentation.
