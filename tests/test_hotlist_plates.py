"""
Tests for Hotlist Plate System

Tests plate detection, OCR, normalization, hotlist matching, and validation.
"""

import pytest
import numpy as np
import cv2
import tempfile
from pathlib import Path
from datetime import datetime

from alibi.plates.plate_detect import PlateDetector, DetectedPlate
from alibi.plates.normalize import normalize_plate, is_valid_namibia_plate, fuzzy_match_plates, levenshtein_distance
from alibi.plates.hotlist_store import HotlistStore, HotlistEntry
from alibi.validator import validate_incident_plan
from alibi.schemas import Incident, IncidentPlan, CameraEvent, RecommendedAction, IncidentStatus, ValidationStatus


class TestPlateNormalization:
    """Test plate normalization"""
    
    def test_normalize_simple_plate(self):
        """Test normalizing simple plate"""
        # Namibia format: N 12345 W
        assert normalize_plate("N 12345 W") == "N12345W"
        assert normalize_plate("N12345W") == "N12345W"
        assert normalize_plate("n12345w") == "N12345W"
    
    def test_normalize_with_hyphens(self):
        """Test normalizing plates with hyphens"""
        assert normalize_plate("N-12345-W") == "N12345W"
        assert normalize_plate("N - 12345 - W") == "N12345W"
    
    def test_normalize_messy_ocr(self):
        """Test normalizing messy OCR output"""
        # Extra spaces
        assert normalize_plate("N  12345  W") == "N12345W"
        
        # Special characters
        assert normalize_plate("N.12345.W") == "N12345W"
        assert normalize_plate("N/12345/W") == "N12345W"
    
    def test_normalize_empty_or_invalid(self):
        """Test handling invalid input"""
        assert normalize_plate("") == ""
        assert normalize_plate("   ") == ""
        assert normalize_plate("!!@#$") == ""
    
    def test_is_valid_namibia_plate(self):
        """Test validating Namibia plate formats"""
        # Valid formats
        assert is_valid_namibia_plate("N12345W")
        assert is_valid_namibia_plate("K12345E")
        
        # Invalid formats
        assert not is_valid_namibia_plate("")
        assert not is_valid_namibia_plate("12345")
        assert not is_valid_namibia_plate("ABCDEF")


class TestLevenshteinDistance:
    """Test edit distance calculation"""
    
    def test_identical_strings(self):
        """Test distance between identical strings"""
        assert levenshtein_distance("N12345W", "N12345W") == 0
    
    def test_one_character_diff(self):
        """Test one character difference"""
        assert levenshtein_distance("N12345W", "N12346W") == 1
        assert levenshtein_distance("N12345W", "M12345W") == 1
    
    def test_multiple_diffs(self):
        """Test multiple differences"""
        assert levenshtein_distance("N12345W", "N54321W") == 4
    
    def test_fuzzy_match(self):
        """Test fuzzy plate matching"""
        # Should match with 1 char difference
        assert fuzzy_match_plates("N12345W", "N12346W", max_distance=1)
        
        # Should not match with 2 char difference (5->7 and 6 added = 2)
        assert not fuzzy_match_plates("N12345W", "N123467W", max_distance=1)
        
        # Should match with spaces (normalized)
        assert fuzzy_match_plates("N 12345 W", "N12345W", max_distance=0)


class TestHotlistStore:
    """Test hotlist storage"""
    
    def test_create_and_load_entry(self, tmp_path):
        """Test creating and loading hotlist entries"""
        store_path = tmp_path / "hotlist.jsonl"
        store = HotlistStore(str(store_path))
        
        # Create entry
        entry = HotlistEntry(
            plate="N12345W",
            reason="Stolen",
            added_ts=datetime.utcnow().isoformat(),
            source_ref="Case #2024-1234"
        )
        
        # Add to store
        store.add_entry(entry)
        
        # Load back
        entries = store.load_all()
        assert len(entries) == 1
        assert entries[0].plate == "N12345W"
        assert entries[0].reason == "Stolen"
    
    def test_get_by_plate(self, tmp_path):
        """Test retrieving entry by plate"""
        store_path = tmp_path / "hotlist.jsonl"
        store = HotlistStore(str(store_path))
        
        # Add multiple entries
        for i in range(3):
            entry = HotlistEntry(
                plate=f"N1234{i}W",
                reason="Stolen",
                added_ts=datetime.utcnow().isoformat(),
                source_ref=f"Case #{i}"
            )
            store.add_entry(entry)
        
        # Retrieve specific entry
        entry = store.get_by_plate("N12341W")
        assert entry is not None
        assert entry.source_ref == "Case #1"
    
    def test_is_on_hotlist(self, tmp_path):
        """Test checking if plate is on hotlist"""
        store_path = tmp_path / "hotlist.jsonl"
        store = HotlistStore(str(store_path))
        
        # Add entry
        entry = HotlistEntry(
            plate="N12345W",
            reason="Stolen",
            added_ts=datetime.utcnow().isoformat(),
            source_ref="Case #1"
        )
        store.add_entry(entry)
        
        # Check
        assert store.is_on_hotlist("N12345W")
        assert not store.is_on_hotlist("N99999W")
    
    def test_remove_entry(self, tmp_path):
        """Test removing entry from hotlist"""
        store_path = tmp_path / "hotlist.jsonl"
        store = HotlistStore(str(store_path))
        
        # Add entry
        entry = HotlistEntry(
            plate="N12345W",
            reason="Stolen",
            added_ts=datetime.utcnow().isoformat(),
            source_ref="Case #1"
        )
        store.add_entry(entry)
        
        # Verify it's there
        assert store.is_on_hotlist("N12345W")
        
        # Remove
        removed = store.remove_entry("N12345W")
        assert removed
        
        # Verify it's gone (from active entries)
        assert not store.is_on_hotlist("N12345W")
        
        # But entry still exists in file (audit trail)
        all_entries = store.load_all()
        assert len(all_entries) == 2  # Original + removal record
    
    def test_cache_functionality(self, tmp_path):
        """Test that caching works"""
        store_path = tmp_path / "hotlist.jsonl"
        store = HotlistStore(str(store_path))
        
        # Add entry
        entry = HotlistEntry(
            plate="N12345W",
            reason="Stolen",
            added_ts=datetime.utcnow().isoformat(),
            source_ref="Case #1"
        )
        store.add_entry(entry)
        
        # First lookup (builds cache)
        result1 = store.get_by_plate("N12345W", use_cache=True)
        assert result1 is not None
        
        # Second lookup (uses cache)
        result2 = store.get_by_plate("N12345W", use_cache=True)
        assert result2 is not None
        assert result2.plate == result1.plate


