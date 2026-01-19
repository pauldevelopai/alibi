"""
Loitering Detector

Detects when objects/people remain in a restricted zone for extended periods.
Uses background subtraction + blob tracking to measure dwell time.
"""

import cv2
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from collections import defaultdict
from dataclasses import dataclass
import time

from alibi.video.detectors.base import Detector, DetectionResult
from alibi.video.zones import Zone


@dataclass
class TrackedBlob:
    """Represents a tracked blob in the scene"""
    centroid: Tuple[float, float]
    first_seen: float
    last_seen: float
    area: float


class LoiteringDetector(Detector):
    """
    Detects loitering using background subtraction and blob tracking.
    
    Tracks objects that remain in restricted zones for extended periods.
    Emits "loitering" events when dwell time exceeds threshold.
    """
    
    def __init__(
        self,
        name: str = "loitering",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Config options:
        - dwell_threshold_seconds: Time to trigger loitering (default 30)
        - min_blob_area: Minimum blob area in pixels (default 1000)
        - max_distance: Max distance to consider same blob (default 50 pixels)
        - bg_learning_rate: Background subtraction learning rate (default 0.01)
        - base_confidence: Base confidence score (default 0.80)
        - severity_scale: Severity increases per 30s (default 1)
        """
        super().__init__(name, config)
        
        # Configuration
        self.dwell_threshold = self.config.get('dwell_threshold_seconds', 30.0)
        self.min_blob_area = self.config.get('min_blob_area', 1000)
        self.max_distance = self.config.get('max_distance', 50.0)
        self.bg_learning_rate = self.config.get('bg_learning_rate', 0.01)
        self.base_confidence = self.config.get('base_confidence', 0.80)
        self.severity_scale = self.config.get('severity_scale', 1)
        
        # State
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=False
        )
        self.tracked_blobs: Dict[int, TrackedBlob] = {}
        self.next_blob_id = 0
        self.last_check_time = 0
        self.frame_count = 0
    
    def detect(
        self,
        frame: np.ndarray,
        timestamp: float,
        zone: Optional[Zone] = None,
        **kwargs
    ) -> Optional[DetectionResult]:
        """
        Detect loitering in frame.
        
        Args:
            frame: Input frame
            timestamp: Frame timestamp
            zone: Optional zone to check (must be restricted)
        
        Returns:
            DetectionResult if loitering detected, None otherwise
        """
        if not self.enabled:
            return None
        
        # Only check restricted zones
        if not zone or not zone.metadata.get('restricted', False):
            return None
        
        self.frame_count += 1
        
        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame, learningRate=self.bg_learning_rate)
        
        # Clean up mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        
        # Apply zone mask
        zone_mask = zone.get_mask(frame.shape[:2])
        fg_mask = cv2.bitwise_and(fg_mask, fg_mask, mask=zone_mask)
        
        # Find contours (blobs)
        contours, _ = cv2.findContours(
            fg_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Extract blob centroids
        current_centroids = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_blob_area:
                continue
            
            # Calculate centroid
            M = cv2.moments(contour)
            if M['m00'] != 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                
                # Check if centroid is inside zone polygon
                if zone.is_inside(cx, cy):
                    current_centroids.append((cx, cy, area))
        
        # Update tracked blobs
        self._update_tracked_blobs(current_centroids, timestamp)
        
        # Check for loitering
        return self._check_loitering(timestamp, zone.zone_id)
    
    def _update_tracked_blobs(
        self,
        current_centroids: List[Tuple[float, float, float]],
        timestamp: float
    ):
        """Update blob tracking with current frame detections"""
        # Match current centroids to tracked blobs
        matched_blob_ids = set()
        matched_centroid_indices = set()
        
        # Match existing blobs
        for blob_id, blob in self.tracked_blobs.items():
            best_match_idx = None
            best_distance = self.max_distance
            
            for idx, (cx, cy, area) in enumerate(current_centroids):
                if idx in matched_centroid_indices:
                    continue
                
                distance = np.sqrt(
                    (cx - blob.centroid[0])**2 +
                    (cy - blob.centroid[1])**2
                )
                
                if distance < best_distance:
                    best_distance = distance
                    best_match_idx = idx
            
            if best_match_idx is not None:
                # Update existing blob
                cx, cy, area = current_centroids[best_match_idx]
                blob.centroid = (cx, cy)
                blob.last_seen = timestamp
                blob.area = area
                matched_blob_ids.add(blob_id)
                matched_centroid_indices.add(best_match_idx)
        
        # Add new blobs for unmatched centroids
        for idx, (cx, cy, area) in enumerate(current_centroids):
            if idx not in matched_centroid_indices:
                self.tracked_blobs[self.next_blob_id] = TrackedBlob(
                    centroid=(cx, cy),
                    first_seen=timestamp,
                    last_seen=timestamp,
                    area=area
                )
                self.next_blob_id += 1
        
        # Remove stale blobs (not seen in 5 seconds)
        stale_ids = [
            blob_id for blob_id, blob in self.tracked_blobs.items()
            if timestamp - blob.last_seen > 5.0
        ]
        for blob_id in stale_ids:
            del self.tracked_blobs[blob_id]
    
    def _check_loitering(
        self,
        timestamp: float,
        zone_id: str
    ) -> Optional[DetectionResult]:
        """Check if any blobs have been loitering long enough"""
        if not self.tracked_blobs:
            return None
        
        # Check each tracked blob
        for blob_id, blob in self.tracked_blobs.items():
            dwell_time = timestamp - blob.first_seen
            
            if dwell_time >= self.dwell_threshold:
                # Calculate severity based on dwell time
                # Increases by severity_scale every 30 seconds
                severity = min(
                    5,
                    2 + int(dwell_time / 30.0) * self.severity_scale
                )
                
                # Calculate confidence (increases with dwell time, caps at 0.95)
                confidence = min(
                    0.95,
                    self.base_confidence + (dwell_time / 120.0) * 0.15
                )
                
                return DetectionResult(
                    detected=True,
                    event_type="loitering",
                    confidence=confidence,
                    severity=severity,
                    zone_id=zone_id,
                    metadata={
                        "dwell_seconds": round(dwell_time, 1),
                        "zone_restricted": True,
                        "blob_count": len(self.tracked_blobs),
                        "blob_area": int(blob.area),
                        "blob_position": {
                            "x": int(blob.centroid[0]),
                            "y": int(blob.centroid[1])
                        }
                    }
                )
        
        return None
    
    def reset(self):
        """Reset detector state"""
        self.tracked_blobs.clear()
        self.next_blob_id = 0
        self.frame_count = 0
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=False
        )
