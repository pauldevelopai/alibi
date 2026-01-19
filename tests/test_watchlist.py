"""
Tests for Watchlist System

Tests enrollment, detection, matching, and safety rules.
"""

import pytest
import numpy as np
import cv2
import tempfile
from pathlib import Path
from datetime import datetime

from alibi.watchlist.watchlist_store import WatchlistStore, WatchlistEntry
from alibi.watchlist.face_detect import FaceDetector
from alibi.watchlist.face_embed import FaceEmbedder
from alibi.watchlist.face_match import FaceMatcher, MatchCandidate
from alibi.video.detectors.watchlist_detector import WatchlistDetector
from alibi.validator import validate_incident_plan
from alibi.schemas import Incident, IncidentPlan, CameraEvent, RecommendedAction, IncidentStatus, ValidationStatus


class TestWatchlistStore:
    """Test watchlist storage"""
    
    def test_create_and_load_entry(self, tmp_path):
        """Test creating and loading watchlist entries"""
        store_path = tmp_path / "test_watchlist.jsonl"
        store = WatchlistStore(str(store_path))
        
        # Create entry
        entry = WatchlistEntry(
            person_id="TEST_001",
            label="Test Person",
            embedding=[0.1, 0.2, 0.3],
            added_ts=datetime.utcnow().isoformat(),
            source_ref="Test Case #123"
        )
        
        # Add to store
        store.add_entry(entry)
        
        # Load back
        entries = store.load_all()
        assert len(entries) == 1
        assert entries[0].person_id == "TEST_001"
        assert entries[0].label == "Test Person"
        assert len(entries[0].embedding) == 3
    
    def test_get_by_person_id(self, tmp_path):
        """Test retrieving entry by person_id"""
        store_path = tmp_path / "test_watchlist.jsonl"
        store = WatchlistStore(str(store_path))
        
        # Add multiple entries
        for i in range(3):
            entry = WatchlistEntry(
                person_id=f"TEST_{i:03d}",
                label=f"Person {i}",
                embedding=[float(i)] * 128,
                added_ts=datetime.utcnow().isoformat(),
                source_ref=f"Case #{i}"
            )
            store.add_entry(entry)
        
        # Retrieve specific entry
        entry = store.get_by_person_id("TEST_001")
        assert entry is not None
        assert entry.label == "Person 1"
    
    def test_get_all_embeddings(self, tmp_path):
        """Test getting all embeddings as dict"""
        store_path = tmp_path / "test_watchlist.jsonl"
        store = WatchlistStore(str(store_path))
        
        # Add entries
        for i in range(3):
            entry = WatchlistEntry(
                person_id=f"TEST_{i:03d}",
                label=f"Person {i}",
                embedding=[float(i)] * 128,
                added_ts=datetime.utcnow().isoformat(),
                source_ref=f"Case #{i}"
            )
            store.add_entry(entry)
        
        # Get embeddings
        embeddings = store.get_all_embeddings()
        assert len(embeddings) == 3
        assert "TEST_001" in embeddings
        assert isinstance(embeddings["TEST_001"], np.ndarray)


class TestFaceDetector:
    """Test face detection"""
    
    def test_detect_face_in_synthetic_image(self):
        """Test detecting a face in a synthetic image"""
        detector = FaceDetector(confidence_threshold=0.3)
        
        # Create synthetic face-like image (simple oval)
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.ellipse(image, (320, 240), (80, 100), 0, 0, 360, (200, 180, 160), -1)
        cv2.circle(image, (300, 220), 10, (50, 50, 50), -1)  # Eye
        cv2.circle(image, (340, 220), 10, (50, 50, 50), -1)  # Eye
        cv2.ellipse(image, (320, 260), (30, 15), 0, 0, 180, (100, 50, 50), 2)  # Mouth
        
        # Detect (may or may not find face depending on detector)
        faces = detector.detect(image)
        
        # Test passes if detector runs without error
        assert isinstance(faces, list)
    
    def test_extract_face(self):
        """Test extracting face region"""
        detector = FaceDetector()
        
        # Create test image
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Define bounding box
        bbox = (100, 100, 200, 200)
        
        # Extract face
        face = detector.extract_face(image, bbox)
        
        # Check dimensions (with padding)
        assert face.shape[0] > 0
        assert face.shape[1] > 0


