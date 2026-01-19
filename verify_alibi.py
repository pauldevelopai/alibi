#!/usr/bin/env python3
"""
Alibi Verification Script

Quick verification that all core components are working.
"""

import sys
from datetime import datetime

print("🔒 Alibi System Verification\n")

# Test 1: Import all core components
print("1. Testing imports...")
try:
    from alibi import (
        CameraEvent,
        Incident,
        IncidentPlan,
        AlertMessage,
        ShiftReport,
        ValidationResult,
        Decision,
        IncidentStatus,
        RecommendedAction,
        build_incident_plan,
        validate_incident_plan,
        compile_alert,
        compile_shift_report,
    )
    print("   ✅ All imports successful")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Create basic incident
print("\n2. Testing incident creation...")
try:
    event = CameraEvent(
        event_id="test_001",
        camera_id="cam_test",
        ts=datetime.utcnow(),
        zone_id="zone_test",
        event_type="person_detected",
        confidence=0.85,
        severity=3,
        clip_url="https://example.com/clip.mp4",
    )
    
    incident = Incident(
        incident_id="inc_test",
        status=IncidentStatus.NEW,
        created_ts=datetime.utcnow(),
        updated_ts=datetime.utcnow(),
        events=[event],
    )
    print("   ✅ Incident created successfully")
except Exception as e:
    print(f"   ❌ Incident creation failed: {e}")
    sys.exit(1)

# Test 3: Build plan
print("\n3. Testing plan generation...")
try:
    plan = build_incident_plan(incident)
    assert plan.incident_id == incident.incident_id
    assert plan.severity == 3
    assert plan.confidence == 0.85
    print(f"   ✅ Plan generated: {plan.recommended_next_step.value}")
except Exception as e:
    print(f"   ❌ Plan generation failed: {e}")
    sys.exit(1)

# Test 4: Validate plan
print("\n4. Testing validation...")
try:
    validation = validate_incident_plan(plan, incident)
    assert validation.passed
    print(f"   ✅ Validation passed (status: {validation.status.value})")
except Exception as e:
    print(f"   ❌ Validation failed: {e}")
    sys.exit(1)

# Test 5: Compile alert
print("\n5. Testing alert compilation...")
try:
    alert = compile_alert(plan, incident)
    assert alert.incident_id == incident.incident_id
    assert alert.title
    assert alert.body
    print(f"   ✅ Alert compiled: {alert.title[:50]}...")
except Exception as e:
    print(f"   ❌ Alert compilation failed: {e}")
    sys.exit(1)

# Test 6: Test forbidden language detection
print("\n6. Testing safety rules...")
try:
    from alibi.validator import contains_forbidden_language
    
    assert contains_forbidden_language("The suspect was seen")
    assert contains_forbidden_language("Criminal activity detected")
    assert not contains_forbidden_language("Possible unauthorized access")
    print("   ✅ Forbidden language detection working")
except Exception as e:
    print(f"   ❌ Safety rules test failed: {e}")
    sys.exit(1)

# Test 7: Test low confidence handling
print("\n7. Testing low confidence rule...")
try:
    low_conf_event = CameraEvent(
        event_id="test_002",
        camera_id="cam_test",
        ts=datetime.utcnow(),
        zone_id="zone_test",
        event_type="person_detected",
        confidence=0.60,  # Below threshold
        severity=3,
    )
    
    low_conf_incident = Incident(
        incident_id="inc_test_2",
        status=IncidentStatus.NEW,
        created_ts=datetime.utcnow(),
        updated_ts=datetime.utcnow(),
        events=[low_conf_event],
    )
    
    low_conf_plan = build_incident_plan(low_conf_incident)
    assert low_conf_plan.recommended_next_step == RecommendedAction.MONITOR
    print("   ✅ Low confidence → monitor (correct)")
except Exception as e:
    print(f"   ❌ Low confidence test failed: {e}")
    sys.exit(1)

# Test 8: Test high severity handling
print("\n8. Testing high severity rule...")
try:
    high_sev_event = CameraEvent(
        event_id="test_003",
        camera_id="cam_test",
        ts=datetime.utcnow(),
        zone_id="zone_test",
        event_type="unauthorized_access",
        confidence=0.90,
        severity=5,  # High severity
        clip_url="https://example.com/clip.mp4",
    )
    
    high_sev_incident = Incident(
        incident_id="inc_test_3",
        status=IncidentStatus.NEW,
        created_ts=datetime.utcnow(),
        updated_ts=datetime.utcnow(),
        events=[high_sev_event],
    )
    
    high_sev_plan = build_incident_plan(high_sev_incident)
    assert high_sev_plan.requires_human_approval is True
    assert high_sev_plan.recommended_next_step == RecommendedAction.DISPATCH_PENDING_REVIEW
    print("   ✅ High severity → human approval required (correct)")
except Exception as e:
    print(f"   ❌ High severity test failed: {e}")
    sys.exit(1)

# Test 9: Test watchlist handling
print("\n9. Testing watchlist match rule...")
try:
    watchlist_event = CameraEvent(
        event_id="test_004",
        camera_id="cam_test",
        ts=datetime.utcnow(),
        zone_id="zone_test",
        event_type="person_detected",
        confidence=0.85,
        severity=3,
        clip_url="https://example.com/clip.mp4",
        metadata={"watchlist_match": True},
    )
    
    watchlist_incident = Incident(
        incident_id="inc_test_4",
        status=IncidentStatus.NEW,
        created_ts=datetime.utcnow(),
        updated_ts=datetime.utcnow(),
        events=[watchlist_event],
    )
    
    watchlist_plan = build_incident_plan(watchlist_incident)
    assert watchlist_plan.requires_human_approval is True
    assert watchlist_plan.recommended_next_step == RecommendedAction.DISPATCH_PENDING_REVIEW
    print("   ✅ Watchlist match → human approval required (correct)")
except Exception as e:
    print(f"   ❌ Watchlist test failed: {e}")
    sys.exit(1)

# Test 10: Test logging
print("\n10. Testing logging...")
try:
    from alibi.alibi_engine import log_incident_processing
    from pathlib import Path
    
    log_incident_processing(incident, plan, validation, alert)
    
    log_file = Path("alibi/data/incident_processing.jsonl")
    assert log_file.exists()
    print("   ✅ Logging working (check alibi/data/incident_processing.jsonl)")
except Exception as e:
    print(f"   ❌ Logging test failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL VERIFICATION TESTS PASSED")
print("="*60)
print("\nAlibi system is fully operational!")
print("\nNext steps:")
print("  • Run demo: PYTHONPATH=. python alibi/demo.py")
print("  • Run tests: pytest tests/test_alibi_engine_validation.py -v")
print("  • Read docs: cat alibi/README.md")
print()
