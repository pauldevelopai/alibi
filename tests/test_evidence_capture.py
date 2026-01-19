"""
Test evidence capture (snapshot + clip) end-to-end.

Uses test_video.mp4 to trigger detections and verify evidence is captured.
"""

import pytest
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import cv2
import numpy as np

from alibi.video.evidence import (
    RollingBufferRecorder,
    save_snapshot,
    save_clip,
    extract_evidence,
    TimestampedFrame
)
from alibi.video.worker import VideoWorker, WorkerConfig, CameraConfig
from alibi.video.detectors.motion_detector import MotionDetector


class TestRollingBufferRecorder:
    """Test the rolling buffer recorder"""
    
    def test_add_frame(self):
        """Test adding frames to buffer"""
        recorder = RollingBufferRecorder(
            camera_id="test_cam",
            buffer_seconds=5.0,
            fps=2.0  # 2 fps = 10 frames for 5 seconds
        )
        
        # Create dummy frames
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add frames
        for i in range(15):
            recorder.add_frame(frame, time.time() + i * 0.5)
            time.sleep(0.01)  # Small delay
        
        # Should have max_frames (10) in buffer
        assert len(recorder.buffer) == recorder.max_frames
        assert recorder.frames_received == 15
    
    def test_get_frame_at_time(self):
        """Test retrieving frame at specific time"""
        recorder = RollingBufferRecorder(
            camera_id="test_cam",
            buffer_seconds=5.0,
            fps=1.0
        )
        
        # Add frames with different timestamps
        base_time = time.time()
        for i in range(5):
            frame = np.full((100, 100, 3), i * 50, dtype=np.uint8)
            recorder.add_frame(frame, base_time + i)
        
        # Get frame closest to base_time + 2.1 (should be frame at +2)
        result_frame = recorder.get_frame_at_time(base_time + 2.1)
        
        assert result_frame is not None
        # Frame at t+2 should have value ~100
        assert 90 < result_frame[0, 0, 0] < 110
    
    def test_get_frames_in_range(self):
        """Test retrieving frames in time range"""
        recorder = RollingBufferRecorder(
            camera_id="test_cam",
            buffer_seconds=10.0,
            fps=1.0
        )
        
        # Add 10 frames
        base_time = time.time()
        for i in range(10):
            frame = np.zeros((100, 100, 3), dtype=np.uint8)
            recorder.add_frame(frame, base_time + i)
        
        # Get frames from t+2 to t+6 (should be 5 frames)
        frames = recorder.get_frames_in_range(
            base_time + 2,
            base_time + 6
        )
        
        assert len(frames) == 5
        
        # Verify chronological order
        for i in range(len(frames) - 1):
            assert frames[i].timestamp < frames[i+1].timestamp


class TestEvidenceSaving:
    """Test saving snapshots and clips"""
    
    def test_save_snapshot(self, tmp_path):
        """Test saving a snapshot"""
        # Create dummy frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Save snapshot
        out_dir = tmp_path / "snapshots"
        rel_path = save_snapshot(
            frame=frame,
            out_dir=out_dir,
            camera_id="test_cam",
            timestamp=time.time()
        )
        
        # Verify file was created
        assert rel_path.startswith("snapshots/")
        assert rel_path.endswith(".jpg")
        
        full_path = tmp_path / rel_path
        assert full_path.exists()
        
        # Verify can be read back
        loaded = cv2.imread(str(full_path))
        assert loaded is not None
        assert loaded.shape == frame.shape
    
    def test_save_clip(self, tmp_path):
        """Test saving a video clip"""
        # Create dummy frames
        frames = []
        for i in range(10):
            frame = np.full((480, 640, 3), i * 25, dtype=np.uint8)
            frames.append(TimestampedFrame(
                frame=frame,
                timestamp=time.time() + i * 0.5
            ))
        
        # Save clip
        out_dir = tmp_path / "clips"
        rel_path = save_clip(
            frames=frames,
            out_dir=out_dir,
            camera_id="test_cam",
            ts_start=time.time(),
            ts_end=time.time() + 5,
            fps=2.0
        )
        
        # Verify file was created
        assert rel_path.startswith("clips/")
        assert rel_path.endswith(".mp4")
        
        full_path = tmp_path / rel_path
        assert full_path.exists()
        
        # Verify can be read back
        cap = cv2.VideoCapture(str(full_path))
        assert cap.isOpened()
        
        # Read first frame
        ret, frame = cap.read()
        assert ret
        assert frame is not None
        
        cap.release()
    
    def test_save_clip_empty_frames(self, tmp_path):
        """Test that save_clip raises error with no frames"""
        out_dir = tmp_path / "clips"
        
        with pytest.raises(ValueError, match="No frames to save"):
            save_clip(
                frames=[],
                out_dir=out_dir,
                camera_id="test_cam",
                ts_start=time.time(),
                ts_end=time.time() + 5,
                fps=1.0
            )


