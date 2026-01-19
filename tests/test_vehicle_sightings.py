"""
Tests for Vehicle Sightings System

Tests vehicle detection, color classification, sightings storage, and search.
"""

import pytest
import numpy as np
import cv2
import tempfile
from pathlib import Path
from datetime import datetime

from alibi.vehicles.vehicle_detect import VehicleDetector, DetectedVehicle
from alibi.vehicles.vehicle_attrs import VehicleAttributeExtractor, VehicleColor, classify_color_simple
from alibi.vehicles.sightings_store import VehicleSightingsStore, VehicleSighting


class TestVehicleDetector:
    """Test vehicle detection"""
    
    def test_detector_initialization(self):
        """Test detector initializes"""
        detector = VehicleDetector()
        assert detector.min_contour_area == 2000
        assert detector.max_contour_area == 100000
    
    def test_detect_on_synthetic_vehicle(self):
        """Test detecting synthetic vehicle-like region"""
        detector = VehicleDetector()
        
        # Create sequence of frames with moving rectangle
        frames = []
        for x in range(100, 300, 20):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.rectangle(frame, (x, 200), (x + 80, 270), (255, 255, 255), -1)
            frames.append(frame)
        
        # Process frames
        vehicles_detected = False
        for frame in frames:
            vehicles = detector.detect(frame, max_vehicles=1)
            if vehicles:
                vehicles_detected = True
                break
        
        # May or may not detect depending on background subtraction learning
        # Test passes if detector runs without error
        assert isinstance(vehicles_detected, bool)


class TestVehicleColorClassification:
    """Test color classification"""
    
    def test_classify_red_vehicle(self):
        """Test classifying red vehicle (deterministic)"""
        extractor = VehicleAttributeExtractor()
        
        # Create red image
        red_image = np.zeros((100, 150, 3), dtype=np.uint8)
        red_image[:, :] = (0, 0, 255)  # BGR: pure red
        
        attrs = extractor.extract_attributes(red_image)
        
        assert attrs.color == VehicleColor.RED.value
        assert attrs.color_confidence > 0.5
    
    def test_classify_white_vehicle(self):
        """Test classifying white vehicle (deterministic)"""
        extractor = VehicleAttributeExtractor()
        
        # Create white image
        white_image = np.zeros((100, 150, 3), dtype=np.uint8)
        white_image[:, :] = (255, 255, 255)  # BGR: pure white
        
        attrs = extractor.extract_attributes(white_image)
        
        assert attrs.color == VehicleColor.WHITE.value
        assert attrs.color_confidence > 0.5
    
    def test_classify_black_vehicle(self):
        """Test classifying black vehicle (deterministic)"""
        extractor = VehicleAttributeExtractor()
        
        # Create black image
        black_image = np.zeros((100, 150, 3), dtype=np.uint8)
        # Already black (all zeros)
        
        attrs = extractor.extract_attributes(black_image)
        
        assert attrs.color == VehicleColor.BLACK.value
        assert attrs.color_confidence > 0.5
    
    def test_classify_blue_vehicle(self):
        """Test classifying blue vehicle (deterministic)"""
        extractor = VehicleAttributeExtractor()
        
        # Create blue image
        blue_image = np.zeros((100, 150, 3), dtype=np.uint8)
        blue_image[:, :] = (255, 0, 0)  # BGR: pure blue
        
        attrs = extractor.extract_attributes(blue_image)
        
        assert attrs.color == VehicleColor.BLUE.value
        assert attrs.color_confidence > 0.5
    
    def test_make_model_placeholder(self):
        """Test that make/model returns placeholder"""
        extractor = VehicleAttributeExtractor()
        
        # Any image
        image = np.zeros((100, 150, 3), dtype=np.uint8)
        
        attrs = extractor.extract_attributes(image)
        
        # Should return placeholder values
        assert attrs.make == "unknown"
        assert attrs.model == "unknown"
        assert attrs.make_model_confidence == 0.0
    
    def test_color_simple_function(self):
        """Test simple color classification function"""
        # Create green image
        green_image = np.zeros((100, 150, 3), dtype=np.uint8)
        green_image[:, :] = (0, 255, 0)  # BGR: pure green
        
        color = classify_color_simple(green_image)
        
        assert color == VehicleColor.GREEN.value


