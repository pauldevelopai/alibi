#!/usr/bin/env python3
"""
Sample script to enroll a test face into the watchlist.

Creates a synthetic face image and enrolls it for testing.
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alibi.watchlist.enroll import enroll_face


def create_sample_face_image(output_path: str):
    """Create a synthetic face-like image for testing"""
    # Create blank image
    img = np.ones((400, 400, 3), dtype=np.uint8) * 240
    
    # Draw face oval
    cv2.ellipse(img, (200, 200), (120, 150), 0, 0, 360, (220, 200, 180), -1)
    
    # Draw eyes
    cv2.circle(img, (160, 170), 20, (50, 50, 50), -1)
    cv2.circle(img, (240, 170), 20, (50, 50, 50), -1)
    cv2.circle(img, (165, 170), 8, (255, 255, 255), -1)
    cv2.circle(img, (245, 170), 8, (255, 255, 255), -1)
    
    # Draw nose
    pts = np.array([[200, 190], [190, 230], [210, 230]], np.int32)
    cv2.fillPoly(img, [pts], (180, 160, 140))
    
    # Draw mouth
    cv2.ellipse(img, (200, 260), (40, 20), 0, 0, 180, (100, 50, 50), 3)
    
    # Draw hair
    cv2.ellipse(img, (200, 120), (130, 80), 0, 180, 360, (60, 40, 20), -1)
    
    # Save
    cv2.imwrite(output_path, img)
    print(f"✅ Created sample face image: {output_path}")


def main():
    """Main entry point"""
    # Create sample face image
    sample_dir = Path("alibi/data/sample_faces")
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    sample_path = sample_dir / "test_person_001.jpg"
    create_sample_face_image(str(sample_path))
    
    # Enroll into watchlist
    print("\n📋 Enrolling into watchlist...")
    success = enroll_face(
        person_id="TEST_PERSON_001",
        label="Test Subject (Sample)",
        image_path=str(sample_path),
        source_ref="Testing/Demo",
        watchlist_path="alibi/data/watchlist.jsonl"
    )
    
    if success:
        print("\n✅ Sample enrollment complete!")
        print(f"   Face image: {sample_path}")
        print(f"   Watchlist: alibi/data/watchlist.jsonl")
        print("\nYou can now test the watchlist detector with this enrolled face.")
    else:
        print("\n❌ Enrollment failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
