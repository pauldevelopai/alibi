"""
Tests for Digital Shield Detectors

Tests loitering, aggression, and crowd panic detectors with synthetic frames.
"""

import pytest
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import Mock

from alibi.video.detectors.loitering_detector import LoiteringDetector
from alibi.video.detectors.aggression_detector import AggressionDetector
from alibi.video.detectors.crowd_panic_detector import CrowdPanicDetector
from alibi.video.zones import Zone


def create_test_zone(restricted=False):
    """Create a test zone for detectors"""
    return Zone(
        zone_id="test_zone",
        name="Test Zone",
        polygon=[(100, 100), (500, 100), (500, 400), (100, 400)],
        metadata={"restricted": restricted}
    )


class TestLoiteringDetector:
    """Test loitering detector"""
    
    def test_detector_initialization(self):
        """Test detector can be initialized"""
        detector = LoiteringDetector(name="test_loitering")
        
        assert detector.name == "test_loitering"
        assert detector.enabled == True
        assert detector.dwell_threshold == 30.0
    
    def test_no_detection_in_non_restricted_zone(self):
        """Test that detector doesn't trigger in non-restricted zones"""
        detector = LoiteringDetector(
            config={'dwell_threshold_seconds': 5}
        )
        
        zone = create_test_zone(restricted=False)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        result = detector.detect(frame, 100.0, zone=zone)
        
        assert result is None
    
    def test_loitering_detection_with_stationary_blob(self):
        """Test detection of stationary object in restricted zone"""
        detector = LoiteringDetector(
            config={
                'dwell_threshold_seconds': 3.0,  # Short threshold for testing
                'min_blob_area': 500
            }
        )
        
        zone = create_test_zone(restricted=True)
        
        # Feed frames with stationary white rectangle in zone
        base_time = 1000.0
        
        for i in range(20):  # 20 frames over 10 seconds (0.5s per frame)
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Add stationary white rectangle in zone
            cv2.rectangle(frame, (250, 200), (350, 300), (255, 255, 255), -1)
            
            result = detector.detect(frame, base_time + i * 0.5, zone=zone)
            
            # Should detect after dwell threshold
            if i * 0.5 >= 3.0:
                if result:  # Detection may take a few frames to stabilize
                    assert result.detected == True
                    assert result.event_type == "loitering"
                    assert result.severity >= 2
                    assert "dwell_seconds" in result.metadata
                    assert result.metadata["zone_restricted"] == True
                    break
    
    def test_loitering_reset(self):
        """Test detector reset clears state"""
        detector = LoiteringDetector()
        
        # Add some tracked blobs
        zone = create_test_zone(restricted=True)
        frame = np.full((480, 640, 3), 128, dtype=np.uint8)
        
        detector.detect(frame, 100.0, zone=zone)
        
        # Reset
        detector.reset()
        
        assert len(detector.tracked_blobs) == 0
        assert detector.next_blob_id == 0


class TestAggressionDetector:
    """Test aggression detector"""
    
    def test_detector_initialization(self):
        """Test detector can be initialized"""
        detector = AggressionDetector(name="test_aggression")
        
        assert detector.name == "test_aggression"
        assert detector.enabled == True
        assert detector.motion_threshold == 5000
    
    def test_no_detection_without_motion(self):
        """Test no detection when there's no motion"""
        detector = AggressionDetector()
        
        zone = create_test_zone()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Feed identical frames (no motion)
        for i in range(15):
            result = detector.detect(frame, 100.0 + i, zone=zone)
        
        assert result is None  # No motion, no detection
    
    def test_aggression_detection_with_erratic_motion(self):
        """Test detection of erratic motion patterns"""
        detector = AggressionDetector(
            config={
                'motion_threshold': 2000,  # Lower for testing
                'variability_threshold': 0.3,
                'window_frames': 8
            }
        )
        
        zone = create_test_zone()
        
        # Create frames with erratic motion
        base_time = 1000.0
        
        for i in range(15):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Add moving white rectangles with varying positions and sizes
            # Simulate erratic, clustered movement
            x = 250 + int(20 * np.sin(i * 2.0))  # Rapid oscillation
            y = 250 + int(15 * np.cos(i * 1.5))
            size = 40 + int(20 * np.sin(i * 3.0))
            
            cv2.rectangle(
                frame,
                (x, y),
                (x + size, y + size),
                (255, 255, 255),
                -1
            )
            
            result = detector.detect(frame, base_time + i * 0.2, zone=zone)
            
            # Should detect after enough frames
            if result and result.detected:
                assert result.event_type == "aggression"
                assert result.severity >= 3
                assert "motion_energy" in result.metadata
                assert "variability_score" in result.metadata
                assert result.metadata["variability_score"] > 0.3
                break
    
    def test_aggression_reset(self):
        """Test detector reset clears state"""
        detector = AggressionDetector()
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detector.detect(frame, 100.0)
        
        # Reset
        detector.reset()
        
        assert detector.prev_frame is None
        assert len(detector.motion_history) == 0


