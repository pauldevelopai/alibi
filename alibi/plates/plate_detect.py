"""
License Plate Detection

Detects license plate regions in images using OpenCV contour heuristics.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class DetectedPlate:
    """A detected license plate region"""
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    confidence: float  # 0.0-1.0
    plate_image: np.ndarray  # Cropped plate region
    
    def get_crop(self, padding: float = 0.1) -> np.ndarray:
        """Get plate crop with optional padding"""
        return self.plate_image


class PlateDetector:
    """
    Detects license plate regions using OpenCV.
    
    Uses edge detection + contour analysis + aspect ratio filtering.
    """
    
    def __init__(
        self,
        min_aspect_ratio: float = 2.0,
        max_aspect_ratio: float = 5.5,
        min_area: int = 1000,
        max_area: int = 30000
    ):
        """
        Initialize plate detector.
        
        Args:
            min_aspect_ratio: Minimum width/height ratio for plates
            max_aspect_ratio: Maximum width/height ratio for plates
            min_area: Minimum contour area in pixels
            max_area: Maximum contour area in pixels
        """
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio
        self.min_area = min_area
        self.max_area = max_area
    
    def detect(self, frame: np.ndarray, max_plates: int = 3) -> List[DetectedPlate]:
        """
        Detect license plates in frame.
        
        Args:
            frame: Input frame (BGR)
            max_plates: Maximum number of plates to return
            
        Returns:
            List of DetectedPlate objects
        """
        if frame is None or frame.size == 0:
            return []
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply bilateral filter to reduce noise while keeping edges sharp
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        
        # Edge detection
        edges = cv2.Canny(gray, 30, 200)
        
        # Find contours
        contours, _ = cv2.findContours(edges.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Sort contours by area (largest first)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]
        
        detected_plates = []
        
        for contour in contours:
            # Approximate contour to polygon
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate area and aspect ratio
            area = w * h
            aspect_ratio = w / float(h) if h > 0 else 0
            
            # Filter by area and aspect ratio
            if (self.min_area <= area <= self.max_area and
                self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio):
                
                # Additional check: look for rectangular-ish shape
                if len(approx) >= 4:  # At least 4 corners
                    # Extract plate region
                    plate_crop = frame[y:y+h, x:x+w]
                    
                    if plate_crop.size > 0:
                        # Calculate confidence based on how rectangular it is
                        confidence = self._calculate_confidence(approx, aspect_ratio, area)
                        
                        detected_plates.append(DetectedPlate(
                            bbox=(x, y, w, h),
                            confidence=confidence,
                            plate_image=plate_crop.copy()
                        ))
            
            if len(detected_plates) >= max_plates:
                break
        
        # Sort by confidence
        detected_plates.sort(key=lambda p: p.confidence, reverse=True)
        
        return detected_plates[:max_plates]
    
    def _calculate_confidence(
        self,
        approx: np.ndarray,
        aspect_ratio: float,
        area: int
    ) -> float:
        """
        Calculate detection confidence.
        
        Based on:
        - How close to ideal aspect ratio (3.0-4.0)
        - How rectangular the shape is
        - Size appropriateness
        """
        confidence = 0.5  # Base confidence
        
        # Aspect ratio score (ideal is 3.0-4.0)
        ideal_ratio = 3.5
        ratio_diff = abs(aspect_ratio - ideal_ratio)
        ratio_score = max(0, 1.0 - (ratio_diff / 2.0))
        confidence += ratio_score * 0.3
        
        # Rectangularity score (4 corners is ideal)
        corner_score = max(0, 1.0 - (abs(len(approx) - 4) / 4.0))
        confidence += corner_score * 0.2
        
        # Clip to [0, 1]
        confidence = np.clip(confidence, 0.0, 1.0)
        
        return confidence


def detect_plates_simple(frame: np.ndarray) -> List[DetectedPlate]:
    """
    Simple convenience function for plate detection.
    
    Args:
        frame: Input frame
        
    Returns:
        List of detected plates
    """
    detector = PlateDetector()
    return detector.detect(frame)
