"""
Tests for Plate-Vehicle Mismatch Detection

Tests mismatch logic, conservative triggering, and validation rules.
"""

import pytest
import numpy as np
import cv2
import tempfile
from pathlib import Path
from datetime import datetime

from alibi.vehicles.plate_registry import PlateRegistryStore, PlateRegistryEntry
from alibi.vehicles.mismatch import (
    normalize_make_model,
    compute_mismatch_score,
    check_mismatch,
    MismatchResult
)
from alibi.validator import validate_incident_plan
from alibi.schemas import (
    Incident,
    IncidentPlan,
    CameraEvent,
    IncidentStatus,
    RecommendedAction,
    ValidationStatus
)


class TestPlateRegistryStore:
    """Test plate registry storage"""
    
    def test_create_and_load_entry(self, tmp_path):
        """Test creating and loading registry entries"""
        store_path = tmp_path / "registry.jsonl"
        store = PlateRegistryStore(str(store_path))
        
        # Create entry
        entry = PlateRegistryEntry(
            plate="N12345W",
            expected_make="Mazda",
            expected_model="Demio",
            source_ref="DMV_2024",
            added_ts=datetime.utcnow().isoformat()
        )
        
        # Add to store
        store.add_entry(entry)
        
        # Load back
        entries = store.load_all()
        assert len(entries) == 1
        assert entries[0].plate == "N12345W"
        assert entries[0].expected_make == "Mazda"
        assert entries[0].expected_model == "Demio"
    
    def test_get_by_plate(self, tmp_path):
        """Test looking up by plate"""
        store_path = tmp_path / "registry.jsonl"
        store = PlateRegistryStore(str(store_path))
        
        # Add entry
        entry = PlateRegistryEntry(
            plate="N12345W",
            expected_make="Mazda",
            expected_model="Demio",
            source_ref="DMV_2024",
            added_ts=datetime.utcnow().isoformat()
        )
        store.add_entry(entry)
        
        # Lookup
        found = store.get_by_plate("N12345W")
        assert found is not None
        assert found.expected_make == "Mazda"
        
        # Not found
        not_found = store.get_by_plate("NOTEXIST")
        assert not_found is None
    
    def test_is_registered(self, tmp_path):
        """Test checking if plate is registered"""
        store_path = tmp_path / "registry.jsonl"
        store = PlateRegistryStore(str(store_path))
        
        # Add entry
        entry = PlateRegistryEntry(
            plate="N12345W",
            expected_make="Mazda",
            expected_model="Demio",
            source_ref="DMV_2024",
            added_ts=datetime.utcnow().isoformat()
        )
        store.add_entry(entry)
        
        # Check
        assert store.is_registered("N12345W")
        assert not store.is_registered("NOTEXIST")


class TestMismatchLogic:
    """Test mismatch detection logic"""
    
    def test_normalize_make_model(self):
        """Test normalization"""
        make, model = normalize_make_model("Mazda", "Demio")
        assert make == "mazda"
        assert model == "demio"
        
        make, model = normalize_make_model("  VW  ", "  Golf  ")
        assert make == "volkswagen"
        assert model == "golf"
    
    def test_exact_match_no_mismatch(self):
        """Test that exact match produces no mismatch"""
        score, explanation = compute_mismatch_score(
            expected_make="Mazda",
            expected_model="Demio",
            observed_make="Mazda",
            observed_model="Demio",
            observed_make_confidence=0.8,
            observed_model_confidence=0.8
        )
        
        assert score == 0.0
        assert "No mismatch" in explanation
    
    def test_unknown_observed_no_mismatch(self):
        """Test that unknown observed produces no mismatch"""
        score, explanation = compute_mismatch_score(
            expected_make="Mazda",
            expected_model="Demio",
            observed_make="unknown",
            observed_model="unknown",
            observed_make_confidence=0.0,
            observed_model_confidence=0.0
        )
        
        assert score == 0.0
        assert "Cannot determine" in explanation
    
    def test_partial_mismatch_model_only(self):
        """Test partial mismatch (make matches, model differs)"""
        score, explanation = compute_mismatch_score(
            expected_make="Mazda",
            expected_model="Demio",
            observed_make="Mazda",
            observed_model="Atenza",
            observed_make_confidence=0.8,
            observed_model_confidence=0.7
        )
        
        assert score > 0.0
        assert score < 0.9  # Partial mismatch is less severe
        assert "Partial mismatch" in explanation
    
    def test_full_mismatch(self):
        """Test full mismatch (both make and model differ)"""
        score, explanation = compute_mismatch_score(
            expected_make="Mazda",
            expected_model="Demio",
            observed_make="Toyota",
            observed_model="Corolla",
            observed_make_confidence=0.8,
            observed_model_confidence=0.8
        )
        
        assert score > 0.6
        assert "Full mismatch" in explanation
    
    def test_check_mismatch_below_confidence_threshold(self):
        """Test that low confidence doesn't trigger mismatch"""
        result = check_mismatch(
            plate_text="N12345W",
            expected_make="Mazda",
            expected_model="Demio",
            observed_make="Toyota",
            observed_model="Corolla",
            observed_make_confidence=0.3,  # Below threshold
            observed_model_confidence=0.3,
            min_confidence=0.5
        )
        
        assert result is None
    
    def test_check_mismatch_below_score_threshold(self):
        """Test that low mismatch score doesn't trigger"""
        # Exact match should not trigger even with high confidence
        result = check_mismatch(
            plate_text="N12345W",
            expected_make="Mazda",
            expected_model="Demio",
            observed_make="Mazda",
            observed_model="Demio",
            observed_make_confidence=0.9,
            observed_model_confidence=0.9,
            min_confidence=0.5,
            min_score=0.3
        )
        
        assert result is None
    
    def test_check_mismatch_triggers_correctly(self):
        """Test that valid mismatch triggers"""
        result = check_mismatch(
            plate_text="N12345W",
            expected_make="Mazda",
            expected_model="Demio",
            observed_make="Toyota",
            observed_model="Corolla",
            observed_make_confidence=0.8,
            observed_model_confidence=0.8,
            min_confidence=0.5,
            min_score=0.3
        )
        
        assert result is not None
        assert result.is_mismatch
        assert result.mismatch_score > 0.3
        assert result.plate_text == "N12345W"
        assert result.expected_make == "Mazda"
        assert result.observed_make == "Toyota"


