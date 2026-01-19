"""
Import Plate Registry from CSV

CLI tool to import plate-to-vehicle mappings from CSV file.
"""

import csv
import argparse
from pathlib import Path
from datetime import datetime

from alibi.vehicles.plate_registry import PlateRegistryStore, PlateRegistryEntry
from alibi.plates.normalize import normalize_plate


def import_csv(csv_path: str, registry_path: str = "alibi/data/plate_registry.jsonl") -> int:
    """
    Import registry entries from CSV.
    
    CSV format:
    plate,make,model,source_ref
    N12345W,Mazda,Demio,DMV_2024
    
    Args:
        csv_path: Path to CSV file
        registry_path: Path to registry JSONL file
        
    Returns:
        Number of entries imported
    """
    store = PlateRegistryStore(registry_path)
    
    imported_count = 0
    skipped_count = 0
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Get fields
            plate = row.get('plate', '').strip()
            make = row.get('make', '').strip()
            model = row.get('model', '').strip()
            source_ref = row.get('source_ref', 'imported').strip()
            
            # Validate
            if not plate or not make or not model:
                print(f"Skipping invalid row: {row}")
                skipped_count += 1
                continue
            
            # Normalize plate
            normalized_plate = normalize_plate(plate)
            
            if not normalized_plate:
                print(f"Skipping invalid plate: {plate}")
                skipped_count += 1
                continue
            
            # Create entry
            entry = PlateRegistryEntry(
                plate=normalized_plate,
                expected_make=make,
                expected_model=model,
                source_ref=source_ref,
                added_ts=datetime.utcnow().isoformat()
            )
            
            # Add to store
            store.add_entry(entry)
            imported_count += 1
    
    print(f"\n✅ Import complete:")
    print(f"   Imported: {imported_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Registry: {registry_path}")
    
    return imported_count


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Import plate registry from CSV file"
    )
    parser.add_argument(
        '--csv',
        required=True,
        help='Path to CSV file (columns: plate,make,model,source_ref)'
    )
    parser.add_argument(
        '--registry',
        default='alibi/data/plate_registry.jsonl',
        help='Path to registry file (default: alibi/data/plate_registry.jsonl)'
    )
    
    args = parser.parse_args()
    
    # Check CSV exists
    if not Path(args.csv).exists():
        print(f"❌ Error: CSV file not found: {args.csv}")
        return 1
    
    # Import
    print(f"📋 Importing plate registry from: {args.csv}")
    import_csv(args.csv, args.registry)
    
    return 0


if __name__ == "__main__":
    exit(main())
