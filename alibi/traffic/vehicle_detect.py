"""
Vehicle Detection

Simple vehicle detection using background subtraction and contour tracking.
Tracks vehicle centroids and bounding boxes within intersection ROI.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import time


@dataclass
class TrackedVehicle:
    """A tracked vehicle in the scene"""
    vehicle_id: int
    centroid: Tuple[int, int]  # (x, y)
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    first_seen: float  # timestamp
    last_seen: float  # timestamp
    trajectory: List[Tuple[int, int]]  # List of centroids over time
    
    def update(self, centroid: Tuple[int, int], bbox: Tuple[int, int, int, int], timestamp: float):
        """Update vehicle position"""
        self.centroid = centroid
        self.bbox = bbox
        self.last_seen = timestamp
        self.trajectory.append(centroid)


class VehicleDetector:
    """
    Detects and tracks vehicles using background subtraction.
    
    Simple baseline approach - can be replaced with ML-based detector later.
    """
    
    def __init__(
        self,
        min_contour_area: int = 1000,
        max_contour_area: int = 50000,
        max_tracking_distance: int = 100,
        max_disappeared_frames: int = 10
    ):
        """
        Initialize vehicle detector.
        
        Args:
            min_contour_area: Minimum contour area to consider as vehicle
            max_contour_area: Maximum contour area to consider as vehicle
            max_tracking_distance: Maximum distance to associate detections with tracked vehicles
            max_disappeared_frames: Maximum frames vehicle can be missing before removal
        """
        self.min_contour_area = min_contour_area
        self.max_contour_area = max_contour_area
        self.max_tracking_distance = max_tracking_distance
        self.max_disappeared_frames = max_disappeared_frames
        
        # Background subtractor
        self.fgbg = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True
        )
        
        # Tracked vehicles
        self.tracked_vehicles: Dict[int, TrackedVehicle] = {}
        self.next_vehicle_id = 0
        self.disappeared_counts: Dict[int, int] = {}
    
    def detect(
        self,
        frame: np.ndarray,
        timestamp: float,
        roi: Optional[Tuple[int, int, int, int]] = None
    ) -> List[TrackedVehicle]:
        """
        Detect vehicles in frame.
        
        Args:
            frame: Input frame (BGR)
            timestamp: Current timestamp
            roi: Optional region of interest (x, y, width, height)
            
        Returns:
            List of currently tracked vehicles
        """
        # Apply ROI if specified
        if roi:
            x, y, w, h = roi
            frame_roi = frame[y:y+h, x:x+w]
            roi_offset = (x, y)
        else:
            frame_roi = frame
            roi_offset = (0, 0)
        
        # Apply background subtraction
        fgmask = self.fgbg.apply(frame_roi)
        
        # Remove shadows (they're marked as 127 in MOG2)
        fgmask[fgmask == 127] = 0
        
        # Apply morphological operations to clean up mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_CLOSE, kernel)
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Extract vehicle detections
        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if self.min_contour_area <= area <= self.max_contour_area:
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                
                # Calculate centroid
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                else:
                    cx = x + w // 2
                    cy = y + h // 2
                
                # Adjust for ROI offset
                cx += roi_offset[0]
                cy += roi_offset[1]
                x += roi_offset[0]
                y += roi_offset[1]
                
                detections.append({
                    'centroid': (cx, cy),
                    'bbox': (x, y, w, h)
                })
        
        # Update tracked vehicles
        self._update_tracking(detections, timestamp)
        
        # Return list of active vehicles
        return list(self.tracked_vehicles.values())
    
    def _update_tracking(self, detections: List[Dict], timestamp: float):
        """
        Update tracked vehicles with new detections.
        
        Uses simple centroid-based tracking.
        """
        # Mark all vehicles as not seen this frame
        for vehicle_id in list(self.tracked_vehicles.keys()):
            if vehicle_id not in self.disappeared_counts:
                self.disappeared_counts[vehicle_id] = 0
        
        # If no detections, increment disappeared counts
        if not detections:
            for vehicle_id in list(self.tracked_vehicles.keys()):
                self.disappeared_counts[vehicle_id] += 1
                
                # Remove vehicles that have been gone too long
                if self.disappeared_counts[vehicle_id] > self.max_disappeared_frames:
                    del self.tracked_vehicles[vehicle_id]
                    del self.disappeared_counts[vehicle_id]
            return
        
        # If no tracked vehicles, create new ones for all detections
        if not self.tracked_vehicles:
            for detection in detections:
                self._register_vehicle(detection, timestamp)
            return
        
        # Match detections to existing vehicles
        vehicle_ids = list(self.tracked_vehicles.keys())
        vehicle_centroids = [v.centroid for v in self.tracked_vehicles.values()]
        
        matched_detections = set()
        matched_vehicles = set()
        
        # Simple nearest-neighbor matching
        for detection in detections:
            det_centroid = detection['centroid']
            
            min_dist = float('inf')
            best_vehicle_idx = None
            
            for idx, vehicle_centroid in enumerate(vehicle_centroids):
                dist = np.linalg.norm(np.array(det_centroid) - np.array(vehicle_centroid))
                
                if dist < min_dist and dist < self.max_tracking_distance:
                    min_dist = dist
                    best_vehicle_idx = idx
            
            if best_vehicle_idx is not None:
                vehicle_id = vehicle_ids[best_vehicle_idx]
                
                # Update vehicle
                self.tracked_vehicles[vehicle_id].update(
                    detection['centroid'],
                    detection['bbox'],
                    timestamp
                )
                
                # Reset disappeared count
                self.disappeared_counts[vehicle_id] = 0
                
                matched_detections.add(detections.index(detection))
                matched_vehicles.add(vehicle_id)
        
        # Register new vehicles for unmatched detections
        for idx, detection in enumerate(detections):
            if idx not in matched_detections:
                self._register_vehicle(detection, timestamp)
        
        # Increment disappeared count for unmatched vehicles
        for vehicle_id in vehicle_ids:
            if vehicle_id not in matched_vehicles:
                self.disappeared_counts[vehicle_id] += 1
                
                # Remove if disappeared too long
                if self.disappeared_counts[vehicle_id] > self.max_disappeared_frames:
                    del self.tracked_vehicles[vehicle_id]
                    del self.disappeared_counts[vehicle_id]
    
    def _register_vehicle(self, detection: Dict, timestamp: float):
        """Register a new vehicle"""
        vehicle_id = self.next_vehicle_id
        self.next_vehicle_id += 1
        
        vehicle = TrackedVehicle(
            vehicle_id=vehicle_id,
            centroid=detection['centroid'],
            bbox=detection['bbox'],
            first_seen=timestamp,
            last_seen=timestamp,
            trajectory=[detection['centroid']]
        )
        
        self.tracked_vehicles[vehicle_id] = vehicle
        self.disappeared_counts[vehicle_id] = 0
    
    def reset(self):
        """Reset detector state"""
        self.tracked_vehicles.clear()
        self.disappeared_counts.clear()
        self.next_vehicle_id = 0
        self.fgbg = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True
        )
