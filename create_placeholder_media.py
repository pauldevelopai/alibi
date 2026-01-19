#!/usr/bin/env python3
"""
Create placeholder media files for testing the Alibi Console.

This script generates simple placeholder images for snapshots
so the console can display evidence links properly during demos.
"""

import json
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont


def create_placeholder_snapshot(event_id: str, camera_id: str, output_path: Path):
    """Create a simple placeholder snapshot image"""
    # Create image
    width, height = 640, 480
    img = Image.new('RGB', (width, height), color=(50, 50, 60))
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fall back to basic if not available
    try:
        # Try to use a system font (size 20 and 16 for details)
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        detail_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except:
        # Fallback to default
        title_font = ImageFont.load_default()
        detail_font = ImageFont.load_default()
    
    # Draw title
    title = "CAMERA SNAPSHOT"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = bbox[2] - bbox[0]
    title_x = (width - title_width) // 2
    draw.text((title_x, 150), title, fill=(200, 200, 200), font=title_font)
    
    # Draw camera ID
    cam_text = f"Camera: {camera_id}"
    bbox = draw.textbbox((0, 0), cam_text, font=detail_font)
    cam_width = bbox[2] - bbox[0]
    cam_x = (width - cam_width) // 2
    draw.text((cam_x, 200), cam_text, fill=(150, 150, 150), font=detail_font)
    
    # Draw event ID
    evt_text = f"Event: {event_id}"
    bbox = draw.textbbox((0, 0), evt_text, font=detail_font)
    evt_width = bbox[2] - bbox[0]
    evt_x = (width - evt_width) // 2
    draw.text((evt_x, 230), evt_text, fill=(150, 150, 150), font=detail_font)
    
    # Draw timestamp
    ts_text = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    bbox = draw.textbbox((0, 0), ts_text, font=detail_font)
    ts_width = bbox[2] - bbox[0]
    ts_x = (width - ts_width) // 2
    draw.text((ts_x, 260), ts_text, fill=(100, 100, 100), font=detail_font)
    
    # Draw border
    draw.rectangle([(10, 10), (width-10, height-10)], outline=(80, 80, 90), width=2)
    
    # Save
    img.save(output_path)
    print(f"Created placeholder: {output_path}")


def generate_placeholders_from_events():
    """Generate placeholder snapshots for existing events in events.jsonl"""
    events_file = Path("alibi/data/events.jsonl")
    snapshots_dir = Path("alibi/data/media/snapshots")
    
    if not events_file.exists():
        print(f"No events file found at {events_file}")
        print("Run the simulator first to generate events.")
        return
    
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    
    # Read events
    events_processed = 0
    with open(events_file, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            
            event = json.loads(line)
            event_id = event.get('event_id')
            camera_id = event.get('camera_id', 'unknown')
            
            if not event_id:
                continue
            
            # Check if placeholder already exists
            snapshot_path = snapshots_dir / f"{event_id}.jpg"
            if snapshot_path.exists():
                continue
            
            # Create placeholder
            create_placeholder_snapshot(event_id, camera_id, snapshot_path)
            events_processed += 1
    
    print(f"\nProcessed {events_processed} events")
    print(f"Snapshots directory: {snapshots_dir}")


def create_sample_placeholders():
    """Create a few sample placeholders for testing"""
    snapshots_dir = Path("alibi/data/media/snapshots")
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    
    samples = [
        ("evt_sample_001", "cam_entrance_main"),
        ("evt_sample_002", "cam_lobby_west"),
        ("evt_sample_003", "cam_parking_north"),
    ]
    
    for event_id, camera_id in samples:
        snapshot_path = snapshots_dir / f"{event_id}.jpg"
        create_placeholder_snapshot(event_id, camera_id, snapshot_path)
    
    print(f"\nCreated {len(samples)} sample placeholders in {snapshots_dir}")


if __name__ == "__main__":
    import sys
    
    print("Alibi Placeholder Media Generator")
    print("==================================\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        # Create sample placeholders only
        create_sample_placeholders()
    else:
        # Generate from events.jsonl
        print("Generating placeholder snapshots from events.jsonl...")
        print("(Use --sample flag to create only sample placeholders)\n")
        generate_placeholders_from_events()
    
    print("\nDone! Start the API server to view snapshots:")
    print("  python -m alibi.alibi_api")
    print("\nThen access snapshots via:")
    print("  http://localhost:8000/media/snapshots/evt_sample_001.jpg")
