"""
Zone Management

Loads and manages polygon zones for area-based detection.
"""

import json
import numpy as np
import cv2
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Zone:
    """
    Polygon zone for area-based detection.
    """
    zone_id: str
    name: str
    polygon: List[Tuple[int, int]]  # List of (x, y) points
    enabled: bool = True
    metadata: Dict = None
    
    def __post_init__(self):
        """Initialize metadata if not provided"""
        if self.metadata is None:
            self.metadata = {}
    
    def create_mask(self, width: int, height: int) -> np.ndarray:
        """
        Create binary mask for this zone.
        
        Args:
            width: Frame width
            height: Frame height
        
        Returns:
            Binary mask (255 inside zone, 0 outside)
        """
        mask = np.zeros((height, width), dtype=np.uint8)
        
        points = np.array(self.polygon, dtype=np.int32)
        cv2.fillPoly(mask, [points], 255)
        
        return mask
    
    def contains_point(self, x: int, y: int) -> bool:
        """
        Check if point is inside zone.
        
        Args:
            x: X coordinate
            y: Y coordinate
        
        Returns:
            True if point is inside zone
        """
        points = np.array(self.polygon, dtype=np.int32)
        result = cv2.pointPolygonTest(points, (float(x), float(y)), False)
        return result >= 0
    
    # Alias for compatibility with different naming conventions
    def is_inside(self, x: int, y: int) -> bool:
        """Alias for contains_point"""
        return self.contains_point(x, y)
    
    def get_mask(self, frame_shape: Tuple[int, int]) -> np.ndarray:
        """
        Get zone mask for given frame shape.
        
        Args:
            frame_shape: (height, width) tuple
            
        Returns:
            Binary mask
        """
        height, width = frame_shape
        return self.create_mask(width, height)
    
    def get_bounding_box(self) -> Tuple[int, int, int, int]:
        """
        Get bounding box of zone.
        
        Returns:
            (x, y, width, height)
        """
        points = np.array(self.polygon)
        x_min, y_min = points.min(axis=0)
        x_max, y_max = points.max(axis=0)
        
        return int(x_min), int(y_min), int(x_max - x_min), int(y_max - y_min)


class ZoneManager:
    """
    Manages multiple zones loaded from configuration.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: Path to zones.json file
        """
        self.config_path = config_path
        self.zones: Dict[str, Zone] = {}
        
        if config_path:
            self.load_zones(config_path)
    
    def load_zones(self, config_path: str):
        """
        Load zones from JSON file.
        
        Format:
        {
          "zones": [
            {
              "zone_id": "zone_entrance",
              "name": "Main Entrance",
              "polygon": [[100, 100], [500, 100], [500, 400], [100, 400]],
              "enabled": true
            }
          ]
        }
        
        Args:
            config_path: Path to zones.json
        """
        path = Path(config_path)
        
        if not path.exists():
            print(f"[ZoneManager] Config file not found: {config_path}")
            print(f"[ZoneManager] Creating default zones file")
            self._create_default_zones(config_path)
            return
        
        with open(path, 'r') as f:
            config = json.load(f)
        
        for zone_data in config.get('zones', []):
            zone = Zone(
                zone_id=zone_data['zone_id'],
                name=zone_data['name'],
                polygon=[tuple(p) for p in zone_data['polygon']],
                enabled=zone_data.get('enabled', True),
                metadata=zone_data.get('metadata', {})
            )
            self.zones[zone.zone_id] = zone
        
        print(f"[ZoneManager] Loaded {len(self.zones)} zones from {config_path}")
    
    def _create_default_zones(self, config_path: str):
        """Create default zones configuration"""
        default_config = {
            "zones": [
                {
                    "zone_id": "zone_entrance",
                    "name": "Main Entrance",
                    "polygon": [[100, 100], [540, 100], [540, 380], [100, 380]],
                    "enabled": True
                },
                {
                    "zone_id": "zone_perimeter_east",
                    "name": "East Perimeter",
                    "polygon": [[400, 50], [600, 50], [600, 450], [400, 450]],
                    "enabled": True
                },
                {
                    "zone_id": "zone_parking_north",
                    "name": "North Parking",
                    "polygon": [[50, 50], [350, 50], [350, 250], [50, 250]],
                    "enabled": True
                },
            ]
        }
        
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        print(f"[ZoneManager] Created default zones file: {config_path}")
        self.load_zones(config_path)
    
    def get_zone(self, zone_id: str) -> Optional[Zone]:
        """Get zone by ID"""
        return self.zones.get(zone_id)
    
    def get_all_zones(self) -> List[Zone]:
        """Get all enabled zones"""
        return [z for z in self.zones.values() if z.enabled]
    
    def create_combined_mask(self, width: int, height: int) -> np.ndarray:
        """
        Create combined mask for all enabled zones.
        
        Args:
            width: Frame width
            height: Frame height
        
        Returns:
            Binary mask
        """
        mask = np.zeros((height, width), dtype=np.uint8)
        
        for zone in self.get_all_zones():
            zone_mask = zone.create_mask(width, height)
            mask = cv2.bitwise_or(mask, zone_mask)
        
        return mask
    
    def get_zones_at_point(self, x: int, y: int) -> List[Zone]:
        """
        Get all zones containing a point.
        
        Args:
            x: X coordinate
            y: Y coordinate
        
        Returns:
            List of zones containing point
        """
        return [z for z in self.get_all_zones() if z.contains_point(x, y)]
    
    def draw_zones(self, frame: np.ndarray, color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 2):
        """
        Draw zones on frame (for visualization).
        
        Args:
            frame: Input frame
            color: Line color (BGR)
            thickness: Line thickness
        
        Returns:
            Frame with zones drawn
        """
        output = frame.copy()
        
        for zone in self.get_all_zones():
            points = np.array(zone.polygon, dtype=np.int32)
            cv2.polylines(output, [points], True, color, thickness)
            
            # Draw zone label
            bbox = zone.get_bounding_box()
            label_pos = (bbox[0] + 5, bbox[1] + 20)
            cv2.putText(output, zone.name, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return output


def compute_zone_activity(mask: np.ndarray, motion_mask: np.ndarray) -> float:
    """
    Compute motion activity within a zone.
    
    Args:
        mask: Zone mask (255 inside, 0 outside)
        motion_mask: Motion detection mask (255 motion, 0 no motion)
    
    Returns:
        Activity ratio (0.0 to 1.0)
    """
    zone_area = np.count_nonzero(mask)
    
    if zone_area == 0:
        return 0.0
    
    # Motion within zone
    motion_in_zone = cv2.bitwise_and(motion_mask, mask)
    motion_pixels = np.count_nonzero(motion_in_zone)
    
    return motion_pixels / zone_area
