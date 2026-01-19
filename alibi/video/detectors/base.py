"""
Base Detector Interface

Abstract class for all detectors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
import numpy as np


@dataclass
class DetectionResult:
    """
    Result from a detector.
    """
    detected: bool
    event_type: str
    confidence: float  # 0.0 to 1.0
    severity: int  # 1 to 5
    metadata: Dict[str, Any]
    zone_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "detected": self.detected,
            "event_type": self.event_type,
            "confidence": self.confidence,
            "severity": self.severity,
            "metadata": self.metadata,
            "zone_id": self.zone_id,
        }


class Detector(ABC):
    """
    Abstract base class for all detectors.
    
    Detectors process frames and emit DetectionResult objects.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            name: Detector name
            config: Detector-specific configuration
        """
        self.name = name
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
    
    @abstractmethod
    def detect(self, frame: np.ndarray, timestamp: float, **kwargs) -> Optional[DetectionResult]:
        """
        Process frame and detect events.
        
        Args:
            frame: Input frame (numpy array)
            timestamp: Frame timestamp (Unix time)
            **kwargs: Additional detector-specific arguments
        
        Returns:
            DetectionResult if event detected, None otherwise
        """
        pass
    
    def reset(self):
        """
        Reset detector state.
        
        Called when stream reconnects or detector restarts.
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled})"