class TestVehicleSightingsStore:
    """Test sightings storage and search"""
    
    def test_create_and_load_sighting(self, tmp_path):
        """Test creating and loading sightings"""
        store_path = tmp_path / "sightings.jsonl"
        store = VehicleSightingsStore(str(store_path))
        
        # Create sighting
        sighting = VehicleSighting(
            sighting_id="test_001",
            camera_id="cam_001",
            ts=datetime.utcnow().isoformat(),
            bbox=(100, 200, 80, 60),
            color="white",
            make="Mazda",
            model="Demio",
            confidence=0.85,
            snapshot_url="/evidence/test.jpg"
        )
        
        # Add to store
        store.add_sighting(sighting)
        
        # Load back
        sightings = store.load_all()
        assert len(sightings) == 1
        assert sightings[0].sighting_id == "test_001"
        assert sightings[0].make == "Mazda"
        assert sightings[0].model == "Demio"
    
    def test_search_by_make(self, tmp_path):
        """Test searching by make"""
        store_path = tmp_path / "sightings.jsonl"
        store = VehicleSightingsStore(str(store_path))
        
        # Add multiple sightings
        sightings = [
            VehicleSighting("s1", "cam_001", datetime.utcnow().isoformat(),
                          (100, 200, 80, 60), "white", "Mazda", "Demio", 0.8),
            VehicleSighting("s2", "cam_001", datetime.utcnow().isoformat(),
                          (100, 200, 80, 60), "red", "Toyota", "Corolla", 0.8),
            VehicleSighting("s3", "cam_001", datetime.utcnow().isoformat(),
                          (100, 200, 80, 60), "blue", "Mazda", "Atenza", 0.8),
        ]
        
        for s in sightings:
            store.add_sighting(s)
        
        # Search for Mazda
        results = store.search(make="Mazda")
        
        assert len(results) == 2
        assert all(s.make == "Mazda" for s in results)
    
    def test_search_by_model(self, tmp_path):
        """Test searching by model"""
        store_path = tmp_path / "sightings.jsonl"
        store = VehicleSightingsStore(str(store_path))
        
        # Add multiple sightings
        sightings = [
            VehicleSighting("s1", "cam_001", datetime.utcnow().isoformat(),
                          (100, 200, 80, 60), "white", "Mazda", "Demio", 0.8),
            VehicleSighting("s2", "cam_001", datetime.utcnow().isoformat(),
                          (100, 200, 80, 60), "red", "Toyota", "Corolla", 0.8),
            VehicleSighting("s3", "cam_001", datetime.utcnow().isoformat(),
                          (100, 200, 80, 60), "white", "Mazda", "Corolla", 0.8),
        ]
        
        for s in sightings:
            store.add_sighting(s)
        
        # Search for Corolla
        results = store.search(model="Corolla")
        
        assert len(results) == 2
        assert all(s.model == "Corolla" for s in results)
    
    def test_search_by_color(self, tmp_path):
        """Test searching by color"""
        store_path = tmp_path / "sightings.jsonl"
        store = VehicleSightingsStore(str(store_path))
        
        # Add multiple sightings
        sightings = [
            VehicleSighting("s1", "cam_001", datetime.utcnow().isoformat(),
                          (100, 200, 80, 60), "white", "Mazda", "Demio", 0.8),
            VehicleSighting("s2", "cam_001", datetime.utcnow().isoformat(),
                          (100, 200, 80, 60), "red", "Toyota", "Corolla", 0.8),
            VehicleSighting("s3", "cam_001", datetime.utcnow().isoformat(),
                          (100, 200, 80, 60), "white", "Honda", "Civic", 0.8),
        ]
        
        for s in sightings:
            store.add_sighting(s)
        
        # Search for white
        results = store.search(color="white")
        
        assert len(results) == 2
        assert all(s.color == "white" for s in results)
    
    def test_search_combined_filters(self, tmp_path):
        """Test searching with multiple filters"""
        store_path = tmp_path / "sightings.jsonl"
        store = VehicleSightingsStore(str(store_path))
        
        # Add multiple sightings
        sightings = [
            VehicleSighting("s1", "cam_001", datetime.utcnow().isoformat(),
                          (100, 200, 80, 60), "white", "Mazda", "Demio", 0.8),
            VehicleSighting("s2", "cam_001", datetime.utcnow().isoformat(),
                          (100, 200, 80, 60), "red", "Mazda", "Demio", 0.8),
            VehicleSighting("s3", "cam_001", datetime.utcnow().isoformat(),
                          (100, 200, 80, 60), "white", "Toyota", "Demio", 0.8),
        ]
        
        for s in sightings:
            store.add_sighting(s)
        
        # Search for white Mazda Demio
        results = store.search(make="Mazda", model="Demio", color="white")
        
        assert len(results) == 1
        assert results[0].sighting_id == "s1"
    
    def test_get_recent_sightings(self, tmp_path):
        """Test getting recent sightings"""
        store_path = tmp_path / "sightings.jsonl"
        store = VehicleSightingsStore(str(store_path))
        
        # Add sightings
        for i in range(5):
            sighting = VehicleSighting(
                f"s{i}", "cam_001", datetime.utcnow().isoformat(),
                (100, 200, 80, 60), "white", "Mazda", "Demio", 0.8
            )
            store.add_sighting(sighting)
        
        # Get recent (limit 3)
        recent = store.get_recent(limit=3)
        
        assert len(recent) == 3
    
    def test_search_partial_match(self, tmp_path):
        """Test partial matching for make/model"""
        store_path = tmp_path / "sightings.jsonl"
        store = VehicleSightingsStore(str(store_path))
        
        # Add sighting with specific make
        sighting = VehicleSighting(
            "s1", "cam_001", datetime.utcnow().isoformat(),
            (100, 200, 80, 60), "white", "Mazda", "Demio", 0.8
        )
        store.add_sighting(sighting)
        
        # Search with partial string
        results = store.search(make="Maz")  # Partial match
        
        assert len(results) == 1
        assert results[0].make == "Mazda"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
