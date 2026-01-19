#!/usr/bin/env python3
"""
Create a test video with motion for Alibi video worker testing.
"""

import cv2
import numpy as np
from pathlib import Path


def create_test_video(output_path: str, duration_seconds: int = 10, fps: int = 10):
    """
    Create a test video with moving objects.
    
    Args:
        output_path: Output file path
        duration_seconds: Video duration in seconds
        fps: Frames per second
    """
    width, height = 640, 480
    total_frames = duration_seconds * fps
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    print(f"Creating test video: {output_path}")
    print(f"  Duration: {duration_seconds}s")
    print(f"  FPS: {fps}")
    print(f"  Frames: {total_frames}")
    
    for frame_num in range(total_frames):
        # Create black background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Calculate time
        t = frame_num / fps
        
        # Add moving box (simulates person/vehicle)
        if t > 2:  # Start motion after 2 seconds
            # Box moves left to right
            x = int(50 + (t - 2) * 50)
            y = 200
            
            if x < width - 100:
                cv2.rectangle(frame, (x, y), (x + 80, y + 120), (255, 255, 255), -1)
                
                # Add some noise for realism
                noise_region = frame[y:y+120, x:x+80]
                noise = np.random.randint(-20, 20, noise_region.shape, dtype=np.int16)
                frame[y:y+120, x:x+80] = np.clip(noise_region.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # Add timestamp text
        timestamp = f"T={t:.1f}s"
        cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)
        
        # Write frame
        out.write(frame)
        
        if (frame_num + 1) % 10 == 0:
            print(f"  Frame {frame_num + 1}/{total_frames}")
    
    out.release()
    
    print(f"✓ Test video created: {output_path}")
    
    # Verify file exists and has size
    path = Path(output_path)
    if path.exists():
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"  File size: {size_mb:.2f} MB")
    else:
        print(f"✗ Error: File not created")


if __name__ == "__main__":
    output_path = "alibi/data/test_video.mp4"
    
    # Create data directory
    Path("alibi/data").mkdir(parents=True, exist_ok=True)
    
    # Create test video
    create_test_video(output_path, duration_seconds=10, fps=10)
    
    print("\nTest video ready for use in cameras.json")
