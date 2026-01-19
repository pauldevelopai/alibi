"""
Frame Sampler

Samples frames at configurable rate from video stream.
"""

import time
import numpy as np
from typing import Generator, Optional
from dataclasses import dataclass


@dataclass
class SamplerConfig:
    """Frame sampler configuration"""
    target_fps: float = 1.0
    skip_similar: bool = True
    similarity_threshold: float = 0.95


class FrameSampler:
    """
    Samples frames at target FPS, optionally skipping similar frames.
    """
    
    def __init__(self, config: SamplerConfig):
        self.config = config
        self.last_frame_time = 0.0
        self.last_frame: Optional[np.ndarray] = None
        self.frames_processed = 0
        self.frames_sampled = 0
    
    @property
    def sample_interval(self) -> float:
        """Time interval between samples"""
        return 1.0 / self.config.target_fps
    
    def should_sample(self, current_time: Optional[float] = None) -> bool:
        """
        Check if enough time has passed to sample next frame.
        
        Args:
            current_time: Override current time (for testing)
        
        Returns:
            True if should sample
        """
        if current_time is None:
            current_time = time.time()
        
        # First frame should always be sampled
        if self.last_frame_time == 0.0:
            return True
        
        elapsed = current_time - self.last_frame_time
        return elapsed >= self.sample_interval
    
    def is_similar(self, frame: np.ndarray) -> bool:
        """
        Check if frame is similar to last sampled frame.
        
        Args:
            frame: Current frame
        
        Returns:
            True if similar to last frame
        """
        if not self.config.skip_similar or self.last_frame is None:
            return False
        
        # Resize both frames to same size for comparison
        if frame.shape != self.last_frame.shape:
            return False
        
        # Compute normalized correlation
        correlation = np.corrcoef(
            frame.flatten(),
            self.last_frame.flatten()
        )[0, 1]
        
        return correlation >= self.config.similarity_threshold
    
    def sample(
        self,
        frames: Generator[np.ndarray, None, None],
        current_time: Optional[float] = None
    ) -> Generator[np.ndarray, None, None]:
        """
        Sample frames from input generator.
        
        Args:
            frames: Input frame generator
            current_time: Override current time (for testing)
        
        Yields:
            Sampled frames
        """
        for frame in frames:
            self.frames_processed += 1
            
            if current_time is None:
                current_time = time.time()
            
            # Check if should sample
            if not self.should_sample(current_time):
                current_time = None  # Reset for next iteration
                continue
            
            # Check similarity
            if self.is_similar(frame):
                current_time = None
                continue
            
            # Sample this frame
            self.last_frame_time = current_time
            self.last_frame = frame.copy()
            self.frames_sampled += 1
            
            yield frame
            
            current_time = None  # Reset for next iteration
    
    def get_stats(self) -> dict:
        """Get sampling statistics"""
        sample_rate = 0.0
        if self.frames_processed > 0:
            sample_rate = self.frames_sampled / self.frames_processed
        
        return {
            "frames_processed": self.frames_processed,
            "frames_sampled": self.frames_sampled,
            "sample_rate": sample_rate,
            "target_fps": self.config.target_fps,
        }
    
    def reset_stats(self):
        """Reset statistics counters"""
        self.frames_processed = 0
        self.frames_sampled = 0


def downsample_frame(frame: np.ndarray, max_dim: int = 640) -> np.ndarray:
    """
    Downsample frame for processing efficiency.
    
    Args:
        frame: Input frame
        max_dim: Maximum dimension (width or height)
    
    Returns:
        Downsampled frame
    """
    height, width = frame.shape[:2]
    
    # Already small enough
    if max(height, width) <= max_dim:
        return frame
    
    # Calculate scale factor
    if width > height:
        scale = max_dim / width
    else:
        scale = max_dim / height
    
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    import cv2
    return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
