#!/usr/bin/env python3
"""
Quick integration verification for Alibi Simulator

Verifies:
1. Simulator can be imported
2. Events can be generated
3. Events are schema-valid
4. Deterministic seeding works
"""

import sys
from datetime import datetime

# Test imports
try:
    from alibi.sim.event_simulator import EventSimulator, Scenario, SimulatorConfig
    from alibi.sim.simulator_manager import SimulatorManager, get_simulator_manager
    from alibi.schemas import CameraEvent
    print("✅ All simulator modules imported successfully")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test event generation
try:
    config = SimulatorConfig(
        scenario=Scenario.NORMAL_DAY,
        rate_per_min=10.0,
        seed=42
    )
    sim = EventSimulator(config)
    
    event = sim.generate_event()
    is_valid, error = sim.validate_event(event)
    
    if not is_valid:
        print(f"❌ Generated invalid event: {error}")
        sys.exit(1)
    
    print(f"✅ Generated valid event: {event['event_type']} @ {event['camera_id']}")
except Exception as e:
    print(f"❌ Event generation failed: {e}")
    sys.exit(1)

# Test CameraEvent schema compatibility
try:
    camera_event = CameraEvent(
        event_id=event['event_id'],
        camera_id=event['camera_id'],
        ts=datetime.fromisoformat(event['ts']),
        zone_id=event['zone_id'],
        event_type=event['event_type'],
        confidence=event['confidence'],
        severity=event['severity'],
        clip_url=event.get('clip_url'),
        snapshot_url=event.get('snapshot_url'),
        metadata=event.get('metadata', {}),
    )
    print(f"✅ Event compatible with CameraEvent schema")
except Exception as e:
    print(f"❌ Schema compatibility failed: {e}")
    sys.exit(1)

# Test deterministic seeding
try:
    config1 = SimulatorConfig(scenario=Scenario.NORMAL_DAY, rate_per_min=10.0, seed=999)
    config2 = SimulatorConfig(scenario=Scenario.NORMAL_DAY, rate_per_min=10.0, seed=999)
    
    sim1 = EventSimulator(config1)
    sim2 = EventSimulator(config2)
    
    events1 = [sim1.generate_event()['event_type'] for _ in range(5)]
    events2 = [sim2.generate_event()['event_type'] for _ in range(5)]
    
    if events1 == events2:
        print(f"✅ Deterministic seeding works: {events1}")
    else:
        print(f"❌ Seeding not deterministic: {events1} vs {events2}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Deterministic seeding test failed: {e}")
    sys.exit(1)

# Test all event types
try:
    config = SimulatorConfig(scenario=Scenario.MIXED_EVENTS, rate_per_min=10.0, seed=123)
    sim = EventSimulator(config)
    
    event_types = set()
    for _ in range(50):
        event = sim.generate_event()
        event_types.add(event['event_type'])
    
    expected_types = {
        'person_detected', 'vehicle_detected', 'loitering',
        'perimeter_breach', 'crowd_anomaly', 'aggression_proxy',
        'vehicle_stop_restricted'
    }
    
    if len(event_types) >= 5:  # Should see most types in 50 events
        print(f"✅ Generated {len(event_types)} event types: {sorted(event_types)}")
    else:
        print(f"⚠️  Only saw {len(event_types)} event types (expected 5+)")
except Exception as e:
    print(f"❌ Event type diversity test failed: {e}")
    sys.exit(1)

# Test simulator manager
try:
    manager = get_simulator_manager()
    status = manager.get_status()
    
    if not status['running']:
        print(f"✅ Simulator manager initialized (not running)")
    else:
        print(f"⚠️  Simulator manager shows running (unexpected)")
except Exception as e:
    print(f"❌ Simulator manager test failed: {e}")
    sys.exit(1)

# Test validation catches errors
try:
    bad_event = {
        "event_id": "test",
        "camera_id": "cam_test",
        "ts": "2026-01-18T12:00:00",
        "zone_id": "zone_test",
        "event_type": "person_detected",
        "confidence": 1.5,  # Invalid
        "severity": 3,
    }
    
    is_valid, error = sim.validate_event(bad_event)
    if not is_valid and "confidence" in error.lower():
        print(f"✅ Validation correctly rejects invalid events")
    else:
        print(f"❌ Validation should have caught invalid confidence")
        sys.exit(1)
except Exception as e:
    print(f"❌ Validation test failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ All integration checks passed!")
print("="*60)
print("\nSimulator is ready for:")
print("  • API integration (python -m alibi.alibi_api)")
print("  • Frontend demo panel")
print("  • Event replay")
print("  • Testing workflows")
