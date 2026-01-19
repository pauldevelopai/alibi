#!/usr/bin/env python3
"""
Test script for Alibi event simulator

Verifies:
1. Event generation with different scenarios
2. Schema validation
3. Deterministic seeding
4. Event type distributions
"""

from alibi.sim.event_simulator import EventSimulator, Scenario, SimulatorConfig


def test_basic_generation():
    """Test basic event generation"""
    print("Test 1: Basic event generation")
    
    config = SimulatorConfig(
        scenario=Scenario.NORMAL_DAY,
        rate_per_min=10.0,
        seed=42
    )
    
    sim = EventSimulator(config)
    
    # Generate 5 events
    events = []
    for i in range(5):
        event = sim.generate_event()
        events.append(event)
        
        # Validate
        is_valid, error = sim.validate_event(event)
        assert is_valid, f"Event {i+1} invalid: {error}"
        
        print(f"  ✓ Event {i+1}: {event['event_type']} @ {event['camera_id']}")
    
    print(f"  ✓ Generated {len(events)} valid events\n")
    return events


def test_deterministic_seeding():
    """Test that same seed produces same events"""
    print("Test 2: Deterministic seeding")
    
    config1 = SimulatorConfig(
        scenario=Scenario.NORMAL_DAY,
        rate_per_min=10.0,
        seed=123
    )
    
    config2 = SimulatorConfig(
        scenario=Scenario.NORMAL_DAY,
        rate_per_min=10.0,
        seed=123
    )
    
    sim1 = EventSimulator(config1)
    sim2 = EventSimulator(config2)
    
    # Generate 3 events from each
    for i in range(3):
        event1 = sim1.generate_event()
        event2 = sim2.generate_event()
        
        # Event types should match
        assert event1['event_type'] == event2['event_type'], \
            f"Event {i+1} types don't match: {event1['event_type']} vs {event2['event_type']}"
        
        print(f"  ✓ Event {i+1}: {event1['event_type']} (deterministic)")
    
    print("  ✓ Seeding is deterministic\n")


def test_scenario_distributions():
    """Test event type distributions for scenarios"""
    print("Test 3: Scenario distributions")
    
    scenarios = [
        Scenario.QUIET_SHIFT,
        Scenario.SECURITY_INCIDENT,
    ]
    
    for scenario in scenarios:
        config = SimulatorConfig(
            scenario=scenario,
            rate_per_min=10.0,
            seed=42
        )
        
        sim = EventSimulator(config)
        
        # Generate 20 events
        event_types = {}
        for _ in range(20):
            event = sim.generate_event()
            event_type = event['event_type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        print(f"  {scenario.value}:")
        for event_type, count in sorted(event_types.items()):
            print(f"    - {event_type}: {count}")
        print()


def test_event_types():
    """Test all event types can be generated"""
    print("Test 4: All event types")
    
    config = SimulatorConfig(
        scenario=Scenario.MIXED_EVENTS,
        rate_per_min=10.0,
        seed=999
    )
    
    sim = EventSimulator(config)
    
    # Generate many events to hit all types
    event_types_seen = set()
    for _ in range(100):
        event = sim.generate_event()
        event_types_seen.add(event['event_type'])
        
        # Validate
        is_valid, error = sim.validate_event(event)
        assert is_valid, f"Invalid event: {error}"
    
    print(f"  ✓ Saw {len(event_types_seen)} event types:")
    for event_type in sorted(event_types_seen):
        print(f"    - {event_type}")
    print()


def test_validation_catches_errors():
    """Test validation catches schema violations"""
    print("Test 5: Validation catches errors")
    
    config = SimulatorConfig(
        scenario=Scenario.NORMAL_DAY,
        rate_per_min=10.0,
    )
    
    sim = EventSimulator(config)
    
    # Test invalid confidence
    bad_event = {
        "event_id": "test_001",
        "camera_id": "cam_test",
        "ts": "2026-01-18T12:00:00",
        "zone_id": "zone_test",
        "event_type": "person_detected",
        "confidence": 1.5,  # Invalid: > 1.0
        "severity": 3,
    }
    
    is_valid, error = sim.validate_event(bad_event)
    assert not is_valid, "Should catch confidence > 1.0"
    assert "confidence" in error.lower()
    print(f"  ✓ Caught invalid confidence: {error}")
    
    # Test invalid severity
    bad_event["confidence"] = 0.8
    bad_event["severity"] = 10  # Invalid: > 5
    
    is_valid, error = sim.validate_event(bad_event)
    assert not is_valid, "Should catch severity > 5"
    assert "severity" in error.lower()
    print(f"  ✓ Caught invalid severity: {error}")
    
    print()


def test_stats():
    """Test simulator statistics"""
    print("Test 6: Simulator statistics")
    
    config = SimulatorConfig(
        scenario=Scenario.NORMAL_DAY,
        rate_per_min=60.0,
        seed=42
    )
    
    sim = EventSimulator(config)
    
    # Generate some events
    for _ in range(10):
        sim.generate_event()
    
    stats = sim.get_stats()
    
    assert stats['events_generated'] == 10
    assert stats['scenario'] == 'normal_day'
    assert stats['seed'] == 42
    assert stats['rate_target'] == 60.0
    
    print(f"  ✓ Events generated: {stats['events_generated']}")
    print(f"  ✓ Scenario: {stats['scenario']}")
    print(f"  ✓ Seed: {stats['seed']}")
    print(f"  ✓ Rate target: {stats['rate_target']}/min")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Alibi Event Simulator Tests")
    print("=" * 60)
    print()
    
    test_basic_generation()
    test_deterministic_seeding()
    test_scenario_distributions()
    test_event_types()
    test_validation_catches_errors()
    test_stats()
    
    print("=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
