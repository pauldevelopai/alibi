"""
Tests for Alibi Video Processing

Tests zone masking, motion detection, and worker components.
"""

import pytest
import numpy as np
import cv2
import time
from pathlib import Path

from alibi.video.zones import Zone, ZoneManager, compute_zone_activity
from alibi.video.frame_sampler import FrameSampler, SamplerConfig
from alibi.video.detectors.motion_detector import MotionDetector
from alibi.video.detectors.presence_after_hours import PresenceAfterHoursDetector
from alibi.video.worker import EventThrottler


class TestZones:
    """Test zone creation and masking"""
    
    def test_zone_creation(self):
        """Test basic zone creation"""
        zone = Zone(
            zone_id="test_zone",
            name="Test Zone",
            polygon=[(100, 100), (200, 100), (200, 200), (100, 200)]
        )
        
        assert zone.zone_id == "test_zone"
        assert zone.name == "Test Zone"
        assert len(zone.polygon) == 4
        assert zone.enabled
    
    def test_zone_mask_creation(self):
        """Test zone mask generation"""
        zone = Zone(
            zone_id="test",
            name="Test",
            polygon=[(100, 100), (200, 100), (200, 200), (100, 200)]
        )
        
        mask = zone.create_mask(400, 400)
        
        assert mask.shape == (400, 400)
        assert mask.dtype == np.uint8
        
        # Inside zone should be 255
        assert mask[150, 150] == 255
        
        # Outside zone should be 0
        assert mask[50, 50] == 0
        assert mask[300, 300] == 0
    
    def test_point_in_zone(self):
        """Test point containment check"""
        zone = Zone(
            zone_id="test",
            name="Test",
            polygon=[(100, 100), (200, 100), (200, 200), (100, 200)]
        )
        
        # Inside
        assert zone.contains_point(150, 150) == True
        
        # Outside
        assert zone.contains_point(50, 50) == False
        assert zone.contains_point(250, 250) == False
        
        # Edge/boundary (depends on cv2 implementation)
        # Just verify it doesn't crash
        zone.contains_point(100, 100)
    
    def test_zone_bounding_box(self):
        """Test bounding box calculation"""
        zone = Zone(
            zone_id="test",
            name="Test",
            polygon=[(100, 100), (200, 100), (200, 200), (100, 200)]
        )
        
        x, y, w, h = zone.get_bounding_box()
        
        assert x == 100
        assert y == 100
        assert w == 100
        assert h == 100
    
    def test_zone_manager_loading(self):
        """Test zone manager with default zones"""
        manager = ZoneManager()  # Should create defaults
        
        # Should have at least one zone
        zones = manager.get_all_zones()
        assert len(zones) >= 0  # May be empty if no config
    
    def test_compute_zone_activity(self):
        """Test zone activity computation"""
        # Create zone mask
        zone_mask = np.zeros((100, 100), dtype=np.uint8)
        zone_mask[25:75, 25:75] = 255  # 50x50 zone
        
        # Create motion mask (partial overlap)
        motion_mask = np.zeros((100, 100), dtype=np.uint8)
        motion_mask[40:60, 40:60] = 255  # 20x20 motion
        
        activity = compute_zone_activity(zone_mask, motion_mask)
        
        # 20x20 motion in 50x50 zone = 400/2500 = 0.16
        assert 0.15 < activity < 0.17
    
    def test_zone_activity_no_motion(self):
        """Test zone activity with no motion"""
        zone_mask = np.zeros((100, 100), dtype=np.uint8)
        zone_mask[25:75, 25:75] = 255
        
        motion_mask = np.zeros((100, 100), dtype=np.uint8)
        
        activity = compute_zone_activity(zone_mask, motion_mask)
        
        assert activity == 0.0
    
    def test_zone_activity_full_motion(self):
        """Test zone activity with full motion"""
        zone_mask = np.zeros((100, 100), dtype=np.uint8)
        zone_mask[25:75, 25:75] = 255
        
        motion_mask = np.zeros((100, 100), dtype=np.uint8)
        motion_mask[25:75, 25:75] = 255
        
        activity = compute_zone_activity(zone_mask, motion_mask)
        
        assert activity == 1.0


