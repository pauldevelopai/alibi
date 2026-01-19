"""
Vehicle Detection

Detects vehicles in video frames for sightings indexing.
Reuses logic from traffic vehicle detection.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class DetectedVehicle:
    """A detected vehicle"""
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    confidence: float  # 0.0-1.0
    vehicle_crop: np.ndarray  # Cropped vehicle region


class VehicleDetector:
    """
    Detects vehicles using background subtraction.
    
    Simplified version of traffic vehicle detector.
    """
    
    def __init__(
        self,
        min_contour_area: int = 2000,
        max_contour_area: int = 100000
    ):
        """
        Initialize vehicle detector.
        
        Args:
            min_contour_area: Minimum contour area in pixels
            max_contour_area: Maximum contour area in pixels
        """
        self.min_contour_area = min_contour_area
        self.max_contour_area = max_contour_area
        
        # Background subtractor
        self.fgbg = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True
        )
    
    def detect(
        self,
        frame: np.ndarray,
        max_vehicles: int = 5
    ) -> List[DetectedVehicle]:
        """
        Detect vehicles in frame.
        
        Args:
            frame: Input frame (BGR)
            max_vehicles: Maximum number of vehicles to return
            
        Returns:
            List of DetectedVehicle objects
        """
        if frame is None or frame.size == 0:
            return []
        
        # Apply background subtraction
        fgmask = self.fgbg.apply(frame)
        
        # Remove shadows (marked as 127)
        fgmask[fgmask == 127] = 0
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_CLOSE, kernel)
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Extract vehicle detections
        detected_vehicles = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if self.min_contour_area <= area <= self.max_contour_area:
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by aspect ratio (reasonable vehicle shape)
                aspect_ratio = w / float(h) if h > 0 else 0
                
                if 0.5 <= aspect_ratio <= 4.0:  # Vehicles are typically wider than tall
                    # Extract vehicle crop
                    vehicle_crop = frame[y:y+h, x:x+w]
                    
                    if vehicle_crop.size > 0:
                        # Calculate confidence (simple: based on area)
                        confidence = min(1.0, area / 10000.0)
                        
                        detected_vehicles.append(DetectedVehicle(
                            bbox=(x, y, w, h),
                            confidence=confidence,
                            vehicle_crop=vehicle_crop.copy()
                        ))
            
            if len(detected_vehicles) >= max_vehicles:
                break
        
        # Sort by confidence
        detected_vehicles.sort(key=lambda v: v.confidence, reverse=True)
        
        return detected_vehicles[:max_vehicles]
    
    def reset(self):
        """Reset detector state"""
        self.fgbg = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True
        )
