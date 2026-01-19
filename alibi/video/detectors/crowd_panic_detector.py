"""
Crowd Panic Detector

Detects potential crowd panic situations using motion entropy and distribution changes.
Analyzes sudden shifts in crowd dynamics that may indicate panic or stampede.
"""

import cv2
import numpy as np
from typing import Optional, Dict, Any
from collections import deque
from scipy.stats import entropy

from alibi.video.detectors.base import Detector, DetectionResult
from alibi.video.zones import Zone


class CrowdPanicDetector(Detector):
    """
    Detects crowd panic using motion entropy and spatial distribution changes.
    
    Analyzes:
    - Motion entropy (disorder/chaos in movement patterns)
    - Spatial distribution changes (sudden shifts in crowd positioning)
    - Rate of change (how quickly patterns are changing)
    
    Conservative thresholds for high-stakes scenarios.
    Emits "crowd_panic" events when indicators suggest panic behavior.
    """
    
    def __init__(
        self,
        name: str = "crowd_panic",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Config options:
        - entropy_threshold: Minimum entropy for panic (default 2.5)
        - change_rate_threshold: Minimum change rate (default 0.5)
        - grid_size: Grid size for spatial analysis (default 8x8)
        - window_frames: Number of frames to analyze (default 8)
        - bg_learning_rate: Background subtraction rate (default 0.02)
        - base_confidence: Base confidence score (default 0.75)
        - base_severity: Base severity level (default 4)
        """
        super().__init__(name, config)
        
        # Configuration
        self.entropy_threshold = self.config.get('entropy_threshold', 2.5)
        self.change_rate_threshold = self.config.get('change_rate_threshold', 0.5)
        self.grid_size = self.config.get('grid_size', (8, 8))
        self.window_frames = self.config.get('window_frames', 8)
        self.bg_learning_rate = self.config.get('bg_learning_rate', 0.02)
        self.base_confidence = self.config.get('base_confidence', 0.75)
        self.base_severity = self.config.get('base_severity', 4)
        
        # State
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=200,
            varThreshold=16,
            detectShadows=False
        )
        self.prev_distribution: Optional[np.ndarray] = None
        self.distribution_history: deque = deque(maxlen=self.window_frames)
        self.entropy_history: deque = deque(maxlen=self.window_frames)
        self.frame_count = 0
    
    def detect(
        self,
        frame: np.ndarray,
        timestamp: float,
        zone: Optional[Zone] = None,
        **kwargs
    ) -> Optional[DetectionResult]:
        """
        Detect crowd panic patterns in frame.
        
        Args:
            frame: Input frame
            timestamp: Frame timestamp
            zone: Optional zone to check
        
        Returns:
            DetectionResult if panic detected, None otherwise
        """
        if not self.enabled:
            return None
        
        self.frame_count += 1
        
        # Apply background subtraction to get foreground (people/crowd)
        fg_mask = self.bg_subtractor.apply(frame, learningRate=self.bg_learning_rate)
        
        # Clean up mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        
        # Apply zone mask if provided
        if zone:
            zone_mask = zone.get_mask(frame.shape[:2])
            fg_mask = cv2.bitwise_and(fg_mask, fg_mask, mask=zone_mask)
        
        # Calculate spatial distribution of foreground
        distribution = self._calculate_spatial_distribution(fg_mask)
        
        # Calculate motion entropy
        motion_entropy = self._calculate_motion_entropy(fg_mask)
        
        # Store in history
        self.distribution_history.append(distribution)
        self.entropy_history.append(motion_entropy)
        
        # Update previous distribution
        self.prev_distribution = distribution.copy()
        
        # Need enough history for analysis
        if len(self.distribution_history) < self.window_frames:
            return None
        
        # Analyze for panic indicators
        result = self._analyze_panic_indicators(zone)
        
        return result
    
    def _calculate_spatial_distribution(self, fg_mask: np.ndarray) -> np.ndarray:
        """
        Calculate spatial distribution of foreground pixels on a grid.
        
        Returns normalized distribution vector.
        """
        h, w = fg_mask.shape
        grid_h, grid_w = self.grid_size
        
        # Calculate cell dimensions
        cell_h = h // grid_h
        cell_w = w // grid_w
        
        # Count foreground pixels in each grid cell
        distribution = np.zeros(grid_h * grid_w)
        
        for i in range(grid_h):
            for j in range(grid_w):
                y_start = i * cell_h
                y_end = (i + 1) * cell_h if i < grid_h - 1 else h
                x_start = j * cell_w
                x_end = (j + 1) * cell_w if j < grid_w - 1 else w
                
                cell = fg_mask[y_start:y_end, x_start:x_end]
                distribution[i * grid_w + j] = np.sum(cell > 0)
        
        # Normalize to probability distribution
        total = np.sum(distribution)
        if total > 0:
            distribution = distribution / total
        else:
            distribution = np.ones_like(distribution) / len(distribution)
        
        return distribution
    
    def _calculate_motion_entropy(self, fg_mask: np.ndarray) -> float:
        """
        Calculate entropy of motion distribution.
        
        Higher entropy = more chaotic/disordered motion.
        """
        # Calculate histogram of foreground pixel intensities
        hist = cv2.calcHist([fg_mask], [0], None, [16], [0, 256])
        hist = hist.flatten()
        
        # Normalize to probability distribution
        hist = hist / (np.sum(hist) + 1e-7)
        
        # Calculate entropy
        return entropy(hist + 1e-10)  # Add small constant to avoid log(0)
    
    def _analyze_panic_indicators(
        self,
        zone: Optional[Zone]
    ) -> Optional[DetectionResult]:
        """Analyze accumulated data for panic indicators"""
        # 1. Check motion entropy (chaos level)
        entropy_array = np.array(self.entropy_history)
        avg_entropy = np.mean(entropy_array)
        max_entropy = np.max(entropy_array)
        
        if avg_entropy < self.entropy_threshold:
            return None  # Not chaotic enough
        
        # 2. Calculate distribution change rate
        if len(self.distribution_history) < 2:
            return None
        
        # Calculate frame-to-frame distribution changes
        changes = []
        for i in range(1, len(self.distribution_history)):
            prev_dist = self.distribution_history[i-1]
            curr_dist = self.distribution_history[i]
            
            # KL divergence or simple L2 distance
            change = np.linalg.norm(curr_dist - prev_dist)
            changes.append(change)
        
        avg_change_rate = np.mean(changes)
        max_change_rate = np.max(changes)
        
        if avg_change_rate < self.change_rate_threshold:
            return None  # Not changing rapidly enough
        
        # 3. Check for sudden spike in change rate (key panic indicator)
        recent_changes = changes[-3:]  # Last 3 frames
        earlier_changes = changes[:-3] if len(changes) > 3 else changes
        
        recent_avg = np.mean(recent_changes)
        earlier_avg = np.mean(earlier_changes) if earlier_changes else 0
        
        change_acceleration = recent_avg / (earlier_avg + 0.1)
        
        # Panic indicators present
        # Calculate confidence based on indicator strength
        confidence = self.base_confidence
        
        # Boost confidence for stronger indicators
        if avg_entropy > self.entropy_threshold * 1.2:
            confidence += 0.08
        if change_acceleration > 2.0:
            confidence += 0.10
        if max_change_rate > self.change_rate_threshold * 2.0:
            confidence += 0.05
        
        confidence = min(0.95, confidence)
        
        # Severity is high for panic (default 4-5)
        severity = self.base_severity
        if avg_entropy > 3.0 and change_acceleration > 2.5:
            severity = 5
        
        return DetectionResult(
            detected=True,
            event_type="crowd_panic",
            confidence=confidence,
            severity=severity,
            zone_id=zone.zone_id if zone else None,
            metadata={
                "entropy_score": round(avg_entropy, 3),
                "max_entropy": round(max_entropy, 3),
                "change_rate": round(avg_change_rate, 3),
                "max_change_rate": round(max_change_rate, 3),
                "change_acceleration": round(change_acceleration, 2),
                "detection_basis": "entropy_and_distribution_analysis"
            }
        )
    
    def reset(self):
        """Reset detector state"""
        self.prev_distribution = None
        self.distribution_history.clear()
        self.entropy_history.clear()
        self.frame_count = 0
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=200,
            varThreshold=16,
            detectShadows=False
        )
