# Alibi Console Quick Start

## 🚀 Start the System

### Terminal 1: Backend
```bash
python -m alibi.alibi_api
```

### Terminal 2: Console
```bash
cd alibi/console
npm install  # First time only
npm run dev
```

### Terminal 3: Test Event Injection
```bash
curl -X POST http://localhost:8000/webhook/camera-event \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "test_001",
    "camera_id": "cam_main",
    "ts": "2026-01-18T16:30:00",
    "zone_id": "zone_entrance",
    "event_type": "person_detected",
    "confidence": 0.87,
    "severity": 3,
    "clip_url": "https://example.com/clip.mp4"
  }'
```

## ✅ Expected Behavior

1. Open `http://localhost:5173`
2. See empty incidents table
3. Run curl command above
4. **Incident appears instantly** (no refresh needed)
5. Click incident row
6. See full detail with plan, alert, validation
7. Click "Confirm" button
8. Redirects to list, **status updates via SSE**

## 🎹 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `j` | Next row |
| `k` | Previous row |
| `Enter` | Open incident |
| `r` | Refresh |

## 📊 Routes

- `/incidents` - Live table
- `/incidents/:id` - Detail view
- `/reports` - Shift reports
- `/settings` - Configuration

## 🔧 Troubleshooting

**Console not connecting?**
- Check backend is running on port 8000
- Check browser console for errors
- Verify `/api` proxy in vite.config.ts

**SSE not working?**
- Open browser DevTools → Network → Filter: EventStream
- Should see `/stream/incidents` connection
- Check for heartbeat every 10s

**npm install fails?**
- Use Node 18+ (check: `node --version`)
- Delete `node_modules` and `package-lock.json`, retry

## 📝 Test Scenarios

### 1. Multiple Events Merge
```bash
# Event 1
curl -X POST http://localhost:8000/webhook/camera-event \
  -H "Content-Type: application/json" \
  -d '{"event_id":"e1","camera_id":"cam_01","ts":"2026-01-18T16:00:00","zone_id":"zone_a","event_type":"person_detected","confidence":0.8,"severity":2}'

# Event 2 (10s later, same camera+zone)
curl -X POST http://localhost:8000/webhook/camera-event \
  -H "Content-Type: application/json" \
  -d '{"event_id":"e2","camera_id":"cam_01","ts":"2026-01-18T16:00:10","zone_id":"zone_a","event_type":"person_detected","confidence":0.85,"severity":3}'
```

**Expected**: Events merge into 1 incident, event_count = 2

### 2. High Severity Alert
```bash
curl -X POST http://localhost:8000/webhook/camera-event \
  -H "Content-Type: application/json" \
  -d '{"event_id":"e3","camera_id":"cam_02","ts":"2026-01-18T16:05:00","zone_id":"zone_restricted","event_type":"breach","confidence":0.92,"severity":5,"clip_url":"https://example.com/clip.mp4"}'
```

**Expected**: requires_approval badge, severity 5/5 (red)

### 3. Watchlist Match
```bash
curl -X POST http://localhost:8000/webhook/camera-event \
  -H "Content-Type: application/json" \
  -d '{"event_id":"e4","camera_id":"cam_03","ts":"2026-01-18T16:10:00","zone_id":"zone_b","event_type":"person_detected","confidence":0.88,"severity":3,"metadata":{"watchlist_match":true}}'
```

**Expected**: requires_approval, recommended_action = dispatch_pending_review

## 📦 Dependencies

**Backend:**
- fastapi
- uvicorn
- (already in requirements.txt)

**Frontend:**
- react
- react-dom
- react-router-dom
- @tanstack/react-table
- tailwindcss
- (see package.json)

## 🎯 Quick Checks

Backend running?
```bash
curl http://localhost:8000/health
```

Frontend building?
```bash
cd alibi/console && npm run build
```

SSE endpoint working?
```bash
curl -N http://localhost:8000/stream/incidents
# Should see heartbeats every 10s
```

---

**Ready to go!** See `ALIBI_CONSOLE_COMPLETE.md` for full documentation.
