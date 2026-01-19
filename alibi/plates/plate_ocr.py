"""
License Plate OCR

Optical Character Recognition for license plates.
"""

import cv2
import numpy as np
from typing import Optional, Tuple
import re


class PlateOCR:
    """
    OCR for license plates.
    
    Uses EasyOCR for text recognition. Falls back to pytesseract if available.
    """
    
    def __init__(self):
        """Initialize OCR engine"""
        self.ocr_engine = None
        self.ocr_type = None
        
        # Try EasyOCR first
        try:
            import easyocr
            self.ocr_engine = easyocr.Reader(['en'], gpu=False)
            self.ocr_type = "easyocr"
            print("[PlateOCR] Using EasyOCR")
        except ImportError:
            pass
        
        # Fall back to pytesseract
        if self.ocr_engine is None:
            try:
                import pytesseract
                self.ocr_engine = pytesseract
                self.ocr_type = "tesseract"
                print("[PlateOCR] Using Tesseract OCR")
            except ImportError:
                pass
        
        if self.ocr_engine is None:
            print("[PlateOCR] WARNING: No OCR library available.")
            print("[PlateOCR] Install with: pip install easyocr")
            print("[PlateOCR] Or: pip install pytesseract")
            self.ocr_type = "none"
    
    def read_plate(self, plate_image: np.ndarray) -> Tuple[str, float]:
        """
        Read text from license plate image.
        
        Args:
            plate_image: Cropped plate region (BGR)
            
        Returns:
            Tuple of (plate_text, confidence)
        """
        if self.ocr_type == "none":
            return "", 0.0
        
        # Preprocess image
        preprocessed = self._preprocess_plate(plate_image)
        
        # Run OCR
        if self.ocr_type == "easyocr":
            return self._read_easyocr(preprocessed)
        elif self.ocr_type == "tesseract":
            return self._read_tesseract(preprocessed)
        
        return "", 0.0
    
    def _preprocess_plate(self, plate_image: np.ndarray) -> np.ndarray:
        """
        Preprocess plate image for better OCR.
        
        Steps:
        - Convert to grayscale
        - Resize to standard height
        - Apply adaptive thresholding
        - Denoise
        """
        # Convert to grayscale
        if len(plate_image.shape) == 3:
            gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_image
        
        # Resize to standard height (helps OCR)
        target_height = 100
        aspect_ratio = plate_image.shape[1] / plate_image.shape[0]
        target_width = int(target_height * aspect_ratio)
        
        if gray.shape[0] != target_height:
            gray = cv2.resize(gray, (target_width, target_height))
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)
        
        return denoised
    
    def _read_easyocr(self, image: np.ndarray) -> Tuple[str, float]:
        """Read using EasyOCR"""
        try:
            results = self.ocr_engine.readtext(image)
            
            if not results:
                return "", 0.0
            
            # Get result with highest confidence
            best_result = max(results, key=lambda x: x[2])
            text = best_result[1]
            confidence = best_result[2]
            
            # Clean text (remove spaces, special chars)
            text = self._clean_ocr_text(text)
            
            return text, confidence
        
        except Exception as e:
            print(f"[PlateOCR] EasyOCR error: {e}")
            return "", 0.0
    
    def _read_tesseract(self, image: np.ndarray) -> Tuple[str, float]:
        """Read using Tesseract"""
        try:
            # Configure Tesseract for license plates
            # --psm 7: Treat image as single text line
            # --oem 3: Use both legacy and LSTM engines
            custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            
            text = self.ocr_engine.image_to_string(image, config=custom_config)
            text = self._clean_ocr_text(text)
            
            # Tesseract doesn't provide confidence easily, use 0.7 as default
            confidence = 0.7 if text else 0.0
            
            return text, confidence
        
        except Exception as e:
            print(f"[PlateOCR] Tesseract error: {e}")
            return "", 0.0
    
    def _clean_ocr_text(self, text: str) -> str:
        """
        Clean OCR output.
        
        - Remove spaces
        - Remove special characters
        - Convert to uppercase
        - Keep only alphanumeric
        """
        # Remove spaces and special chars
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        return text
