"""
Aggression Detector

Detects potential aggression using motion energy patterns and rapid changes.
Uses proxy indicators: high motion + rapid variability + spatial clustering.
"""

import cv2
import numpy as np
from typing import Optional, Dict, Any, List
from collections import deque

from alibi.video.detectors.base import Detector, DetectionResult
from alibi.video.zones import Zone


class AggressionDetector(Detector):
    """
    Detects potential aggression using motion-based proxies.
    
    Analyzes:
    - Motion energy (intensity of movement)
    - Motion variability (rapid changes in motion patterns)
    - Spatial clustering (concentrated activity)
    
    Conservative thresholds to minimize false positives.
    Emits "aggression" events when patterns match aggressive behavior.
    """
    
    def __init__(
        self,
        name: str = "aggression",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Config options:
        - motion_threshold: Minimum motion energy (default 5000)
        - variability_threshold: Minimum variability score (default 0.4)
        - clustering_threshold: Spatial concentration threshold (default 0.3)
        - window_frames: Number of frames to analyze (default 10)
        - blur_size: Gaussian blur kernel size (default 21)
        - base_confidence: Base confidence score (default 0.70)
        - base_severity: Base severity level (default 3)
        """
        super().__init__(name, config)
        
        # Configuration
        self.motion_threshold = self.config.get('motion_threshold', 5000)
        self.variability_threshold = self.config.get('variability_threshold', 0.4)
        self.clustering_threshold = self.config.get('clustering_threshold', 0.3)
        self.window_frames = self.config.get('window_frames', 10)
        self.blur_size = self.config.get('blur_size', 21)
        self.base_confidence = self.config.get('base_confidence', 0.70)
        self.base_severity = self.config.get('base_severity', 3)
        
        # State
        self.prev_frame: Optional[np.ndarray] = None
        self.motion_history: deque = deque(maxlen=self.window_frames)
        self.frame_count = 0
    
    def detect(
        self,
        frame: np.ndarray,
        timestamp: float,
        zone: Optional[Zone] = None,
        **kwargs
    ) -> Optional[DetectionResult]:
        """
        Detect aggression patterns in frame.
        
        Args:
            frame: Input frame
            timestamp: Frame timestamp
            zone: Optional zone to check
        
        Returns:
            DetectionResult if aggression detected, None otherwise
        """
        if not self.enabled:
            return None
        
        self.frame_count += 1
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (self.blur_size, self.blur_size), 0)
        
        # Need previous frame for comparison
        if self.prev_frame is None:
            self.prev_frame = gray
            return None
        
        # Calculate frame difference
        frame_diff = cv2.absdiff(self.prev_frame, gray)
        
        # Apply zone mask if provided
        if zone:
            zone_mask = zone.get_mask(frame.shape[:2])
            frame_diff = cv2.bitwise_and(frame_diff, frame_diff, mask=zone_mask)
        
        # Threshold to get motion pixels
        _, motion_mask = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
        
        # Calculate motion energy (sum of motion pixels)
        motion_energy = np.sum(motion_mask) / 255.0
        
        # Store in history
        self.motion_history.append(motion_energy)
        
        # Update previous frame
        self.prev_frame = gray.copy()
        
        # Need enough history for analysis
        if len(self.motion_history) < self.window_frames:
            return None
        
        # Analyze motion patterns
        result = self._analyze_motion_patterns(motion_mask, zone)
        
        return result
    
    def _analyze_motion_patterns(
        self,
        motion_mask: np.ndarray,
        zone: Optional[Zone]
    ) -> Optional[DetectionResult]:
        """Analyze motion patterns for aggression indicators"""
        # 1. Check motion energy (intensity of movement)
        motion_array = np.array(self.motion_history)
        avg_motion = np.mean(motion_array)
        
        if avg_motion < self.motion_threshold:
            return None  # Not enough motion
        
        # 2. Calculate motion variability (rapid changes)
        motion_std = np.std(motion_array)
        motion_range = np.max(motion_array) - np.min(motion_array)
        
        # Normalize variability (0-1 range)
        variability_score = min(1.0, (motion_std / (avg_motion + 1.0)))
        
        if variability_score < self.variability_threshold:
            return None  # Motion not erratic enough
        
        # 3. Check spatial clustering (concentrated activity)
        clustering_score = self._calculate_clustering(motion_mask)
        
        if clustering_score < self.clustering_threshold:
            return None  # Motion too dispersed
        
        # All indicators present - potential aggression
        # Calculate confidence based on how strong indicators are
        confidence = self.base_confidence
        
        # Boost confidence for stronger indicators
        if variability_score > 0.6:
            confidence += 0.1
        if clustering_score > 0.5:
            confidence += 0.1
        if avg_motion > self.motion_threshold * 1.5:
            confidence += 0.05
        
        confidence = min(0.95, confidence)
        
        # Calculate severity based on indicator strength
        severity = self.base_severity
        if variability_score > 0.7 and clustering_score > 0.6:
            severity = min(5, severity + 1)
        
        return DetectionResult(
            detected=True,
            event_type="aggression",
            confidence=confidence,
            severity=severity,
            zone_id=zone.zone_id if zone else None,
            metadata={
                "motion_energy": round(avg_motion, 1),
                "variability_score": round(variability_score, 3),
                "clustering_score": round(clustering_score, 3),
                "motion_range": round(motion_range, 1),
                "detection_basis": "motion_pattern_analysis"
            }
        )
    
    def _calculate_clustering(self, motion_mask: np.ndarray) -> float:
        """
        Calculate spatial clustering of motion.
        
        Returns value 0-1 where 1 = highly concentrated motion
        """
        # Find motion pixels
        motion_pixels = np.argwhere(motion_mask > 0)
        
        if len(motion_pixels) < 10:
            return 0.0
        
        # Calculate center of motion
        center = np.mean(motion_pixels, axis=0)
        
        # Calculate distances from center
        distances = np.linalg.norm(motion_pixels - center, axis=1)
        avg_distance = np.mean(distances)
        
        # Calculate spatial concentration
        # Lower average distance = higher clustering
        frame_diagonal = np.sqrt(motion_mask.shape[0]**2 + motion_mask.shape[1]**2)
        
        # Normalize (inverse of distance ratio)
        clustering = 1.0 - min(1.0, (avg_distance / (frame_diagonal * 0.25)))
        
        return clustering
    
    def reset(self):
        """Reset detector state"""
        self.prev_frame = None
        self.motion_history.clear()
        self.frame_count = 0
