#!/usr/bin/env python3
"""
Alibi Demo Script

Demonstrates the full incident processing pipeline with various scenarios.
"""

from datetime import datetime, timedelta

from alibi import (
    CameraEvent,
    Incident,
    IncidentStatus,
    build_incident_plan,
    validate_incident_plan,
    compile_alert,
    compile_shift_report,
    Decision,
)
from alibi.config import AlibiConfig
from alibi.alibi_engine import log_incident_processing


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_scenario_1_normal_detection():
    """Scenario 1: Normal detection with good confidence"""
    print_section("Scenario 1: Normal Detection (Medium Severity, Good Confidence)")
    
    event = CameraEvent(
        event_id="evt_001",
        camera_id="cam_north_entrance",
        ts=datetime.utcnow(),
        zone_id="zone_lobby",
        event_type="person_detected",
        confidence=0.85,
        severity=3,
        clip_url="https://storage.example.com/clips/evt_001.mp4",
        snapshot_url="https://storage.example.com/snapshots/evt_001.jpg",
        metadata={},
    )
    
    incident = Incident(
        incident_id="inc_001",
        status=IncidentStatus.NEW,
        created_ts=datetime.utcnow(),
        updated_ts=datetime.utcnow(),
        events=[event],
    )
    
    plan = build_incident_plan(incident)
    validation = validate_incident_plan(plan, incident)
    
    print(f"\n📊 Incident Plan:")
    print(f"   Summary: {plan.summary_1line}")
    print(f"   Severity: {plan.severity}/5")
    print(f"   Confidence: {plan.confidence:.2f}")
    print(f"   Recommended Action: {plan.recommended_next_step.value}")
    print(f"   Requires Approval: {plan.requires_human_approval}")
    
    print(f"\n✓ Validation: {'PASSED' if validation.passed else 'FAILED'}")
    if validation.warnings:
        for warning in validation.warnings:
            print(f"   ⚠️  {warning}")
    
    if validation.passed:
        alert = compile_alert(plan, incident)
        print(f"\n📢 Alert Message:")
        print(f"   Title: {alert.title}")
        print(f"   Body: {alert.body}")
        print(f"   Actions: {', '.join(alert.operator_actions)}")
        
        # Log the processing
        log_incident_processing(incident, plan, validation, alert)
        print(f"\n✓ Logged to alibi/data/incident_processing.jsonl")


def demo_scenario_2_low_confidence():
    """Scenario 2: Low confidence detection"""
    print_section("Scenario 2: Low Confidence Detection (Monitor Only)")
    
    event = CameraEvent(
        event_id="evt_002",
        camera_id="cam_parking_lot",
        ts=datetime.utcnow(),
        zone_id="zone_parking",
        event_type="vehicle_detected",
        confidence=0.65,  # Below threshold
        severity=3,
        clip_url="https://storage.example.com/clips/evt_002.mp4",
        snapshot_url="https://storage.example.com/snapshots/evt_002.jpg",
        metadata={},
    )
    
    incident = Incident(
        incident_id="inc_002",
        status=IncidentStatus.NEW,
        created_ts=datetime.utcnow(),
        updated_ts=datetime.utcnow(),
        events=[event],
    )
    
    plan = build_incident_plan(incident)
    validation = validate_incident_plan(plan, incident)
    
    print(f"\n📊 Incident Plan:")
    print(f"   Summary: {plan.summary_1line}")
    print(f"   Confidence: {plan.confidence:.2f} (BELOW THRESHOLD)")
    print(f"   Recommended Action: {plan.recommended_next_step.value}")
    print(f"   Risk Flags: {', '.join(plan.action_risk_flags)}")
    
    print(f"\n✓ Validation: {'PASSED' if validation.passed else 'FAILED'}")
    print(f"   → System correctly recommends 'monitor' for low confidence")


def demo_scenario_3_high_severity():
    """Scenario 3: High severity requiring human approval"""
    print_section("Scenario 3: High Severity (Human Approval Required)")
    
    event = CameraEvent(
        event_id="evt_003",
        camera_id="cam_restricted_area",
        ts=datetime.utcnow(),
        zone_id="zone_restricted",
        event_type="unauthorized_access",
        confidence=0.90,
        severity=5,  # High severity
        clip_url="https://storage.example.com/clips/evt_003.mp4",
        snapshot_url="https://storage.example.com/snapshots/evt_003.jpg",
        metadata={},
    )
    
    incident = Incident(
        incident_id="inc_003",
        status=IncidentStatus.NEW,
        created_ts=datetime.utcnow(),
        updated_ts=datetime.utcnow(),
        events=[event],
    )
    
    plan = build_incident_plan(incident)
    validation = validate_incident_plan(plan, incident)
    
    print(f"\n📊 Incident Plan:")
    print(f"   Summary: {plan.summary_1line}")
    print(f"   Severity: {plan.severity}/5 (HIGH)")
    print(f"   Confidence: {plan.confidence:.2f}")
    print(f"   Recommended Action: {plan.recommended_next_step.value}")
    print(f"   Requires Approval: {plan.requires_human_approval} ⚠️")
    print(f"   Risk Flags: {', '.join(plan.action_risk_flags)}")
    
    if validation.passed:
        alert = compile_alert(plan, incident)
        print(f"\n📢 Alert Message:")
        print(f"   Title: {alert.title}")
        if alert.disclaimer:
            print(f"   Disclaimer: {alert.disclaimer}")