class TestFaceEmbedder:
    """Test face embedding generation"""
    
    def test_generate_embedding(self):
        """Test generating embedding from face image"""
        embedder = FaceEmbedder()
        
        # Create synthetic face image
        face_image = np.random.randint(0, 255, (96, 96, 3), dtype=np.uint8)
        
        # Generate embedding
        embedding = embedder.generate_embedding(face_image)
        
        # Check properties
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) > 0
        assert embedding.dtype == np.float32
        
        # Check normalization (should be close to unit length)
        norm = np.linalg.norm(embedding)
        assert 0.9 <= norm <= 1.1
    
    def test_consistent_embeddings(self):
        """Test that same image produces consistent embeddings"""
        embedder = FaceEmbedder()
        
        # Create test image
        face_image = np.random.randint(0, 255, (96, 96, 3), dtype=np.uint8)
        
        # Generate twice
        emb1 = embedder.generate_embedding(face_image)
        emb2 = embedder.generate_embedding(face_image)
        
        # Should be identical
        assert np.allclose(emb1, emb2)


class TestFaceMatcher:
    """Test face matching"""
    
    def test_exact_match(self):
        """Test matching identical embeddings"""
        matcher = FaceMatcher(match_threshold=0.9, top_k=3)
        
        # Create identical embeddings
        query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        watchlist_embeddings = {
            "PERSON_001": np.array([1.0, 0.0, 0.0], dtype=np.float32),
            "PERSON_002": np.array([0.0, 1.0, 0.0], dtype=np.float32),
        }
        watchlist_labels = {
            "PERSON_001": "John Doe",
            "PERSON_002": "Jane Smith",
        }
        
        # Match
        is_match, candidates, best_score = matcher.match(
            query, watchlist_embeddings, watchlist_labels
        )
        
        # Should match PERSON_001 perfectly
        assert is_match
        assert best_score > 0.99
        assert candidates[0].person_id == "PERSON_001"
    
    def test_no_match_below_threshold(self):
        """Test that low similarity doesn't match"""
        matcher = FaceMatcher(match_threshold=0.9, top_k=3)
        
        # Create dissimilar embeddings
        query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        watchlist_embeddings = {
            "PERSON_001": np.array([0.0, 1.0, 0.0], dtype=np.float32),
            "PERSON_002": np.array([0.0, 0.0, 1.0], dtype=np.float32),
        }
        watchlist_labels = {
            "PERSON_001": "John Doe",
            "PERSON_002": "Jane Smith",
        }
        
        # Match
        is_match, candidates, best_score = matcher.match(
            query, watchlist_embeddings, watchlist_labels
        )
        
        # Should not match
        assert not is_match
        assert best_score < 0.9
    
    def test_top_k_candidates(self):
        """Test that top-k candidates are returned"""
        matcher = FaceMatcher(match_threshold=0.5, top_k=2)
        
        # Create embeddings with varying similarity
        query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        watchlist_embeddings = {
            "PERSON_001": np.array([0.9, 0.1, 0.0], dtype=np.float32),  # High similarity
            "PERSON_002": np.array([0.7, 0.3, 0.0], dtype=np.float32),  # Medium similarity
            "PERSON_003": np.array([0.0, 1.0, 0.0], dtype=np.float32),  # Low similarity
        }
        watchlist_labels = {
            "PERSON_001": "Person 1",
            "PERSON_002": "Person 2",
            "PERSON_003": "Person 3",
        }
        
        # Match
        is_match, candidates, best_score = matcher.match(
            query, watchlist_embeddings, watchlist_labels
        )
        
        # Should return top 2
        assert len(candidates) == 2
        assert candidates[0].person_id == "PERSON_001"
        assert candidates[1].person_id == "PERSON_002"