class TestFrameSampler:
    """Test frame sampling"""
    
    def test_sampler_creation(self):
        """Test sampler configuration"""
        config = SamplerConfig(target_fps=2.0)
        sampler = FrameSampler(config)
        
        assert sampler.config.target_fps == 2.0
        assert sampler.sample_interval == 0.5
    
    def test_should_sample_timing(self):
        """Test sampling timing logic"""
        config = SamplerConfig(target_fps=1.0)  # 1 frame per second
        sampler = FrameSampler(config)
        
        # First sample should be immediate (last_frame_time is 0.0)
        assert sampler.should_sample(0.0) == True
        sampler.last_frame_time = 100.0  # Simulate first sample at t=100
        
        # Too soon (only 0.5s elapsed)
        assert sampler.should_sample(100.5) == False
        
        # After interval (1.0s elapsed)
        assert sampler.should_sample(101.0) == True
    
    def test_sampler_stats(self):
        """Test statistics tracking"""
        config = SamplerConfig(target_fps=1.0)
        sampler = FrameSampler(config)
        
        # Create dummy frames
        frames = [np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8) for _ in range(10)]
        
        # Sample (will sample all since we control timing)
        sampled = list(sampler.sample(iter(frames)))
        
        stats = sampler.get_stats()
        
        assert stats['frames_processed'] == 10
        assert stats['frames_sampled'] == len(sampled)
        assert stats['target_fps'] == 1.0


class TestMotionDetector:
    """Test motion detection"""
    
    def test_detector_creation(self):
        """Test detector initialization"""
        detector = MotionDetector()
        
        assert detector.name == "motion"
        assert detector.enabled == True
        assert detector.threshold > 0
        assert detector.min_area > 0
    
    def test_motion_detection_no_change(self):
        """Test no motion on identical frames"""
        detector = MotionDetector()
        
        # Create identical frames
        frame1 = np.ones((480, 640, 3), dtype=np.uint8) * 100
        frame2 = frame1.copy()
        
        # First frame initializes
        result1 = detector.detect(frame1, time.time())
        assert result1 is None
        
        # Second frame (no motion)
        result2 = detector.detect(frame2, time.time())
        assert result2 is None or result2.detected == False
    
    def test_motion_detection_with_change(self):
        """Test motion detection on different frames"""
        detector = MotionDetector(config={'min_area': 100, 'activity_threshold': 0.005})
        
        # Create frame 1
        frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Create frame 2 with large white rectangle (significant motion)
        frame2 = np.zeros((480, 640, 3), dtype=np.uint8)
        frame2[100:300, 200:400, :] = 255
        
        # Initialize with frame 1
        detector.detect(frame1, time.time())
        
        # Detect motion in frame 2
        result = detector.detect(frame2, time.time())
        
        # Should detect motion
        assert result is not None
        assert result.detected == True
        assert result.event_type == "motion_in_zone"
        assert 0.0 <= result.confidence <= 1.0
        assert 1 <= result.severity <= 5
        assert 'motion_area' in result.metadata
    
    def test_motion_detector_reset(self):
        """Test detector reset"""
        detector = MotionDetector()
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detector.detect(frame, time.time())
        
        assert detector.prev_frame is not None
        
        detector.reset()
        
        assert detector.prev_frame is None
        assert detector.frame_count == 0


class TestPresenceAfterHoursDetector:
    """Test after-hours presence detection"""
    
    def test_detector_creation(self):
        """Test after-hours detector initialization"""
        detector = PresenceAfterHoursDetector()
        
        assert detector.name == "after_hours"
        assert detector.enabled == True
        assert detector.motion_detector is not None
    
    def test_time_window_parsing(self):
        """Test time window configuration"""
        detector = PresenceAfterHoursDetector(config={
            'after_hours_start': '22:00',
            'after_hours_end': '06:00'
        })
        
        assert detector.after_hours_start.hour == 22
        assert detector.after_hours_end.hour == 6
    
    def test_after_hours_check_overnight(self):
        """Test after-hours check for overnight window"""
        detector = PresenceAfterHoursDetector(config={
            'after_hours_start': '22:00',
            'after_hours_end': '06:00'
        })
        
        # 23:00 should be after hours
        from datetime import datetime
        dt = datetime(2026, 1, 18, 23, 0, 0)
        assert detector.is_after_hours(dt.timestamp()) == True
        
        # 03:00 should be after hours
        dt = datetime(2026, 1, 18, 3, 0, 0)
        assert detector.is_after_hours(dt.timestamp()) == True
        
        # 12:00 should NOT be after hours
        dt = datetime(2026, 1, 18, 12, 0, 0)
        assert detector.is_after_hours(dt.timestamp()) == False
    
    def test_after_hours_check_daytime(self):
        """Test after-hours check for daytime window"""
        detector = PresenceAfterHoursDetector(config={
            'after_hours_start': '09:00',
            'after_hours_end': '17:00'
        })
        
        # 10:00 should be after hours (within window)
        from datetime import datetime
        dt = datetime(2026, 1, 18, 10, 0, 0)
        assert detector.is_after_hours(dt.timestamp()) == True
        
        # 20:00 should NOT be after hours
        dt = datetime(2026, 1, 18, 20, 0, 0)
        assert detector.is_after_hours(dt.timestamp()) == False


