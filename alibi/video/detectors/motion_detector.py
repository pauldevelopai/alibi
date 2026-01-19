"""
Motion Detector

Frame differencing based motion detection with zone masking.
"""

import cv2
import numpy as np
from typing import Optional, Dict, Any
from alibi.video.detectors.base import Detector, DetectionResult
from alibi.video.zones import Zone


class MotionDetector(Detector):
    """
    Detects motion using frame differencing.
    
    Emits "motion_in_zone" events when motion exceeds threshold within a zone.
    """
    
    def __init__(
        self,
        name: str = "motion",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Config options:
        - threshold: Motion pixel threshold (0-255), default 25
        - min_area: Minimum motion area (pixels), default 500
        - blur_size: Gaussian blur kernel size, default 21
        - dilation_iterations: Morphological dilation iterations, default 2
        - activity_threshold: Zone activity ratio threshold, default 0.01
        - base_confidence: Base confidence score, default 0.75
        - base_severity: Base severity level, default 2
        """
        super().__init__(name, config)
        
        # Configuration
        self.threshold = self.config.get('threshold', 25)
        self.min_area = self.config.get('min_area', 500)
        self.blur_size = self.config.get('blur_size', 21)
        self.dilation_iterations = self.config.get('dilation_iterations', 2)
        self.activity_threshold = self.config.get('activity_threshold', 0.01)
        self.base_confidence = self.config.get('base_confidence', 0.75)
        self.base_severity = self.config.get('base_severity', 2)
        
        # State
        self.prev_frame: Optional[np.ndarray] = None
        self.background: Optional[np.ndarray] = None
        self.frame_count = 0
    
    def detect(
        self,
        frame: np.ndarray,
        timestamp: float,
        zone: Optional[Zone] = None,
        **kwargs
    ) -> Optional[DetectionResult]:
        """
        Detect motion in frame.
        
        Args:
            frame: Input frame
            timestamp: Frame timestamp
            zone: Optional zone for masking
        
        Returns:
            DetectionResult if motion detected, None otherwise
        """
        self.frame_count += 1
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (self.blur_size, self.blur_size), 0)
        
        # Initialize background
        if self.prev_frame is None:
            self.prev_frame = gray
            return None
        
        # Compute frame difference
        frame_diff = cv2.absdiff(self.prev_frame, gray)
        
        # Threshold
        _, thresh = cv2.threshold(frame_diff, self.threshold, 255, cv2.THRESH_BINARY)
        
        # Dilate to fill gaps
        kernel = np.ones((5, 5), np.uint8)
        thresh = cv2.dilate(thresh, kernel, iterations=self.dilation_iterations)
        
        # Apply zone mask if provided
        if zone:
            zone_mask = zone.create_mask(frame.shape[1], frame.shape[0])
            thresh = cv2.bitwise_and(thresh, zone_mask)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter by area
        significant_contours = [c for c in contours if cv2.contourArea(c) >= self.min_area]
        
        # Update previous frame
        self.prev_frame = gray
        
        # Check if motion detected
        if not significant_contours:
            return None
        
        # Calculate metrics
        total_motion_area = sum(cv2.contourArea(c) for c in significant_contours)
        frame_area = frame.shape[0] * frame.shape[1]
        
        if zone:
            zone_mask = zone.create_mask(frame.shape[1], frame.shape[0])
            zone_area = np.count_nonzero(zone_mask)
            motion_in_zone = cv2.bitwise_and(thresh, zone_mask)
            motion_pixels = np.count_nonzero(motion_in_zone)
            activity_ratio = motion_pixels / zone_area if zone_area > 0 else 0
        else:
            activity_ratio = total_motion_area / frame_area
        
        # Check activity threshold
        if activity_ratio < self.activity_threshold:
            return None
        
        # Calculate confidence and severity
        # Higher activity = higher confidence and severity
        confidence = min(self.base_confidence + (activity_ratio * 0.2), 1.0)
        
        if activity_ratio > 0.1:
            severity = 3
        elif activity_ratio > 0.05:
            severity = 2
        else:
            severity = 1
        
        # Get largest contour center
        largest_contour = max(significant_contours, key=cv2.contourArea)
        M = cv2.moments(largest_contour)
        if M["m00"] > 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = 0, 0
        
        # Build metadata
        metadata = {
            "motion_area": int(total_motion_area),
            "activity_ratio": float(activity_ratio),
            "contour_count": len(significant_contours),
            "center_x": cx,
            "center_y": cy,
        }
        
        return DetectionResult(
            detected=True,
            event_type="motion_in_zone",
            confidence=confidence,
            severity=severity,
            metadata=metadata,
            zone_id=zone.zone_id if zone else None,
        )
    
    def reset(self):
        """Reset detector state"""
        self.prev_frame = None
        self.background = None
        self.frame_count = 0
