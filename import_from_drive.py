"""
Import Emails from Google Drive

If you're using the Gmail Apps Script to save emails to Google Drive,
this script imports them into your Content Inbox.

SETUP:
1. Set up the Gmail Apps Script (email_automation/gmail_apps_script.js)
2. Sync your Google Drive folder to your computer
3. Set DRIVE_FOLDER_PATH below to point to that folder
4. Run this script periodically (or set up a cron job)

Or just run this from the app's Settings tab.
"""

import json
from pathlib import Path
from content_inbox import add_to_inbox, load_inbox

# Path to your synced Google Drive folder
# Update this to match your setup
DRIVE_FOLDER_PATH = Path.home() / "Google Drive" / "Newsletter-Inbox-Export"

# Alternative paths to check
ALTERNATIVE_PATHS = [
    Path.home() / "Google Drive" / "Newsletter-Inbox-Export",
    Path.home() / "GoogleDrive" / "Newsletter-Inbox-Export",
    Path.home() / "Library" / "CloudStorage" / "GoogleDrive-*" / "My Drive" / "Newsletter-Inbox-Export",
    Path.home() / "Dropbox" / "Newsletter-Inbox-Export",
]


def find_drive_folder() -> Path:
    """Find the Google Drive folder."""
    # Check configured path
    if DRIVE_FOLDER_PATH.exists():
        return DRIVE_FOLDER_PATH
    
    # Check alternative paths
    for path in ALTERNATIVE_PATHS:
        if '*' in str(path):
            # Glob pattern
            parent = path.parent
            pattern = path.name
            if parent.exists():
                matches = list(parent.glob(pattern))
                if matches:
                    return matches[0]
        elif path.exists():
            return path
    
    return None


def import_from_drive(folder_path: Path = None) -> dict:
    """
    Import email JSON files from Google Drive folder.
    
    Returns:
        dict with 'imported', 'skipped', 'errors' counts
    """
    folder = folder_path or find_drive_folder()
    
    if not folder or not folder.exists():
        return {
            'error': f'Drive folder not found. Check path: {DRIVE_FOLDER_PATH}',
            'imported': 0,
            'skipped': 0,
        }
    
    results = {
        'imported': 0,
        'skipped': 0,
        'errors': 0,
        'files_found': 0,
    }
    
    # Get existing inbox IDs to avoid re-processing
    existing = load_inbox()
    existing_subjects = {item.get('title', '') for item in existing}
    
    # Find JSON files
    json_files = list(folder.glob("*.json"))
    results['files_found'] = len(json_files)
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                email_data = json.load(f)
            
            subject = email_data.get('subject', '')
            
            # Skip if already imported (by subject)
            if subject in existing_subjects:
                results['skipped'] += 1
                continue
            
            # Add to inbox
            content = email_data.get('body') or email_data.get('html', '')
            
            result = add_to_inbox(
                content=content,
                source="email",
                title=subject,
                sender=email_data.get('from', ''),
                content_type="newsletter"
            )
            
            if result.get('error'):
                results['skipped'] += 1
            else:
                results['imported'] += 1
                existing_subjects.add(subject)
                
        except Exception as e:
            results['errors'] += 1
            print(f"Error processing {json_file.name}: {e}")
    
    return results


def import_from_folder(folder_path: str) -> dict:
    """Import from a specific folder path (for use in the app)."""
    return import_from_drive(Path(folder_path))


if __name__ == "__main__":
    print("=" * 60)
    print("IMPORT FROM GOOGLE DRIVE")
    print("=" * 60)
    
    folder = find_drive_folder()
    if folder:
        print(f"\nFound folder: {folder}")
    else:
        print(f"\nFolder not found: {DRIVE_FOLDER_PATH}")
        print("\nAlternative paths checked:")
        for p in ALTERNATIVE_PATHS:
            print(f"  - {p}")
        print("\nUpdate DRIVE_FOLDER_PATH in this script to match your setup.")
        exit(1)
    
    print("\nImporting emails...")
    results = import_from_drive()
    
    print(f"\nResults:")
    print(f"  Files found: {results['files_found']}")
    print(f"  Imported: {results['imported']}")
    print(f"  Skipped (duplicates): {results['skipped']}")
    print(f"  Errors: {results['errors']}")