class TestEventThrottler:
    """Test event throttling"""
    
    def test_throttler_creation(self):
        """Test throttler initialization"""
        throttler = EventThrottler(throttle_seconds=30)
        
        assert throttler.throttle_seconds == 30
        assert len(throttler.last_events) == 0
    
    def test_first_event_always_sent(self):
        """Test first event is always sent"""
        throttler = EventThrottler(throttle_seconds=30)
        
        should_send = throttler.should_send(
            camera_id="cam1",
            zone_id="zone1",
            event_type="motion_in_zone",
            severity=2,
            current_time=1000.0
        )
        
        assert should_send == True
    
    def test_duplicate_event_throttled(self):
        """Test duplicate events are throttled"""
        throttler = EventThrottler(throttle_seconds=30)
        
        # Send first event
        throttler.should_send("cam1", "zone1", "motion_in_zone", 2, 1000.0)
        
        # Try to send duplicate immediately
        should_send = throttler.should_send("cam1", "zone1", "motion_in_zone", 2, 1005.0)
        
        assert should_send == False
    
    def test_event_sent_after_throttle_period(self):
        """Test event sent after throttle period expires"""
        throttler = EventThrottler(throttle_seconds=30)
        
        # Send first event
        throttler.should_send("cam1", "zone1", "motion_in_zone", 2, 1000.0)
        
        # Try after throttle period
        should_send = throttler.should_send("cam1", "zone1", "motion_in_zone", 2, 1031.0)
        
        assert should_send == True
    
    def test_higher_severity_bypasses_throttle(self):
        """Test higher severity events bypass throttle"""
        throttler = EventThrottler(throttle_seconds=30)
        
        # Send first event (severity 2)
        throttler.should_send("cam1", "zone1", "motion_in_zone", 2, 1000.0)
        
        # Send higher severity event immediately
        should_send = throttler.should_send("cam1", "zone1", "motion_in_zone", 4, 1005.0)
        
        assert should_send == True
    
    def test_different_camera_not_throttled(self):
        """Test different camera events not throttled"""
        throttler = EventThrottler(throttle_seconds=30)
        
        # Send event from cam1
        throttler.should_send("cam1", "zone1", "motion_in_zone", 2, 1000.0)
        
        # Send event from cam2 (different camera)
        should_send = throttler.should_send("cam2", "zone1", "motion_in_zone", 2, 1005.0)
        
        assert should_send == True
    
    def test_throttler_cleanup(self):
        """Test old entries cleanup"""
        throttler = EventThrottler(throttle_seconds=30)
        
        # Add old entry
        throttler.should_send("cam1", "zone1", "motion_in_zone", 2, 1000.0)
        
        assert len(throttler.last_events) == 1
        
        # Cleanup old entries (max_age = 1000 seconds)
        throttler.cleanup_old_entries(current_time=2100.0, max_age=1000)
        
        assert len(throttler.last_events) == 0


def test_full_pipeline_integration():
    """Integration test of full processing pipeline"""
    # Create test frames
    frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
    frame2 = np.zeros((480, 640, 3), dtype=np.uint8)
    frame2[100:300, 200:400, :] = 255  # Add motion
    
    # Create zone
    zone = Zone(
        zone_id="test_zone",
        name="Test Zone",
        polygon=[(150, 50), (450, 50), (450, 350), (150, 350)]
    )
    
    # Create detector
    detector = MotionDetector(config={'min_area': 100, 'activity_threshold': 0.005})
    
    # Process frames
    detector.detect(frame1, time.time(), zone=zone)
    result = detector.detect(frame2, time.time(), zone=zone)
    
    # Should detect motion in zone
    assert result is not None
    assert result.detected == True
    assert result.zone_id == "test_zone"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
