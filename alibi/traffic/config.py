"""
Traffic Camera Configuration

Loads configuration for traffic enforcement cameras including:
- Traffic light ROI (region of interest)
- Stop line definition
- Intersection ROI for vehicle detection
"""

import json
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class TrafficCameraConfig:
    """Configuration for a traffic enforcement camera"""
    camera_id: str
    
    # Traffic light ROI: (x, y, width, height)
    traffic_light_roi: Tuple[int, int, int, int]
    
    # Stop line: list of (x, y) points defining the line
    # Can be 2 points (straight line) or multiple points (polygon)
    stop_line: List[Tuple[int, int]]
    
    # Intersection ROI for vehicle detection: (x, y, width, height)
    # If None, uses entire frame
    intersection_roi: Optional[Tuple[int, int, int, int]] = None
    
    # Direction of traffic (for line crossing detection)
    # "up", "down", "left", "right", or angle in degrees
    traffic_direction: str = "up"
    
    # Metadata
    location: str = ""
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrafficCameraConfig':
        """Create from dictionary"""
        return cls(
            camera_id=data["camera_id"],
            traffic_light_roi=tuple(data["traffic_light_roi"]),
            stop_line=[tuple(pt) for pt in data["stop_line"]],
            intersection_roi=tuple(data["intersection_roi"]) if data.get("intersection_roi") else None,
            traffic_direction=data.get("traffic_direction", "up"),
            location=data.get("location", ""),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "camera_id": self.camera_id,
            "traffic_light_roi": list(self.traffic_light_roi),
            "stop_line": [list(pt) for pt in self.stop_line],
            "intersection_roi": list(self.intersection_roi) if self.intersection_roi else None,
            "traffic_direction": self.traffic_direction,
            "location": self.location,
            "enabled": self.enabled,
            "metadata": self.metadata
        }


def load_traffic_cameras(config_path: str = "alibi/data/traffic_cameras.json") -> Dict[str, TrafficCameraConfig]:
    """
    Load traffic camera configurations from JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dict mapping camera_id to TrafficCameraConfig
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        print(f"[TrafficConfig] No config file found at {config_path}, creating default")
        _create_default_config(config_path)
    
    with open(config_file, 'r') as f:
        data = json.load(f)
    
    cameras = {}
    for camera_data in data.get("cameras", []):
        config = TrafficCameraConfig.from_dict(camera_data)
        cameras[config.camera_id] = config
    
    print(f"[TrafficConfig] Loaded {len(cameras)} traffic camera configs")
    return cameras


def _create_default_config(config_path: str):
    """Create default configuration file"""
    default_config = {
        "cameras": [
            {
                "camera_id": "traffic_cam_001",
                "location": "Main St & 1st Ave",
                "traffic_light_roi": [50, 50, 100, 150],  # x, y, w, h
                "stop_line": [[100, 400], [540, 400]],  # Two points defining line
                "intersection_roi": [0, 200, 640, 280],  # x, y, w, h
                "traffic_direction": "up",  # Vehicles moving upward
                "enabled": True,
                "metadata": {
                    "speed_limit_mph": 35,
                    "description": "Sample traffic camera configuration"
                }
            }
        ],
        "_readme": "Traffic camera configuration for red light enforcement. Each camera needs: traffic_light_roi (where the light is), stop_line (line vehicles should not cross on red), intersection_roi (area to detect vehicles)."
    }
    
    # Create directory if needed
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write config
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"[TrafficConfig] Created default config at {config_path}")


def save_traffic_cameras(cameras: Dict[str, TrafficCameraConfig], config_path: str = "alibi/data/traffic_cameras.json"):
    """
    Save traffic camera configurations to JSON file.
    
    Args:
        cameras: Dict mapping camera_id to TrafficCameraConfig
        config_path: Path to configuration file
    """
    data = {
        "cameras": [config.to_dict() for config in cameras.values()],
        "_readme": "Traffic camera configuration for red light enforcement."
    }
    
    with open(config_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"[TrafficConfig] Saved {len(cameras)} traffic camera configs to {config_path}")