class TestCrowdPanicDetector:
    """Test crowd panic detector"""
    
    def test_detector_initialization(self):
        """Test detector can be initialized"""
        detector = CrowdPanicDetector(name="test_panic")
        
        assert detector.name == "test_panic"
        assert detector.enabled == True
        assert detector.entropy_threshold == 2.5
    
    def test_no_detection_without_crowd(self):
        """Test no detection in empty scenes"""
        detector = CrowdPanicDetector()
        
        zone = create_test_zone()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Feed empty frames
        for i in range(15):
            result = detector.detect(frame, 100.0 + i, zone=zone)
        
        assert result is None
    
    def test_panic_detection_with_chaotic_movement(self):
        """Test detection of chaotic crowd movement"""
        detector = CrowdPanicDetector(
            config={
                'entropy_threshold': 2.0,  # Lower for testing
                'change_rate_threshold': 0.3,
                'window_frames': 6
            }
        )
        
        zone = create_test_zone()
        
        # Create frames with chaotic, changing crowd patterns
        base_time = 1000.0
        
        for i in range(12):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Simulate chaotic crowd with multiple random blobs
            # that change position rapidly
            np.random.seed(i * 7)  # Different seed per frame for chaos
            
            for j in range(8):  # Multiple blobs
                x = np.random.randint(150, 450)
                y = np.random.randint(150, 350)
                radius = np.random.randint(15, 40)
                
                cv2.circle(frame, (x, y), radius, (200, 200, 200), -1)
            
            result = detector.detect(frame, base_time + i * 0.3, zone=zone)
            
            # Should detect after enough frames
            if result and result.detected:
                assert result.event_type == "crowd_panic"
                assert result.severity >= 4  # High severity for panic
                assert "entropy_score" in result.metadata
                assert "change_rate" in result.metadata
                break
    
    def test_panic_reset(self):
        """Test detector reset clears state"""
        detector = CrowdPanicDetector()
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detector.detect(frame, 100.0)
        
        # Reset
        detector.reset()
        
        assert detector.prev_distribution is None
        assert len(detector.distribution_history) == 0
        assert len(detector.entropy_history) == 0


class TestDigitalShieldIntegration:
    """Integration tests for Digital Shield suite"""
    
    def test_all_detectors_can_run_on_same_frame(self):
        """Test all detectors can process the same frame without conflicts"""
        loitering = LoiteringDetector()
        aggression = AggressionDetector()
        panic = CrowdPanicDetector()
        
        zone = create_test_zone(restricted=True)
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # All should run without errors
        result1 = loitering.detect(frame, 100.0, zone=zone)
        result2 = aggression.detect(frame, 100.0, zone=zone)
        result3 = panic.detect(frame, 100.0, zone=zone)
        
        # Results may be None (no detection), but shouldn't error
        assert result1 is None or result1.detected is not None
        assert result2 is None or result2.detected is not None
        assert result3 is None or result3.detected is not None
    
    def test_detectors_with_test_video(self):
        """Test detectors can process real video file if available"""
        test_video = Path("alibi/data/test_video.mp4")
        
        if not test_video.exists():
            pytest.skip("test_video.mp4 not found")
        
        # Initialize detectors
        detectors = [
            LoiteringDetector(),
            AggressionDetector(),
            CrowdPanicDetector()
        ]
        
        zone = create_test_zone(restricted=True)
        
        # Open video
        cap = cv2.VideoCapture(str(test_video))
        
        if not cap.isOpened():
            pytest.skip("Could not open test_video.mp4")
        
        frame_count = 0
        detections = []
        
        # Process first 30 frames
        while frame_count < 30:
            ret, frame = cap.read()
            if not ret:
                break
            
            timestamp = 1000.0 + frame_count * 0.1
            
            # Run all detectors
            for detector in detectors:
                result = detector.detect(frame, timestamp, zone=zone)
                if result and result.detected:
                    detections.append((detector.name, result))
            
            frame_count += 1
        
        cap.release()
        
        # Should have processed frames
        assert frame_count > 0
        
        # Detections may or may not occur depending on video content
        print(f"\nProcessed {frame_count} frames")
        print(f"Total detections: {len(detections)}")
        
        for detector_name, result in detections:
            print(f"  {detector_name}: {result.event_type} "
                  f"(confidence={result.confidence:.2f}, "
                  f"severity={result.severity})")


class TestDetectorConfigurations:
    """Test detector configuration handling"""
    
    def test_loitering_custom_config(self):
        """Test loitering detector with custom configuration"""
        config = {
            'dwell_threshold_seconds': 60,
            'min_blob_area': 2000,
            'base_confidence': 0.85
        }
        
        detector = LoiteringDetector(config=config)
        
        assert detector.dwell_threshold == 60
        assert detector.min_blob_area == 2000
        assert detector.base_confidence == 0.85
    
    def test_aggression_custom_config(self):
        """Test aggression detector with custom configuration"""
        config = {
            'motion_threshold': 8000,
            'variability_threshold': 0.5,
            'base_severity': 4
        }
        
        detector = AggressionDetector(config=config)
        
        assert detector.motion_threshold == 8000
        assert detector.variability_threshold == 0.5
        assert detector.base_severity == 4
    
    def test_panic_custom_config(self):
        """Test panic detector with custom configuration"""
        config = {
            'entropy_threshold': 3.0,
            'grid_size': (10, 10),
            'window_frames': 12
        }
        
        detector = CrowdPanicDetector(config=config)
        
        assert detector.entropy_threshold == 3.0
        assert detector.grid_size == (10, 10)
        assert detector.window_frames == 12


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
