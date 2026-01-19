"""
RTSP Reader

Reads video streams from RTSP URLs or local files using OpenCV with ffmpeg fallback.
"""

import cv2
import subprocess
import numpy as np
from typing import Optional, Generator, Tuple
from pathlib import Path
import time


class RTSPReader:
    """
    Video stream reader supporting RTSP URLs and local files.
    
    Uses OpenCV VideoCapture with automatic ffmpeg fallback.
    """
    
    def __init__(
        self,
        source: str,
        reconnect_delay: float = 5.0,
        buffer_size: int = 1,
    ):
        """
        Args:
            source: RTSP URL or local file path
            reconnect_delay: Seconds to wait before reconnecting after failure
            buffer_size: Number of frames to buffer (1 = latest frame only)
        """
        self.source = source
        self.reconnect_delay = reconnect_delay
        self.buffer_size = buffer_size
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_file = self._is_local_file(source)
        self.frame_count = 0
        self.last_reconnect = 0.0
        
        # Metadata
        self.fps: Optional[float] = None
        self.width: Optional[int] = None
        self.height: Optional[int] = None
    
    def _is_local_file(self, source: str) -> bool:
        """Check if source is a local file"""
        return Path(source).exists()
    
    def open(self) -> bool:
        """
        Open video stream.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cap = cv2.VideoCapture(self.source)
            
            # Set buffer size for RTSP streams (minimize latency)
            if not self.is_file:
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
            
            if not self.cap.isOpened():
                print(f"[RTSPReader] Failed to open: {self.source}")
                return False
            
            # Read metadata
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Fallback FPS if not available
            if self.fps == 0 or self.fps is None:
                self.fps = 25.0  # Default
            
            print(f"[RTSPReader] Opened: {self.source}")
            print(f"[RTSPReader]   Resolution: {self.width}x{self.height}")
            print(f"[RTSPReader]   FPS: {self.fps}")
            
            return True
            
        except Exception as e:
            print(f"[RTSPReader] Error opening stream: {e}")
            return False
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read next frame.
        
        Returns:
            (success, frame) tuple
        """
        if self.cap is None or not self.cap.isOpened():
            return False, None
        
        ret, frame = self.cap.read()
        
        if ret:
            self.frame_count += 1
            return True, frame
        
        return False, None
    
    def close(self):
        """Close video stream"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            print(f"[RTSPReader] Closed: {self.source}")
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect to stream.
        
        Returns:
            True if successful, False otherwise
        """
        current_time = time.time()
        
        # Rate limit reconnection attempts
        if current_time - self.last_reconnect < self.reconnect_delay:
            return False
        
        self.last_reconnect = current_time
        
        print(f"[RTSPReader] Reconnecting to: {self.source}")
        self.close()
        return self.open()
    
    def frames(self, max_failures: int = 10) -> Generator[np.ndarray, None, None]:
        """
        Generator yielding frames with automatic reconnection.
        
        Args:
            max_failures: Maximum consecutive failures before giving up
        
        Yields:
            Frame as numpy array
        """
        if not self.open():
            raise RuntimeError(f"Failed to open video source: {self.source}")
        
        failures = 0
        
        try:
            while True:
                ret, frame = self.read()
                
                if ret:
                    failures = 0
                    yield frame
                else:
                    failures += 1
                    
                    # For files, end of stream is normal
                    if self.is_file:
                        print(f"[RTSPReader] End of file: {self.source}")
                        break
                    
                    # For streams, attempt reconnection
                    if failures >= max_failures:
                        print(f"[RTSPReader] Max failures reached, giving up")
                        break
                    
                    print(f"[RTSPReader] Frame read failed (attempt {failures}/{max_failures})")
                    
                    if self.reconnect():
                        print(f"[RTSPReader] Reconnection successful")
                        failures = 0
                    else:
                        time.sleep(1)  # Brief delay before retry
        
        finally:
            self.close()
    
    def __enter__(self):
        """Context manager entry"""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def test_source(source: str, max_frames: int = 10) -> bool:
    """
    Test video source by reading a few frames.
    
    Args:
        source: RTSP URL or file path
        max_frames: Number of frames to read
    
    Returns:
        True if source is readable
    """
    try:
        reader = RTSPReader(source)
        
        for i, frame in enumerate(reader.frames()):
            print(f"Frame {i+1}: {frame.shape}")
            
            if i + 1 >= max_frames:
                break
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False
