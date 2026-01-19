#!/usr/bin/env python3
"""
Simple Alibi Example

Minimal example showing the core workflow.
"""

from datetime import datetime

from alibi import (
    CameraEvent,
    Incident,
    IncidentStatus,
    build_incident_plan,
    validate_incident_plan,
    compile_alert,
)


def main():
    # 1. Create a camera event
    event = CameraEvent(
        event_id="evt_001",
        camera_id="cam_entrance",
        ts=datetime.utcnow(),
        zone_id="zone_main",
        event_type="person_detected",
        confidence=0.85,
        severity=3,
        clip_url="https://storage.example.com/clips/evt_001.mp4",
        snapshot_url="https://storage.example.com/snapshots/evt_001.jpg",
        metadata={},
    )
    
    # 2. Create an incident
    incident = Incident(
        incident_id="inc_001",
        status=IncidentStatus.NEW,
        created_ts=datetime.utcnow(),
        updated_ts=datetime.utcnow(),
        events=[event],
    )
    
    # 3. Build incident plan
    plan = build_incident_plan(incident)
    
    print(f"Incident: {incident.incident_id}")
    print(f"Summary: {plan.summary_1line}")
    print(f"Severity: {plan.severity}/5")
    print(f"Confidence: {plan.confidence:.2f}")
    print(f"Recommended Action: {plan.recommended_next_step.value}")
    print(f"Requires Approval: {plan.requires_human_approval}")
    
    # 4. Validate plan
    validation = validate_incident_plan(plan, incident)
    
    if not validation.passed:
        print("\n❌ Validation FAILED:")
        for violation in validation.violations:
            print(f"  - {violation}")
        return
    
    print("\n✓ Validation passed")
    
    # 5. Compile alert
    alert = compile_alert(plan, incident)
    
    print(f"\nAlert Title: {alert.title}")
    print(f"Alert Body:\n{alert.body}")
    
    if alert.disclaimer:
        print(f"\nDisclaimer: {alert.disclaimer}")
    
    print(f"\nOperator Actions:")
    for action in alert.operator_actions:
        print(f"  - {action}")


if __name__ == "__main__":
    main()