class TestExtractEvidence:
    """Test the extract_evidence function"""
    
    def test_extract_evidence_success(self, tmp_path):
        """Test successful evidence extraction"""
        # Create recorder with frames
        recorder = RollingBufferRecorder(
            camera_id="test_cam",
            buffer_seconds=20.0,
            fps=1.0
        )
        
        # Add frames around event time
        event_time = time.time()
        for i in range(-10, 11):  # -10s to +10s around event
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            recorder.add_frame(frame, event_time + i)
        
        # Extract evidence
        evidence_dir = tmp_path
        snapshot_path, clip_path = extract_evidence(
            recorder=recorder,
            event_timestamp=event_time,
            evidence_dir=evidence_dir,
            clip_before_seconds=5.0,
            clip_after_seconds=5.0,
            fps=1.0
        )
        
        # Verify both were created
        assert snapshot_path is not None
        assert clip_path is not None
        
        assert snapshot_path.startswith("snapshots/")
        assert clip_path.startswith("clips/")
        
        # Verify files exist
        assert (tmp_path / snapshot_path).exists()
        assert (tmp_path / clip_path).exists()
    
    def test_extract_evidence_empty_buffer(self, tmp_path):
        """Test extraction with empty buffer"""
        recorder = RollingBufferRecorder(
            camera_id="test_cam",
            buffer_seconds=10.0,
            fps=1.0
        )
        
        # No frames added
        evidence_dir = tmp_path
        snapshot_path, clip_path = extract_evidence(
            recorder=recorder,
            event_timestamp=time.time(),
            evidence_dir=evidence_dir,
            clip_before_seconds=5.0,
            clip_after_seconds=5.0,
            fps=1.0
        )
        
        # Both should be None (no frames available)
        assert snapshot_path is None
        assert clip_path is None


