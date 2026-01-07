"""
Substack Export Importer

Imports a full Substack data export (posts.csv, delivers, opens, HTML content)
and calculates real open rates for each newsletter.

This gives us MUCH better data for training the AI model.
"""

import os
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd


# Paths
DATA_DIR = Path(__file__).parent / "data"
OUTPUT_JSONL = DATA_DIR / "newsletters_raw.jsonl"
OUTPUT_STATS = DATA_DIR / "newsletters_with_stats.csv"


def count_lines_in_csv(filepath: Path) -> int:
    """Count data rows in a CSV file (excluding header)."""
    if not filepath.exists():
        return 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header
        return sum(1 for row in reader if row)


def import_substack_export(export_dir: str) -> tuple[list[dict], pd.DataFrame]:
    """
    Import a Substack data export directory.
    
    Expected structure:
    export_dir/
        posts.csv           - Main posts metadata
        posts/
            {post_id}.delivers.csv  - Delivery records
            {post_id}.opens.csv     - Open records
            {post_id}.{slug}.html   - Full HTML content
    
    Returns:
        newsletters: list of newsletter dicts (for JSONL)
        stats_df: DataFrame with performance stats
    """
    export_path = Path(export_dir)
    posts_csv = export_path / "posts.csv"
    posts_dir = export_path / "posts"
    
    if not posts_csv.exists():
        raise FileNotFoundError(f"posts.csv not found in {export_dir}")
    
    print(f"Loading posts from {posts_csv}...")
    
    # Load posts.csv
    posts_df = pd.read_csv(posts_csv)
    
    # Filter to published newsletters only
    published = posts_df[
        (posts_df['is_published'] == True) & 
        (posts_df['type'] == 'newsletter') &
        (posts_df['title'].notna())
    ].copy()
    
    print(f"Found {len(published)} published newsletters")
    
    newsletters = []
    stats_rows = []
    
    for _, row in published.iterrows():
        full_post_id = str(row['post_id'])
        # Extract just the numeric part (before the dot)
        post_id = full_post_id.split('.')[0]
        title = row['title']
        date = row.get('post_date', '')
        subtitle = row.get('subtitle', '')
        audience = row.get('audience', 'everyone')
        
        print(f"  Processing: {title[:50]}...")
        
        # Find the HTML content file
        html_content = None
        if posts_dir.exists():
            # Look for HTML file matching this post_id
            html_files = list(posts_dir.glob(f"{post_id}.*.html"))
            if html_files:
                html_file = html_files[0]
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
        
        # Count delivers
        delivers_file = posts_dir / f"{post_id}.delivers.csv"
        delivers_count = count_lines_in_csv(delivers_file)
        
        # Count opens
        opens_file = posts_dir / f"{post_id}.opens.csv"
        opens_count = count_lines_in_csv(opens_file)
        
        # Calculate open rate
        open_rate = opens_count / delivers_count if delivers_count > 0 else 0
        
        # Build newsletter record
        newsletter = {
            'post_id': post_id,
            'title': title,
            'subtitle': subtitle,
            'published_date': date,
            'audience': audience,
            'content_html': html_content,
            'scraped_at': datetime.now().isoformat(),
            'url': f"https://developai.substack.com/p/{post_id}",
        }
        newsletters.append(newsletter)
        
        # Build stats record
        stats_rows.append({
            'title': title,
            'date': date[:10] if date else '',  # Just the date part
            'delivers': delivers_count,
            'opens': opens_count,
            'open_rate': round(open_rate, 4),
            'audience': audience,
            'post_id': post_id,
            'url': f"https://developai.substack.com/p/{post_id}",
        })
        
        print(f"    → {delivers_count} delivers, {opens_count} opens = {open_rate:.1%} open rate")
    
    stats_df = pd.DataFrame(stats_rows)
    
    return newsletters, stats_df


def save_imported_data(newsletters: list[dict], stats_df: pd.DataFrame):
    """Save the imported data to the standard locations."""
    
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save newsletters as JSONL
    with open(OUTPUT_JSONL, 'w', encoding='utf-8') as f:
        for newsletter in newsletters:
            f.write(json.dumps(newsletter, ensure_ascii=False) + '\n')
    
    print(f"\nSaved {len(newsletters)} newsletters to {OUTPUT_JSONL}")
    
    # Save stats as CSV
    stats_df.to_csv(OUTPUT_STATS, index=False)
    
    print(f"Saved stats to {OUTPUT_STATS}")


def print_summary(stats_df: pd.DataFrame):
    """Print a summary of the imported data."""
    
    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    
    print(f"\nTotal newsletters: {len(stats_df)}")
    print(f"Total delivers: {stats_df['delivers'].sum():,}")
    print(f"Total opens: {stats_df['opens'].sum():,}")
    
    avg_open_rate = stats_df['opens'].sum() / stats_df['delivers'].sum() if stats_df['delivers'].sum() > 0 else 0
    print(f"Overall open rate: {avg_open_rate:.1%}")
    
    print(f"\nAverage open rate: {stats_df['open_rate'].mean():.1%}")
    print(f"Best open rate: {stats_df['open_rate'].max():.1%}")
    print(f"Lowest open rate: {stats_df['open_rate'].min():.1%}")
    
    # Top performers
    print("\n📈 TOP 10 BY OPEN RATE:")
    top_10 = stats_df.nlargest(10, 'open_rate')
    for i, (_, row) in enumerate(top_10.iterrows(), 1):
        print(f"  {i}. {row['open_rate']:.1%} - {row['title'][:50]}...")
    
    # Bottom performers
    print("\n📉 BOTTOM 5 BY OPEN RATE:")
    bottom_5 = stats_df.nsmallest(5, 'open_rate')
    for i, (_, row) in enumerate(bottom_5.iterrows(), 1):
        print(f"  {i}. {row['open_rate']:.1%} - {row['title'][:50]}...")


def run_import(export_dir: str):
    """Main import function."""
    
    print("=" * 60)
    print("SUBSTACK EXPORT IMPORTER")
    print("=" * 60)
    
    newsletters, stats_df = import_substack_export(export_dir)
    save_imported_data(newsletters, stats_df)
    print_summary(stats_df)
    
    print("\n✅ Import complete!")
    print("\nNext steps:")
    print("  1. Run: python style_analyzer.py  (to regenerate the Bible)")
    print("  2. Restart the Streamlit app")
    
    return newsletters, stats_df


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        # Default path
        export_dir = "/Users/paulmcnally/Developai Dropbox/Paul McNally/Mac/Desktop/full"
        print(f"Using default export directory: {export_dir}")
    else:
        export_dir = sys.argv[1]
    
    run_import(export_dir)

