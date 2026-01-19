"""
Privacy Redaction for Training Data

Ensures personally identifiable information (PII) is removed before fine-tuning.

Methods:
- Face blurring (OpenCV Gaussian blur)
- Face pixelation (low-res mosaic)
- Face masking (black box)
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path


def blur_faces(
    image: np.ndarray,
    face_boxes: List[Tuple[int, int, int, int]],
    blur_strength: int = 99
) -> np.ndarray:
    """
    Blur faces in image using Gaussian blur.
    
    Args:
        image: Input image (BGR)
        face_boxes: List of face bounding boxes (x, y, w, h)
        blur_strength: Blur kernel size (must be odd)
        
    Returns:
        Image with blurred faces
    """
    result = image.copy()
    
    # Ensure blur_strength is odd
    if blur_strength % 2 == 0:
        blur_strength += 1
    
    for (x, y, w, h) in face_boxes:
        # Extract face ROI
        face_roi = result[y:y+h, x:x+w]
        
        # Apply Gaussian blur
        blurred_face = cv2.GaussianBlur(face_roi, (blur_strength, blur_strength), 0)
        
        # Replace face in result
        result[y:y+h, x:x+w] = blurred_face
    
    return result


def pixelate_faces(
    image: np.ndarray,
    face_boxes: List[Tuple[int, int, int, int]],
    pixel_size: int = 20
) -> np.ndarray:
    """
    Pixelate faces in image (mosaic effect).
    
    Args:
        image: Input image (BGR)
        face_boxes: List of face bounding boxes (x, y, w, h)
        pixel_size: Size of pixelation blocks
        
    Returns:
        Image with pixelated faces
    """
    result = image.copy()
    
    for (x, y, w, h) in face_boxes:
        # Extract face ROI
        face_roi = result[y:y+h, x:x+w]
        
        # Get dimensions
        roi_h, roi_w = face_roi.shape[:2]
        
        # Resize down
        temp = cv2.resize(
            face_roi,
            (roi_w // pixel_size, roi_h // pixel_size),
            interpolation=cv2.INTER_LINEAR
        )
        
        # Resize back up (pixelated)
        pixelated = cv2.resize(
            temp,
            (roi_w, roi_h),
            interpolation=cv2.INTER_NEAREST
        )
        
        # Replace face in result
        result[y:y+h, x:x+w] = pixelated
    
    return result


def mask_faces(
    image: np.ndarray,
    face_boxes: List[Tuple[int, int, int, int]],
    color: Tuple[int, int, int] = (0, 0, 0)
) -> np.ndarray:
    """
    Mask faces with solid color box.
    
    Args:
        image: Input image (BGR)
        face_boxes: List of face bounding boxes (x, y, w, h)
        color: Mask color (BGR)
        
    Returns:
        Image with masked faces
    """
    result = image.copy()
    
    for (x, y, w, h) in face_boxes:
        cv2.rectangle(result, (x, y), (x+w, y+h), color, -1)
    
    return result


def detect_faces(image: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """
    Detect faces in image using OpenCV cascade.
    
    Args:
        image: Input image (BGR)
        
    Returns:
        List of face bounding boxes (x, y, w, h)
    """
    try:
        # Load OpenCV's pre-trained face detector
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        return [(x, y, w, h) for (x, y, w, h) in faces]
    
    except Exception as e:
        print(f"⚠️  Face detection failed: {e}")
        return []


def redact_image(
    image_path: str,
    output_path: str,
    method: str = "blur",
    face_boxes: Optional[List[Tuple[int, int, int, int]]] = None
) -> bool:
    """
    Redact faces in image file.
    
    Args:
        image_path: Input image path
        output_path: Output image path
        method: Redaction method ("blur", "pixelate", "mask")
        face_boxes: Optional pre-detected face boxes (if None, auto-detect)
        
    Returns:
        True if successful
    """
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Failed to read image: {image_path}")
        return False
    
    # Detect faces if not provided
    if face_boxes is None:
        face_boxes = detect_faces(image)
    
    if not face_boxes:
        print(f"ℹ️  No faces detected in {image_path}")
        # No faces, just copy the image
        cv2.imwrite(output_path, image)
        return True
    
    print(f"🔒 Redacting {len(face_boxes)} faces in {image_path}")
    
    # Apply redaction
    if method == "blur":
        result = blur_faces(image, face_boxes)
    elif method == "pixelate":
        result = pixelate_faces(image, face_boxes)
    elif method == "mask":
        result = mask_faces(image, face_boxes)
    else:
        print(f"❌ Unknown redaction method: {method}")
        return False
    
    # Save result
    cv2.imwrite(output_path, result)
    print(f"✅ Redacted image saved to {output_path}")
    
    return True


def redact_video(
    video_path: str,
    output_path: str,
    method: str = "blur",
    face_boxes_per_frame: Optional[Dict[int, List[Tuple[int, int, int, int]]]] = None
) -> bool:
    """
    Redact faces in video file.
    
    Args:
        video_path: Input video path
        output_path: Output video path
        method: Redaction method ("blur", "pixelate", "mask")
        face_boxes_per_frame: Optional dict of frame_num -> face_boxes
        
    Returns:
        True if successful
    """
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Failed to open video: {video_path}")
        return False
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    # Create output writer
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_num = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Get face boxes for this frame (or detect)
        if face_boxes_per_frame and frame_num in face_boxes_per_frame:
            face_boxes = face_boxes_per_frame[frame_num]
        else:
            face_boxes = detect_faces(frame)
        
        # Apply redaction
        if face_boxes:
            if method == "blur":
                frame = blur_faces(frame, face_boxes)
            elif method == "pixelate":
                frame = pixelate_faces(frame, face_boxes)
            elif method == "mask":
                frame = mask_faces(frame, face_boxes)
        
        # Write frame
        out.write(frame)
        frame_num += 1
    
    # Cleanup
    cap.release()
    out.release()
    
    print(f"✅ Redacted video saved to {output_path} ({frame_num} frames)")
    return True


def check_privacy_risk(image_path: str) -> Tuple[bool, int]:
    """
    Check if image contains faces (privacy risk).
    
    Args:
        image_path: Path to image
        
    Returns:
        (has_faces, num_faces)
    """
    image = cv2.imread(image_path)
    if image is None:
        return False, 0
    
    faces = detect_faces(image)
    return len(faces) > 0, len(faces)


# Type hint imports
from typing import Dict