class TestEndToEndWithSyntheticFrames:
    """End-to-end test with synthetic frames"""
    
    def test_evidence_capture_integration(self, tmp_path):
        """
        Integration test: Create frames, add to recorder, extract evidence.
        This tests the complete evidence capture flow without needing video file.
        """
        # Create evidence recorder
        recorder = RollingBufferRecorder(
            camera_id="test_cam",
            buffer_seconds=10.0,
            fps=2.0
        )
        
        # Create synthetic frames with timestamps
        base_time = time.time()
        width, height = 640, 480
        
        # Add 20 frames (10 seconds at 2 fps)
        for i in range(20):
            # Create frame with varying content
            frame = np.full((height, width, 3), (i * 12) % 255, dtype=np.uint8)
            # Add a square that moves
            x = (i * 20) % (width - 100)
            y = height // 2 - 50
            cv2.rectangle(frame, (x, y), (x + 100, y + 100), (255, 255, 255), -1)
            
            recorder.add_frame(frame, base_time + i * 0.5)
        
        # Simulate event detection at midpoint (t+5s)
        event_timestamp = base_time + 5.0
        
        # Extract evidence
        evidence_dir = tmp_path
        snapshot_path, clip_path = extract_evidence(
            recorder=recorder,
            event_timestamp=event_timestamp,
            evidence_dir=evidence_dir,
            clip_before_seconds=3.0,
            clip_after_seconds=3.0,
            fps=2.0
        )
        
        # Verify snapshot was created
        assert snapshot_path is not None, "Snapshot was not created"
        assert snapshot_path.startswith("snapshots/")
        
        snapshot_file = evidence_dir / snapshot_path
        assert snapshot_file.exists(), f"Snapshot file not found: {snapshot_file}"
        
        # Verify it's a valid image
        img = cv2.imread(str(snapshot_file))
        assert img is not None, "Snapshot is not a valid image"
        assert img.shape == (height, width, 3)
        
        # Verify clip was created
        assert clip_path is not None, "Clip was not created"
        assert clip_path.startswith("clips/")
        
        clip_file = evidence_dir / clip_path
        assert clip_file.exists(), f"Clip file not found: {clip_file}"
        
        # Verify it's a valid video
        cap = cv2.VideoCapture(str(clip_file))
        assert cap.isOpened(), "Clip is not a valid video"
        
        # Count frames in clip (should be ~12 frames: 6 seconds at 2 fps)
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
        
        cap.release()
        
        # Should have multiple frames
        assert frame_count >= 5, f"Clip has too few frames: {frame_count}"
        
        print(f"\n✅ Evidence capture integration test passed!")
        print(f"   Snapshot: {snapshot_path}")
        print(f"   Clip: {clip_path} ({frame_count} frames)")
        print(f"   Snapshot size: {snapshot_file.stat().st_size} bytes")
        print(f"   Clip size: {clip_file.stat().st_size} bytes")


class TestEndToEndWithRealVideo:
    """Test with actual test_video.mp4 if available"""
    
    def test_evidence_extraction_manual(self, tmp_path):
        """
        Manual test of evidence extraction without full worker.
        Uses test_video.mp4 if available.
        """
        test_video = Path("alibi/data/test_video.mp4")
        if not test_video.exists():
            pytest.skip("test_video.mp4 not found")
        
        # Read a few frames from test video
        cap = cv2.VideoCapture(str(test_video))
        
        if not cap.isOpened():
            pytest.skip("Could not open test_video.mp4")
        
        # Create recorder and add frames
        recorder = RollingBufferRecorder(
            camera_id="test_cam",
            buffer_seconds=5.0,
            fps=2.0
        )
        
        base_time = time.time()
        frames_added = 0
        
        for i in range(20):  # Read up to 20 frames
            ret, frame = cap.read()
            if not ret:
                break
            
            recorder.add_frame(frame, base_time + i * 0.5)
            frames_added += 1
        
        cap.release()
        
        if frames_added < 5:
            pytest.skip(f"Not enough frames in test video ({frames_added})")
        
        # Extract evidence at midpoint
        event_time = base_time + frames_added * 0.25  # 25% through
        
        evidence_dir = tmp_path
        snapshot_path, clip_path = extract_evidence(
            recorder=recorder,
            event_timestamp=event_time,
            evidence_dir=evidence_dir,
            clip_before_seconds=2.0,
            clip_after_seconds=2.0,
            fps=2.0
        )
        
        # Verify snapshot was created
        assert snapshot_path is not None, "Snapshot not created"
        assert (tmp_path / snapshot_path).exists()
        
        # Clip may not be created if not enough frames
        if clip_path:
            assert (tmp_path / clip_path).exists()
        
        print(f"\n✅ Manual evidence extraction passed with real video!")
        print(f"   Frames used: {frames_added}")
        print(f"   Snapshot: {snapshot_path}")
        print(f"   Clip: {clip_path}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
