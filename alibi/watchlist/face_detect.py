"""
Face Detection

Lightweight face detection using OpenCV DNN with pre-trained models.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path


class FaceDetector:
    """
    Face detector using OpenCV DNN with Caffe model.
    
    Uses res10_300x300_ssd_iter_140000.caffemodel (lightweight, fast).
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.5,
        model_path: Optional[str] = None
    ):
        """
        Initialize face detector.
        
        Args:
            confidence_threshold: Minimum confidence for detection
            model_path: Path to model files (optional, uses OpenCV built-in)
        """
        self.confidence_threshold = confidence_threshold
        
        # Try to load OpenCV's built-in face detector
        try:
            # OpenCV DNN face detector (Caffe model)
            # This is lightweight and included with OpenCV
            prototxt = cv2.data.haarcascades + "../deploy.prototxt"
            model = cv2.data.haarcascades + "../res10_300x300_ssd_iter_140000.caffemodel"
            
            # Try loading from OpenCV data directory
            # If not available, fall back to Haar Cascades
            try:
                self.net = cv2.dnn.readNetFromCaffe(prototxt, model)
                self.method = "dnn"
                print("[FaceDetector] Using OpenCV DNN face detector")
            except:
                # Fall back to Haar Cascades (always available)
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
                self.method = "haar"
                print("[FaceDetector] Using Haar Cascade face detector")
        
        except Exception as e:
            print(f"[FaceDetector] Warning: {e}")
            # Fall back to Haar Cascades
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            self.method = "haar"
            print("[FaceDetector] Using Haar Cascade face detector (fallback)")
    
    def detect(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in image.
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            List of bounding boxes [(x, y, w, h), ...]
        """
        if self.method == "dnn":
            return self._detect_dnn(image)
        else:
            return self._detect_haar(image)
    
    def _detect_dnn(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect using DNN"""
        h, w = image.shape[:2]
        
        # Prepare blob
        blob = cv2.dnn.blobFromImage(
            cv2.resize(image, (300, 300)),
            1.0,
            (300, 300),
            (104.0, 177.0, 123.0)
        )
        
        # Forward pass
        self.net.setInput(blob)
        detections = self.net.forward()
        
        # Extract bounding boxes
        faces = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > self.confidence_threshold:
                # Get bounding box
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                x1, y1, x2, y2 = box.astype(int)
                
                # Convert to (x, y, w, h) format
                x = max(0, x1)
                y = max(0, y1)
                width = min(w - x, x2 - x1)
                height = min(h - y, y2 - y1)
                
                faces.append((x, y, width, height))
        
        return faces
    
    def _detect_haar(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect using Haar Cascades"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # Convert to list of tuples
        return [(int(x), int(y), int(w), int(h)) for x, y, w, h in faces]
    
    def extract_face(
        self,
        image: np.ndarray,
        bbox: Tuple[int, int, int, int],
        padding: float = 0.2
    ) -> np.ndarray:
        """
        Extract face region from image with padding.
        
        Args:
            image: Input image
            bbox: Bounding box (x, y, w, h)
            padding: Padding ratio (0.2 = 20% padding)
            
        Returns:
            Face crop image
        """
        x, y, w, h = bbox
        
        # Add padding
        pad_w = int(w * padding)
        pad_h = int(h * padding)
        
        x1 = max(0, x - pad_w)
        y1 = max(0, y - pad_h)
        x2 = min(image.shape[1], x + w + pad_w)
        y2 = min(image.shape[0], y + h + pad_h)
        
        # Extract face
        face = image[y1:y2, x1:x2]
        
        return face
    
    def detect_and_extract(
        self,
        image: np.ndarray,
        return_largest: bool = True
    ) -> Optional[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
        """
        Detect faces and extract the largest one.
        
        Args:
            image: Input image
            return_largest: Return largest face only
            
        Returns:
            Tuple of (face_crop, bbox) or None if no face detected
        """
        faces = self.detect(image)
        
        if not faces:
            return None
        
        if return_largest:
            # Get largest face by area
            largest = max(faces, key=lambda f: f[2] * f[3])
            face_crop = self.extract_face(image, largest)
            return face_crop, largest
        else:
            # Return first face
            face_crop = self.extract_face(image, faces[0])
            return face_crop, faces[0]
