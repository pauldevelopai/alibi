"""
Traffic Light State Detection

Detects RED/GREEN/AMBER traffic light states using HSV color thresholding.
Uses temporal smoothing to avoid flicker.
"""

import cv2
import numpy as np
from enum import Enum
from typing import Tuple, Optional
from collections import deque


class LightState(str, Enum):
    """Traffic light states"""
    RED = "red"
    AMBER = "amber"
    GREEN = "green"
    UNKNOWN = "unknown"


class TrafficLightDetector:
    """
    Detects traffic light state from video frames using HSV color thresholding.
    
    Uses a smoothing window to avoid false positives from flickering lights.
    """
    
    def __init__(
        self,
        smoothing_window: int = 5,
        min_pixel_threshold: int = 10
    ):
        """
        Initialize traffic light detector.
        
        Args:
            smoothing_window: Number of frames to smooth over
            min_pixel_threshold: Minimum number of pixels to consider a color present
        """
        self.smoothing_window = smoothing_window
        self.min_pixel_threshold = min_pixel_threshold
        
        # History for temporal smoothing
        self.state_history: deque = deque(maxlen=smoothing_window)
        
        # HSV color ranges for each light state
        # RED: Two ranges (red wraps around in HSV)
        self.red_lower1 = np.array([0, 100, 100])
        self.red_upper1 = np.array([10, 255, 255])
        self.red_lower2 = np.array([160, 100, 100])
        self.red_upper2 = np.array([180, 255, 255])
        
        # AMBER/YELLOW
        self.amber_lower = np.array([15, 100, 100])
        self.amber_upper = np.array([35, 255, 255])
        
        # GREEN
        self.green_lower = np.array([40, 50, 50])
        self.green_upper = np.array([80, 255, 255])
    
    def detect(self, frame: np.ndarray, roi: Tuple[int, int, int, int]) -> Tuple[LightState, float]:
        """
        Detect traffic light state from frame ROI.
        
        Args:
            frame: Input frame (BGR)
            roi: Region of interest (x, y, width, height)
            
        Returns:
            Tuple of (state, confidence)
        """
        x, y, w, h = roi
        
        # Extract ROI
        light_roi = frame[y:y+h, x:x+w]
        
        if light_roi.size == 0:
            return LightState.UNKNOWN, 0.0
        
        # Convert to HSV
        hsv = cv2.cvtColor(light_roi, cv2.COLOR_BGR2HSV)
        
        # Count pixels for each color
        red_pixels = self._count_red_pixels(hsv)
        amber_pixels = self._count_amber_pixels(hsv)
        green_pixels = self._count_green_pixels(hsv)
        
        # Determine state based on pixel counts
        max_pixels = max(red_pixels, amber_pixels, green_pixels)
        
        if max_pixels < self.min_pixel_threshold:
            state = LightState.UNKNOWN
        elif red_pixels == max_pixels:
            state = LightState.RED
        elif amber_pixels == max_pixels:
            state = LightState.AMBER
        elif green_pixels == max_pixels:
            state = LightState.GREEN
        else:
            state = LightState.UNKNOWN
        
        # Add to history
        self.state_history.append(state)
        
        # Get smoothed state (most common in window)
        smoothed_state = self._get_smoothed_state()
        
        # Calculate confidence based on consistency
        confidence = self._calculate_confidence(smoothed_state)
        
        return smoothed_state, confidence
    
    def _count_red_pixels(self, hsv: np.ndarray) -> int:
        """Count red pixels in HSV image (red wraps around)"""
        mask1 = cv2.inRange(hsv, self.red_lower1, self.red_upper1)
        mask2 = cv2.inRange(hsv, self.red_lower2, self.red_upper2)
        mask = cv2.bitwise_or(mask1, mask2)
        return np.count_nonzero(mask)
    
    def _count_amber_pixels(self, hsv: np.ndarray) -> int:
        """Count amber/yellow pixels in HSV image"""
        mask = cv2.inRange(hsv, self.amber_lower, self.amber_upper)
        return np.count_nonzero(mask)
    
    def _count_green_pixels(self, hsv: np.ndarray) -> int:
        """Count green pixels in HSV image"""
        mask = cv2.inRange(hsv, self.green_lower, self.green_upper)
        return np.count_nonzero(mask)
    
    def _get_smoothed_state(self) -> LightState:
        """Get most common state in history window"""
        if not self.state_history:
            return LightState.UNKNOWN
        
        # Count occurrences
        counts = {}
        for state in self.state_history:
            counts[state] = counts.get(state, 0) + 1
        
        # Return most common (excluding UNKNOWN if possible)
        states_sorted = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        # Prefer non-UNKNOWN states
        for state, count in states_sorted:
            if state != LightState.UNKNOWN:
                return state
        
        return states_sorted[0][0]
    
    def _calculate_confidence(self, state: LightState) -> float:
        """Calculate confidence based on consistency in history"""
        if not self.state_history:
            return 0.0
        
        # Count how many frames match current state
        matches = sum(1 for s in self.state_history if s == state)
        confidence = matches / len(self.state_history)
        
        return confidence
    
    def reset(self):
        """Reset detector state"""
        self.state_history.clear()