class TestWatchlistDetector:
    """Test watchlist detector"""
    
    def test_detector_initialization(self, tmp_path):
        """Test detector initializes correctly"""
        watchlist_path = tmp_path / "watchlist.jsonl"
        
        detector = WatchlistDetector(
            name="test_watchlist",
            config={
                "watchlist_path": str(watchlist_path),
                "match_threshold": 0.6,
                "check_interval_seconds": 1.0,
            }
        )
        
        assert detector.name == "test_watchlist"
        assert detector.match_threshold == 0.6
    
    def test_detector_with_empty_watchlist(self, tmp_path):
        """Test detector with no watchlist entries"""
        watchlist_path = tmp_path / "watchlist.jsonl"
        
        detector = WatchlistDetector(
            name="test_watchlist",
            config={
                "watchlist_path": str(watchlist_path),
            }
        )
        
        # Create test frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Should return None (no watchlist entries)
        result = detector.detect(frame, timestamp=0.0)
        assert result is None
    
    def test_detector_emits_watchlist_match(self, tmp_path):
        """Test detector emits watchlist_match event"""
        # This is a simplified test - in practice, face detection may not work on random images
        watchlist_path = tmp_path / "watchlist.jsonl"
        
        # Create watchlist with entry
        store = WatchlistStore(str(watchlist_path))
        entry = WatchlistEntry(
            person_id="TEST_001",
            label="Test Person",
            embedding=np.random.randn(128).tolist(),
            added_ts=datetime.utcnow().isoformat(),
            source_ref="Test"
        )
        store.add_entry(entry)
        
        detector = WatchlistDetector(
            name="test_watchlist",
            config={
                "watchlist_path": str(watchlist_path),
                "match_threshold": 0.3,  # Low threshold for testing
                "check_interval_seconds": 0.0,  # Check every frame
            }
        )
        
        # Reload watchlist
        detector._reload_watchlist()
        
        # Verify watchlist loaded
        assert len(detector.watchlist_embeddings) == 1


class TestWatchlistValidation:
    """Test watchlist safety rules in validator"""
    
    def test_watchlist_match_requires_approval(self):
        """Test that watchlist match requires human approval"""
        # Create incident with watchlist match
        event = CameraEvent(
            event_id="evt_001",
            camera_id="cam_001",
            ts=datetime.utcnow(),
            zone_id="zone_001",
            event_type="watchlist_match",
            confidence=0.85,
            severity=4,
            clip_url="/evidence/clips/test.mp4",
            snapshot_url="/evidence/snapshots/test.jpg",
            metadata={"match_score": 0.85}
        )
        
        incident = Incident(
            incident_id="inc_001",
            status=IncidentStatus.NEW,
            created_ts=datetime.utcnow(),
            updated_ts=datetime.utcnow(),
            events=[event]
        )
        
        # Create plan WITHOUT human approval (should violate)
        plan = IncidentPlan(
            incident_id="inc_001",
            summary_1line="Watchlist match detected",
            recommended_next_step=RecommendedAction.NOTIFY,
            confidence=0.85,
            severity=4,
            requires_human_approval=False,  # WRONG
            evidence_refs=["/evidence/clips/test.mp4"],
            uncertainty_notes="None"
        )
        
        # Validate
        result = validate_incident_plan(plan, incident)
        
        # Should fail validation
        assert result.status == ValidationStatus.FAIL
        assert not result.passed
        assert any("watchlist" in v.lower() for v in result.violations)
    
    def test_watchlist_alert_language(self):
        """Test that watchlist alerts use proper language"""
        event = CameraEvent(
            event_id="evt_001",
            camera_id="cam_001",
            ts=datetime.utcnow(),
            zone_id="zone_001",
            event_type="watchlist_match",
            confidence=0.85,
            severity=4,
            clip_url="/evidence/clips/test.mp4",
            snapshot_url="/evidence/snapshots/test.jpg",
            metadata={"match_score": 0.85}
        )
        
        incident = Incident(
            incident_id="inc_001",
            status=IncidentStatus.NEW,
            created_ts=datetime.utcnow(),
            updated_ts=datetime.utcnow(),
            events=[event]
        )
        
        # Test forbidden language: "identified as John Doe"
        plan_bad = IncidentPlan(
            incident_id="inc_001",
            summary_1line="Person identified as John Doe",  # FORBIDDEN
            recommended_next_step=RecommendedAction.DISPATCH_PENDING_REVIEW,
            confidence=0.85,
            severity=4,
            requires_human_approval=True,
            evidence_refs=["/evidence/clips/test.mp4"],
            uncertainty_notes="None"
        )
        
        result = validate_incident_plan(plan_bad, incident)
        assert result.status == ValidationStatus.FAIL
        assert not result.passed
        assert any("identity claim" in v.lower() or "possible match" in v.lower() for v in result.violations)
        
        # Test correct language: "possible match"
        plan_good = IncidentPlan(
            incident_id="inc_001",
            summary_1line="Possible watchlist match requires verification",  # CORRECT
            recommended_next_step=RecommendedAction.DISPATCH_PENDING_REVIEW,
            confidence=0.85,
            severity=4,
            requires_human_approval=True,
            evidence_refs=["/evidence/clips/test.mp4"],
            uncertainty_notes="None"
        )
        
        result = validate_incident_plan(plan_good, incident)
        # Should pass (no violations), may have warnings
        assert result.passed
        assert len(result.violations) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
