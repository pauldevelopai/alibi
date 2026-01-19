"""
License Plate Normalization

Normalizes license plate strings for consistent matching.
Configurable for Namibia plate formats.
"""

import re
from typing import Optional


# Namibia license plate format patterns
# Format: Region Code + Number + Region Code
# Example: N 12345 W or N12345W
# Regions: W (Windhoek), K (Khomas), E (Erongo), O (Otjozondjupa), etc.

NAMIBIA_PATTERNS = [
    r'^([A-Z])[\s\-]*(\d{3,6})[\s\-]*([A-Z])$',  # N 12345 W or N12345W
    r'^([A-Z]{2})[\s\-]*(\d{3,6})$',              # WH 12345 (some formats)
    r'^(\d{3,6})[\s\-]*([A-Z]{2})$',              # 12345 WH (reversed)
]

# Common OCR substitution errors
OCR_CORRECTIONS = {
    # Number -> Letter
    '0': 'O',
    '1': 'I',
    '5': 'S',
    '8': 'B',
    # Letter -> Number
    'O': '0',
    'I': '1',
    'S': '5',
    'B': '8',
    'Z': '2',
    'G': '6',
}


def normalize_plate(plate_text: str, strict: bool = False) -> str:
    """
    Normalize license plate text.
    
    Steps:
    1. Convert to uppercase
    2. Remove spaces, hyphens, special chars
    3. Apply format-specific normalization
    
    Args:
        plate_text: Raw plate text from OCR
        strict: If True, only return plates matching known patterns
        
    Returns:
        Normalized plate string
    """
    if not plate_text:
        return ""
    
    # Convert to uppercase
    plate = plate_text.upper()
    
    # Remove common non-alphanumeric chars except spaces
    plate = re.sub(r'[^A-Z0-9\s]', '', plate)
    
    # Try to match Namibia patterns
    for pattern in NAMIBIA_PATTERNS:
        match = re.match(pattern, plate)
        if match:
            # Reconstruct in standard format (no spaces)
            groups = match.groups()
            normalized = ''.join(groups)
            return normalized
    
    # If no pattern matched but not strict, just remove spaces
    if not strict:
        normalized = plate.replace(' ', '')
        return normalized
    
    return ""


def is_valid_namibia_plate(plate_text: str) -> bool:
    """
    Check if plate text matches valid Namibia format.
    
    Args:
        plate_text: Plate text to validate
        
    Returns:
        True if valid format
    """
    if not plate_text:
        return False
    
    plate = plate_text.upper().replace(' ', '')
    
    # Check against patterns
    for pattern in NAMIBIA_PATTERNS:
        # Remove spaces from pattern for matching
        pattern_no_space = pattern.replace('[\\s\\-]*', '')
        if re.match(pattern_no_space, plate):
            return True
    
    return False


def apply_ocr_corrections(plate_text: str, aggressive: bool = False) -> list[str]:
    """
    Generate possible corrections for OCR errors.
    
    Args:
        plate_text: Original plate text
        aggressive: If True, generate more variations
        
    Returns:
        List of possible corrected variations (including original)
    """
    variations = [plate_text]
    
    if not aggressive:
        return variations
    
    # For each character, try common substitutions
    for i, char in enumerate(plate_text):
        if char in OCR_CORRECTIONS:
            # Create variation with substitution
            variant = plate_text[:i] + OCR_CORRECTIONS[char] + plate_text[i+1:]
            variations.append(variant)
    
    return list(set(variations))  # Remove duplicates


def fuzzy_match_plates(plate1: str, plate2: str, max_distance: int = 1) -> bool:
    """
    Check if two plates are similar (fuzzy match).
    
    Uses edit distance to allow for minor OCR errors.
    
    Args:
        plate1: First plate
        plate2: Second plate
        max_distance: Maximum edit distance to consider a match
        
    Returns:
        True if plates are similar
    """
    # Normalize both
    p1 = normalize_plate(plate1)
    p2 = normalize_plate(plate2)
    
    if not p1 or not p2:
        return False
    
    # Calculate Levenshtein distance
    distance = levenshtein_distance(p1, p2)
    
    return distance <= max_distance


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein (edit) distance between two strings.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Edit distance (number of single-character edits)
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, or substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def format_plate_display(plate_text: str) -> str:
    """
    Format plate for human-readable display.
    
    Args:
        plate_text: Normalized plate text
        
    Returns:
        Formatted plate string (with spaces for readability)
    """
    plate = normalize_plate(plate_text)
    
    if not plate:
        return plate_text
    
    # For Namibia format N12345W -> N 12345 W
    if len(plate) >= 7 and plate[0].isalpha() and plate[-1].isalpha():
        return f"{plate[0]} {plate[1:-1]} {plate[-1]}"
    
    # For other formats, add space every 3-4 chars
    if len(plate) > 6:
        mid = len(plate) // 2
        return f"{plate[:mid]} {plate[mid:]}"
    
    return plate
