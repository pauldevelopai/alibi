#!/usr/bin/env python3
"""
Check Fine-Tuning Status

Run: python check_training.py
Or with auto-refresh: python check_training.py --watch
"""

import sys
import time
from datetime import datetime
from fine_tuning import check_job_status, get_job_events, set_active_model

# Current job ID
JOB_ID = 'ftjob-jeQbOXVIitN5wq4ozIHfOaKa'
TOTAL_TOKENS = 71012  # From our export


def print_status():
    """Print detailed status."""
    status = check_job_status(JOB_ID)
    
    print('\033[2J\033[H')  # Clear screen
    print('=' * 60)
    print('🎯 FINE-TUNING STATUS')
    print('=' * 60)
    print(f"Job ID: {JOB_ID}")
    
    # Status with emoji
    status_emoji = {
        'validating_files': '🔍',
        'queued': '⏳',
        'running': '🏃',
        'succeeded': '✅',
        'failed': '❌',
        'cancelled': '🚫'
    }
    emoji = status_emoji.get(status['status'], '❓')
    print(f"Status: {emoji} {status['status'].upper()}")
    print(f"Base Model: {status['base_model']}")
    
    # Calculate elapsed time
    try:
        created = int(status['created_at'])
        created_dt = datetime.fromtimestamp(created)
        elapsed = datetime.now() - created_dt
        elapsed_mins = int(elapsed.total_seconds() / 60)
        elapsed_secs = int(elapsed.total_seconds() % 60)
        print(f"Elapsed: {elapsed_mins}m {elapsed_secs}s")
    except:
        elapsed_mins = 0
    
    # Training progress
    if status.get('trained_tokens'):
        trained = status['trained_tokens']
        # 3 epochs, so total = tokens * 3
        total_with_epochs = TOTAL_TOKENS * 3
        progress = min(100, (trained / total_with_epochs) * 100)
        bar_len = 30
        filled = int(bar_len * progress / 100)
        bar = '█' * filled + '░' * (bar_len - filled)
        print(f"Progress: [{bar}] {progress:.1f}%")
        print(f"Trained: {trained:,} / ~{total_with_epochs:,} tokens")
    
    # Time estimate for running jobs
    if status['status'] == 'running':
        # Typical: ~15-30 min for 70K tokens with 3 epochs
        estimated_total = 20  # Conservative estimate
        remaining = max(0, estimated_total - elapsed_mins)
        print(f"Estimated remaining: ~{int(remaining)}-{int(remaining+10)} minutes")
    
    # Success!
    if status['fine_tuned_model']:
        print()
        print('🎉 ' + '=' * 56 + ' 🎉')
        print(f"   TRAINING COMPLETE!")
        print(f"   Model: {status['fine_tuned_model']}")
        print('🎉 ' + '=' * 56 + ' 🎉')
        
        # Auto-activate
        set_active_model(status['fine_tuned_model'])
        print("\n✅ Model has been set as active for generation!")
        return True  # Done
    
    if status.get('error'):
        print(f"\n❌ Error: {status['error']}")
        return True  # Done (with error)
    
    # Get recent events
    print()
    print('-' * 60)
    print('📋 TRAINING LOG')
    print('-' * 60)
    
    try:
        events = get_job_events(JOB_ID, limit=8)
        for event in reversed(events):
            level = '✓' if event['level'] == 'info' else '⚠'
            msg = event['message']
            # Truncate long messages
            if len(msg) > 55:
                msg = msg[:52] + '...'
            print(f" {level} {msg}")
    except Exception as e:
        print(f"  Could not fetch events: {e}")
    
    print()
    print("Run with --watch for auto-refresh, or Ctrl+C to exit")
    
    return status['status'] in ['succeeded', 'failed', 'cancelled']


def main():
    watch_mode = '--watch' in sys.argv or '-w' in sys.argv
    
    if watch_mode:
        print("Starting watch mode (refreshes every 30 seconds)...")
        while True:
            done = print_status()
            if done:
                break
            time.sleep(30)
    else:
        print_status()


if __name__ == '__main__':
    main()








