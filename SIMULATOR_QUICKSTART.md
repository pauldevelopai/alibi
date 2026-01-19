# Alibi Simulator - Quick Start Guide

## 5-Minute Demo

### Prerequisites

- Python 3.9+ with dependencies installed
- Node.js 18+ (for frontend)
- Terminal access

### Step 1: Start the Backend API

```bash
cd /path/to/alibi
python -m alibi.alibi_api
```

Expected output:
```
🔒 Starting Alibi API server...
   Host: 0.0.0.0
   Port: 8000
   Docs: http://localhost:8000/docs
```

### Step 2: Start the Frontend Console (Optional)

In a new terminal:

```bash
cd alibi/console
npm install  # First time only
npm run dev
```

Expected output:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Step 3: Start the Simulator

**Option A: Via API (curl)**

```bash
curl -X POST http://localhost:8000/sim/start \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "security_incident",
    "rate_per_min": 30,
    "seed": 42
  }'
```

**Option B: Via Frontend Demo Panel**

1. Open http://localhost:5173/incidents
2. Click "← Demo" button on right edge
3. Select scenario: "Security Incident"
4. Set rate: 30 events/min
5. Enter seed: 42
6. Click "Start"

### Step 4: Watch Incidents Stream Live

**In Browser:**
- Incidents appear in real-time on `/incidents` page
- Click any incident to view Replay Timeline
- Status badges update automatically

**Via API:**
```bash
# Check simulator status
curl http://localhost:8000/sim/status

# List incidents
curl http://localhost:8000/incidents | jq
```

### Step 5: Stop the Simulator

**Via API:**
```bash
curl -X POST http://localhost:8000/sim/stop
```

**Via Frontend:**
- Click "Stop" button in Demo Panel

## Common Scenarios

### Quiet Night Shift

```bash
curl -X POST http://localhost:8000/sim/start \
  -d '{"scenario": "quiet_shift", "rate_per_min": 5}'
```

Low event rate, mostly routine detections.

### Busy Evening

```bash
curl -X POST http://localhost:8000/sim/start \
  -d '{"scenario": "busy_evening", "rate_per_min": 40}'
```

High event rate, mix of loitering and crowd anomalies.

### Security Incident

```bash
curl -X POST http://localhost:8000/sim/start \
  -d '{"scenario": "security_incident", "rate_per_min": 20}'
```

High severity events: perimeter breaches, aggression proxies.

### Deterministic Demo

```bash
curl -X POST http://localhost:8000/sim/start \
  -d '{"scenario": "mixed_events", "rate_per_min": 15, "seed": 999}'
```

Same seed = same events every time (reproducible).

## Replay Historical Events

### Create JSONL File

```bash
cat > demo_events.jsonl << 'EOF'
{"event_id":"demo_001","camera_id":"cam_entrance_main","ts":"2026-01-18T10:00:00","zone_id":"zone_entrance","event_type":"person_detected","confidence":0.85,"severity":2,"clip_url":"https://example.com/clip1.mp4","snapshot_url":"https://example.com/snap1.jpg","metadata":{"person_count":1}}
{"event_id":"demo_002","camera_id":"cam_entrance_main","ts":"2026-01-18T10:02:00","zone_id":"zone_entrance","event_type":"loitering","confidence":0.78,"severity":3,"clip_url":"https://example.com/clip2.mp4","snapshot_url":"https://example.com/snap2.jpg","metadata":{"duration_seconds":180}}
{"event_id":"demo_003","camera_id":"cam_perimeter_east","ts":"2026-01-18T10:05:00","zone_id":"zone_perimeter_east","event_type":"perimeter_breach","confidence":0.88,"severity":4,"clip_url":"https://example.com/clip3.mp4","snapshot_url":"https://example.com/snap3.jpg","metadata":{"breach_type":"fence_crossing","after_hours":true}}
EOF
```

### Replay via API

```bash
curl -X POST http://localhost:8000/sim/replay \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "file_path": "demo_events.jsonl"
}
EOF
```

### Replay via Frontend

1. Open Demo Panel
2. Scroll to "Replay JSONL" section
3. Paste JSONL content
4. Click "Replay Events"

## Troubleshooting

### Simulator Won't Start

**Error**: "Simulator already running"

**Solution**: Stop existing simulator first:
```bash
curl -X POST http://localhost:8000/sim/stop
```

### No Incidents Appearing

**Check simulator status:**
```bash
curl http://localhost:8000/sim/status
```

**Verify events are being generated:**
- `events_generated` should be increasing
- `incidents_created` should be > 0

**Check API logs:**
- Look for validation errors
- Verify events are schema-compliant

### Invalid Scenario Error

**Error**: "Invalid scenario. Must be one of: ..."

**Valid scenarios:**
- `quiet_shift`
- `normal_day`
- `busy_evening`
- `security_incident`
- `mixed_events`

### Replay Fails

**Check JSONL format:**
- One JSON object per line
- No trailing commas
- Valid ISO 8601 timestamps
- Confidence: 0.0-1.0
- Severity: 1-5

**Example valid event:**
```json
{"event_id":"evt_001","camera_id":"cam_test","ts":"2026-01-18T12:00:00","zone_id":"zone_test","event_type":"person_detected","confidence":0.85,"severity":2,"clip_url":null,"snapshot_url":null,"metadata":{}}
```

## Testing

### Run Unit Tests

```bash
python test_simulator.py
```

Expected: 6 tests pass

### Run API Tests

```bash
./test_simulator_api.sh
```

Expected: 9 tests pass

### Manual Verification

```bash
# Start simulator
curl -X POST http://localhost:8000/sim/start \
  -d '{"scenario": "normal_day", "rate_per_min": 20, "seed": 42}'

# Wait 10 seconds
sleep 10

# Check status
curl http://localhost:8000/sim/status | jq

# Should show:
# - running: true
# - events_generated: ~3-4
# - incidents_created: >= 1

# Check incidents
curl http://localhost:8000/incidents | jq '. | length'

# Should show: >= 1

# Stop
curl -X POST http://localhost:8000/sim/stop
```

## Next Steps

- Read [SIMULATOR_COMPLETE.md](SIMULATOR_COMPLETE.md) for full documentation
- Explore different scenarios and rates
- Create custom JSONL replay files
- Integrate with your testing workflows

## Support

For issues or questions:
1. Check API docs: http://localhost:8000/docs
2. Review logs in terminal
3. Verify schema compliance with `test_simulator.py`