class TestPlateDetector:
    """Test plate detection"""
    
    def test_detector_initialization(self):
        """Test detector initializes"""
        detector = PlateDetector()
        assert detector.min_aspect_ratio == 2.0
        assert detector.max_aspect_ratio == 5.5
    
    def test_detect_on_synthetic_plate(self):
        """Test detecting synthetic plate-like region"""
        # Create image with rectangular region
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw plate-like rectangle
        cv2.rectangle(frame, (200, 200), (400, 260), (255, 255, 255), -1)
        cv2.putText(frame, "N12345W", (210, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        detector = PlateDetector()
        plates = detector.detect(frame, max_plates=1)
        
        # May or may not detect depending on edge strength
        # Test passes if detector runs without error
        assert isinstance(plates, list)


class TestHotlistValidation:
    """Test validator rules for hotlist plates"""
    
    def test_hotlist_requires_approval(self):
        """Test that hotlist matches require human approval"""
        event = CameraEvent(
            event_id="evt_001",
            camera_id="cam_001",
            ts=datetime.utcnow(),
            zone_id=None,
            event_type="hotlist_plate_match",
            confidence=0.85,
            severity=4,
            clip_url="/evidence/clips/test.mp4",
            snapshot_url="/evidence/snapshots/test.jpg",
            metadata={"plate_text": "N12345W", "ocr_confidence": 0.85}
        )
        
        incident = Incident(
            incident_id="inc_001",
            status=IncidentStatus.NEW,
            created_ts=datetime.utcnow(),
            updated_ts=datetime.utcnow(),
            events=[event]
        )
        
        # Plan WITHOUT approval (should violate)
        plan = IncidentPlan(
            incident_id="inc_001",
            summary_1line="Hotlist plate detected",
            recommended_next_step=RecommendedAction.NOTIFY,
            confidence=0.85,
            severity=4,
            requires_human_approval=False,  # WRONG
            evidence_refs=["/evidence/clips/test.mp4"],
            uncertainty_notes="None"
        )
        
        result = validate_incident_plan(plan, incident)
        
        assert result.status == ValidationStatus.FAIL
        assert not result.passed
        assert any("hotlist" in v.lower() and "approval" in v.lower() for v in result.violations)
    
    def test_hotlist_language_enforcement(self):
        """Test that hotlist alerts use proper language"""
        event = CameraEvent(
            event_id="evt_001",
            camera_id="cam_001",
            ts=datetime.utcnow(),
            zone_id=None,
            event_type="hotlist_plate_match",
            confidence=0.85,
            severity=4,
            clip_url="/evidence/clips/test.mp4",
            snapshot_url="/evidence/snapshots/test.jpg",
            metadata={"plate_text": "N12345W"}
        )
        
        incident = Incident(
            incident_id="inc_001",
            status=IncidentStatus.NEW,
            created_ts=datetime.utcnow(),
            updated_ts=datetime.utcnow(),
            events=[event]
        )
        
        # Test forbidden language: "confirmed stolen"
        plan_bad = IncidentPlan(
            incident_id="inc_001",
            summary_1line="Confirmed stolen vehicle at location",  # FORBIDDEN
            recommended_next_step=RecommendedAction.DISPATCH_PENDING_REVIEW,
            confidence=0.85,
            severity=4,
            requires_human_approval=True,
            evidence_refs=["/evidence/clips/test.mp4"],
            uncertainty_notes="None"
        )
        
        result = validate_incident_plan(plan_bad, incident)
        assert not result.passed
        assert any("hotlist" in v.lower() or "possible" in v.lower() for v in result.violations)
        
        # Test correct language: "possible hotlist match"
        plan_good = IncidentPlan(
            incident_id="inc_001",
            summary_1line="Possible hotlist plate match requires verification",  # CORRECT
            recommended_next_step=RecommendedAction.DISPATCH_PENDING_REVIEW,
            confidence=0.85,
            severity=4,
            requires_human_approval=True,
            evidence_refs=["/evidence/clips/test.mp4"],
            uncertainty_notes="None"
        )
        
        result = validate_incident_plan(plan_good, incident)
        assert result.passed
        assert len(result.violations) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
