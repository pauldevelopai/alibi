# Alibi Event Simulator

Demo-grade event generation and replay system for the Alibi incident management platform.

## Overview

The Alibi Event Simulator generates realistic camera events for demonstrations, testing, and development. It feeds the **same ingestion endpoint** (`/webhook/camera-event`) as production cameras, ensuring complete integration fidelity.

## Features

- ✅ **7 Event Types**: person_detected, vehicle_detected, loitering, perimeter_breach, crowd_anomaly, aggression_proxy, vehicle_stop_restricted
- ✅ **5 Scenario Presets**: quiet_shift, normal_day, busy_evening, security_incident, mixed_events
- ✅ **Deterministic Seeding**: Reproducible event sequences for testing
- ✅ **Rate Control**: 0.1-120 events per minute
- ✅ **Strict Validation**: Rejects invalid events (no silent fixes)
- ✅ **JSONL Replay**: Replay historical events from files
- ✅ **Real-time Streaming**: Events flow through SSE to frontend
- ✅ **Frontend Controls**: Demo panel with start/stop/replay

## Quick Start

### Start Simulator via API

```bash
curl -X POST http://localhost:8000/sim/start \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "normal_day",
    "rate_per_min": 20,
    "seed": 42
  }'
```

### Check Status

```bash
curl http://localhost:8000/sim/status
```

### Stop Simulator

```bash
curl -X POST http://localhost:8000/sim/stop
```

### Replay Events

```bash
curl -X POST http://localhost:8000/sim/replay \
  -H "Content-Type: application/json" \
  -d '{
    "jsonl_data": "{\"event_id\":\"evt_001\",...}\n{\"event_id\":\"evt_002\",...}"
  }'
```

## Architecture

### Components

1. **`event_simulator.py`**: Core event generation logic
   - Generates schema-valid CameraEvent objects
   - Supports 7 event types with realistic metadata
   - Deterministic seeding via dedicated Random instance
   - Built-in validation

2. **`simulator_manager.py`**: Lifecycle management
   - Singleton pattern (one simulator at a time)
   - Async event generation loop
   - Rate control
   - Statistics tracking

3. **API Endpoints** (in `alibi_api.py`):
   - `POST /sim/start`
   - `POST /sim/stop`
   - `GET /sim/status`
   - `POST /sim/replay`

4. **Frontend** (in `console/src/`):
   - `DemoPanel.tsx`: Control panel component
   - Enhanced incident detail with Replay Timeline

## Event Types

### person_detected
Basic person detection event.

**Metadata**: `person_count`, `direction`

### vehicle_detected
Vehicle detection event.

**Metadata**: `vehicle_type`, `speed_estimate`

### loitering
Person remaining in area for extended duration.

**Metadata**: `duration_seconds`, `person_count`, `behavior`

### perimeter_breach
Unauthorized access to restricted perimeter (after-hours).

**Metadata**: `breach_type`, `after_hours`, `direction`

**Note**: Only generated at perimeter cameras.

### crowd_anomaly
Unusual crowd density or people count spike.

**Metadata**: `people_count`, `density`, `anomaly_type`, `baseline_count`

### aggression_proxy
Rapid motion and clustering suggesting confrontation.

**Metadata**: `motion_intensity`, `rapid_motion`, `clustering`, `person_count`, `behavior`

### vehicle_stop_restricted
Vehicle stopped in restricted zone.

**Metadata**: `vehicle_type`, `stopped_duration_seconds`, `restricted_zone`, `license_plate_visible`

**Note**: Only generated at restricted/parking zones.

## Scenarios

### quiet_shift
Low activity, mostly routine detections.
- 60% person_detected
- 30% vehicle_detected
- 8% loitering
- 1% perimeter_breach
- 1% aggression_proxy

### normal_day
Typical daytime activity.
- 50% person_detected
- 25% vehicle_detected
- 15% loitering
- 2% perimeter_breach
- 3% crowd_anomaly
- 3% aggression_proxy
- 2% vehicle_stop_restricted

### busy_evening
High activity with more incidents.
- 40% person_detected
- 20% vehicle_detected
- 20% loitering
- 5% perimeter_breach
- 10% crowd_anomaly
- 3% aggression_proxy
- 2% vehicle_stop_restricted

### security_incident
High-severity event scenario.
- 20% person_detected
- 10% vehicle_detected
- 10% loitering
- 30% perimeter_breach
- 5% crowd_anomaly
- 20% aggression_proxy
- 5% vehicle_stop_restricted