class TestMismatchValidator:
    """Test validator rules for mismatch events"""
    
    def test_mismatch_must_have_neutral_language(self):
        """Test that mismatch alerts must use 'possible mismatch' language"""
        # Create incident with mismatch event
        mismatch_event = CameraEvent(
            event_id="evt_001",
            camera_id="cam_001",
            ts=datetime.utcnow(),
            zone_id="zone_001",
            event_type="plate_vehicle_mismatch",
            confidence=0.85,
            severity=4,
            metadata={
                "plate_text": "N12345W",
                "expected_make": "Mazda",
                "expected_model": "Demio",
                "observed_make": "Toyota",
                "observed_model": "Corolla",
                "mismatch_score": 0.85
            }
        )
        
        incident = Incident(
            incident_id="inc_001",
            status=IncidentStatus.NEW,
            events=[mismatch_event],
            created_ts=datetime.utcnow(),
            updated_ts=datetime.utcnow()
        )
        
        # Plan with certain language (WRONG)
        plan_bad = IncidentPlan(
            incident_id="inc_001",
            summary_1line="Confirmed stolen vehicle with swapped plates",
            severity=4,
            confidence=0.85,
            uncertainty_notes="",
            recommended_next_step=RecommendedAction.NOTIFY,
            requires_human_approval=False
        )
        
        result = validate_incident_plan(plan_bad, incident)
        
        # Should fail
        assert len(result.violations) > 0
        assert any("mismatch" in v.lower() or "forbidden" in v.lower() for v in result.violations)
    
    def test_mismatch_must_require_human_approval(self):
        """Test that mismatch alerts must require human approval"""
        mismatch_event = CameraEvent(
            event_id="evt_001",
            camera_id="cam_001",
            ts=datetime.utcnow(),
            zone_id="zone_001",
            event_type="plate_vehicle_mismatch",
            confidence=0.85,
            severity=4,
            metadata={"mismatch_score": 0.85}
        )
        
        incident = Incident(
            incident_id="inc_001",
            status=IncidentStatus.NEW,
            events=[mismatch_event],
            created_ts=datetime.utcnow(),
            updated_ts=datetime.utcnow()
        )
        
        # Plan without human approval (WRONG)
        plan = IncidentPlan(
            incident_id="inc_001",
            summary_1line="Possible mismatch requires verification",
            severity=4,
            confidence=0.85,
            uncertainty_notes="",
            recommended_next_step=RecommendedAction.DISPATCH_PENDING_REVIEW,
            requires_human_approval=False  # WRONG
        )
        
        result = validate_incident_plan(plan, incident)
        
        # Should have violation about human approval
        assert len(result.violations) > 0
        assert any("human" in v.lower() and "approval" in v.lower() for v in result.violations)
    
    def test_mismatch_valid_plan_passes(self):
        """Test that properly formatted mismatch plan passes"""
        mismatch_event = CameraEvent(
            event_id="evt_001",
            camera_id="cam_001",
            ts=datetime.utcnow(),
            zone_id="zone_001",
            event_type="plate_vehicle_mismatch",
            confidence=0.85,
            severity=4,
            metadata={
                "plate_text": "N12345W",
                "expected_make": "Mazda",
                "expected_model": "Demio",
                "observed_make": "Toyota",
                "observed_model": "Corolla",
                "mismatch_score": 0.85
            },
            snapshot_url="/evidence/snapshot.jpg",
            clip_url="/evidence/clip.mp4"
        )
        
        incident = Incident(
            incident_id="inc_001",
            status=IncidentStatus.NEW,
            events=[mismatch_event],
            created_ts=datetime.utcnow(),
            updated_ts=datetime.utcnow()
        )
        
        # Proper plan
        plan = IncidentPlan(
            incident_id="inc_001",
            summary_1line="Possible plate-vehicle mismatch requires verification at cam_001",
            severity=4,
            confidence=0.85,
            uncertainty_notes="Visual verification required before any action",
            recommended_next_step=RecommendedAction.DISPATCH_PENDING_REVIEW,
            requires_human_approval=True,
            evidence_refs=["/evidence/snapshot.jpg", "/evidence/clip.mp4"]
        )
        
        result = validate_incident_plan(plan, incident)
        
        # Should pass (no violations)
        assert result.passed is True or len(result.violations) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
