"""
Alibi License Plate Recognition System

Hotlist plate detection and matching.
ALWAYS requires human verification. NO automated impoundment.
"""

from alibi.plates.plate_detect import PlateDetector, DetectedPlate
from alibi.plates.plate_ocr import PlateOCR
from alibi.plates.normalize import normalize_plate, is_valid_namibia_plate
from alibi.plates.hotlist_store import HotlistStore, HotlistEntry

__all__ = [
    'PlateDetector',
    'DetectedPlate',
    'PlateOCR',
    'normalize_plate',
    'is_valid_namibia_plate',
    'HotlistStore',
    'HotlistEntry',
]