### mixed_events
Balanced distribution across all types.

## Usage Examples

### Python API

```python
from alibi.sim.event_simulator import EventSimulator, Scenario, SimulatorConfig

# Create simulator
config = SimulatorConfig(
    scenario=Scenario.NORMAL_DAY,
    rate_per_min=20.0,
    seed=42  # Optional: for deterministic replay
)

sim = EventSimulator(config)

# Generate event
event = sim.generate_event()

# Validate
is_valid, error = sim.validate_event(event)
if not is_valid:
    print(f"Invalid event: {error}")

# Get statistics
stats = sim.get_stats()
print(f"Generated {stats['events_generated']} events")
```

### Async Manager

```python
from alibi.sim.simulator_manager import get_simulator_manager
from alibi.sim.event_simulator import Scenario

async def event_callback(event):
    # Process event
    print(f"Event: {event['event_type']}")

manager = get_simulator_manager()

# Start
await manager.start(
    scenario=Scenario.SECURITY_INCIDENT,
    rate_per_min=30.0,
    seed=999,
    event_callback=event_callback
)

# Check status
status = manager.get_status()

# Stop
await manager.stop()
```

## Testing

### Run Unit Tests

```bash
python test_simulator.py
```

**Coverage**:
- Basic event generation
- Deterministic seeding
- Scenario distributions
- All event types
- Validation
- Statistics

### Run API Tests

```bash
./test_simulator_api.sh
```

**Coverage**:
- Start/stop simulator
- Status polling
- Incident creation
- JSONL replay
- Error handling

### Integration Verification

```bash
python verify_simulator_integration.py
```

## Validation Rules

All events must pass validation:

- `event_id`: Required string
- `camera_id`: Required string
- `zone_id`: Required string
- `event_type`: Required string
- `confidence`: 0.0-1.0 (float)
- `severity`: 1-5 (int)
- `ts`: Valid ISO 8601 timestamp
- `clip_url`: Optional string
- `snapshot_url`: Optional string
- `metadata`: Optional dict

**Invalid events are rejected and logged, NOT silently fixed.**

## Frontend Integration

### Demo Panel

Located on `/incidents` page (right edge).

**Controls**:
- Scenario dropdown
- Rate slider (1-60 events/min)
- Seed input (optional)
- Start/Stop buttons
- Replay textarea (paste JSONL)

**Status Display**:
- Running indicator
- Events generated counter
- Incidents created counter
- Current rate
- Scenario name
- Seed (if set)

### Replay Timeline

Located on `/incidents/:id` detail page.

**Features**:
- Ordered events with timestamps
- Event metadata (expandable)
- Evidence links (clip, snapshot)
- Camera and zone info
- Confidence and severity

## Performance

- **Generation overhead**: ~1ms per event
- **Rate accuracy**: ±2% of target
- **Memory footprint**: <10MB
- **Concurrency**: Single simulator (singleton)
- **SSE latency**: <100ms to frontend

## Limitations

1. **Single simulator**: Only one can run at a time
2. **Synthetic evidence**: URLs point to example.com
3. **No time travel**: Replay uses current timestamps
4. **Fixed cameras**: 8 cameras hardcoded
5. **No multi-tenancy**: Shared camera namespace

## Troubleshooting

### Simulator Won't Start

**Error**: "Simulator already running"

**Solution**:
```bash
curl -X POST http://localhost:8000/sim/stop
```

### No Incidents Appearing

**Check status**:
```bash
curl http://localhost:8000/sim/status
```

Verify `events_generated` is increasing.

### Invalid Event Errors

Check API logs for validation errors. Common issues:
- Confidence not in 0.0-1.0 range
- Severity not in 1-5 range
- Invalid timestamp format
- Missing required fields

## Documentation

- **[SIMULATOR_COMPLETE.md](../../SIMULATOR_COMPLETE.md)**: Full technical documentation
- **[SIMULATOR_QUICKSTART.md](../../SIMULATOR_QUICKSTART.md)**: 5-minute quick start
- **[SIMULATOR_IMPLEMENTATION_SUMMARY.md](../../SIMULATOR_IMPLEMENTATION_SUMMARY.md)**: Implementation details

## API Reference

See FastAPI docs at `http://localhost:8000/docs` for interactive API documentation.

## Support

For issues or questions:
1. Check API docs: http://localhost:8000/docs
2. Review logs in terminal
3. Run verification: `python verify_simulator_integration.py`
4. Run tests: `python test_simulator.py`