def demo_scenario_4_watchlist_match():
    """Scenario 4: Watchlist match"""
    print_section("Scenario 4: Watchlist Match (Human Review Required)")
    
    event = CameraEvent(
        event_id="evt_004",
        camera_id="cam_main_entrance",
        ts=datetime.utcnow(),
        zone_id="zone_entrance",
        event_type="person_detected",
        confidence=0.82,
        severity=3,
        clip_url="https://storage.example.com/clips/evt_004.mp4",
        snapshot_url="https://storage.example.com/snapshots/evt_004.jpg",
        metadata={"watchlist_match": True},  # Watchlist match!
    )
    
    incident = Incident(
        incident_id="inc_004",
        status=IncidentStatus.NEW,
        created_ts=datetime.utcnow(),
        updated_ts=datetime.utcnow(),
        events=[event],
    )
    
    plan = build_incident_plan(incident)
    validation = validate_incident_plan(plan, incident)
    
    print(f"\n📊 Incident Plan:")
    print(f"   Summary: {plan.summary_1line}")
    print(f"   Watchlist Match: YES ⚠️")
    print(f"   Recommended Action: {plan.recommended_next_step.value}")
    print(f"   Requires Approval: {plan.requires_human_approval}")
    print(f"   Risk Flags: {', '.join(plan.action_risk_flags)}")
    
    if validation.passed:
        alert = compile_alert(plan, incident)
        print(f"\n📢 Alert Message:")
        print(f"   Title: {alert.title}")
        print(f"   Disclaimer: {alert.disclaimer}")


def demo_scenario_5_validation_failure():
    """Scenario 5: Validation failure (accusatory language)"""
    print_section("Scenario 5: Validation Failure (Forbidden Language)")
    
    from alibi.schemas import IncidentPlan, RecommendedAction
    
    # Manually create a plan with forbidden language
    incident = Incident(
        incident_id="inc_005",
        status=IncidentStatus.NEW,
        created_ts=datetime.utcnow(),
        updated_ts=datetime.utcnow(),
        events=[],
    )
    
    bad_plan = IncidentPlan(
        incident_id="inc_005",
        summary_1line="Suspect detected breaking into building",  # FORBIDDEN!
        severity=3,
        confidence=0.85,
        uncertainty_notes="None",
        recommended_next_step=RecommendedAction.NOTIFY,
        requires_human_approval=False,
        evidence_refs=["https://storage.example.com/clips/evt_005.mp4"],
    )
    
    validation = validate_incident_plan(bad_plan, incident)
    
    print(f"\n📊 Incident Plan:")
    print(f"   Summary: {bad_plan.summary_1line}")
    
    print(f"\n❌ Validation: FAILED")
    print(f"   Violations:")
    for violation in validation.violations:
        print(f"      • {violation}")
    
    print(f"\n   → System prevents output with accusatory language")


def demo_scenario_6_shift_report():
    """Scenario 6: Generate shift report"""
    print_section("Scenario 6: Shift Report Generation")
    
    # Create some sample incidents
    incidents = []
    decisions = []
    
    start_ts = datetime.utcnow() - timedelta(hours=8)
    
    for i in range(5):
        event = CameraEvent(
            event_id=f"evt_{i+10}",
            camera_id=f"cam_0{i+1}",
            ts=start_ts + timedelta(hours=i),
            zone_id="zone_main",
            event_type="person_detected",
            confidence=0.75 + (i * 0.05),
            severity=2 + (i % 3),
            clip_url=f"https://storage.example.com/clips/evt_{i+10}.mp4",
        )
        
        incident = Incident(
            incident_id=f"inc_{i+10}",
            status=IncidentStatus.CLOSED,
            created_ts=start_ts + timedelta(hours=i),
            updated_ts=start_ts + timedelta(hours=i, minutes=30),
            events=[event],
        )
        incidents.append(incident)
        
        # Create decision
        decision = Decision(
            incident_id=incident.incident_id,
            decision_ts=incident.updated_ts,
            action_taken="dismissed" if i % 2 == 0 else "escalated",
            operator_notes=f"Reviewed incident {i+10}",
            was_true_positive=(i % 2 == 1),
        )
        decisions.append(decision)
    
    end_ts = datetime.utcnow()
    
    report = compile_shift_report(incidents, decisions, start_ts, end_ts)
    
    print(f"\n📋 Shift Report:")
    print(f"   Period: {start_ts.strftime('%H:%M')} - {end_ts.strftime('%H:%M')}")
    print(f"   Total Incidents: {report.total_incidents}")
    print(f"   Precision: {report.kpis['precision']:.1%}")
    print(f"   True Positives: {report.kpis['true_positives']}")
    print(f"   False Positives: {report.kpis['false_positives']}")
    print(f"\n   Severity Breakdown:")
    for sev, count in sorted(report.by_severity.items()):
        print(f"      Level {sev}: {count} incidents")
    print(f"\n   Narrative:")
    for line in report.narrative.split('\n'):
        if line.strip():
            print(f"      {line}")


def main():
    """Run all demo scenarios"""
    print("\n" + "🔒" * 35)
    print("   ALIBI - AI-Assisted Incident Alert Management")
    print("   Demo: Hard Safety Rules in Action")
    print("🔒" * 35)
    
    demo_scenario_1_normal_detection()
    demo_scenario_2_low_confidence()
    demo_scenario_3_high_severity()
    demo_scenario_4_watchlist_match()
    demo_scenario_5_validation_failure()
    demo_scenario_6_shift_report()
    
    print_section("Demo Complete")
    print("\nKey Takeaways:")
    print("  ✓ Low confidence → automatic 'monitor' recommendation")
    print("  ✓ High severity → requires human approval")
    print("  ✓ Watchlist match → requires human review")
    print("  ✓ Forbidden language → validation fails")
    print("  ✓ All processing logged to JSONL")
    print("\nSee alibi/README.md for full documentation.")
    print()


if __name__ == "__main__":
    main()
