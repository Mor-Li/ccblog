#!/usr/bin/env python3
"""
Script to download all images from the surjective transformers blog post.
"""

import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

def sanitize_filename(filename):
    """Remove special characters and spaces from filename."""
    # Replace various space characters with underscores
    filename = filename.replace(' ', '_')
    filename = filename.replace('\u202f', '_')  # narrow no-break space
    filename = filename.replace('\u00a0', '_')  # non-breaking space
    filename = filename.replace('\xa0', '_')    # another non-breaking space

    # Remove or replace other problematic characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'_+', '_', filename)  # Replace multiple underscores with single
    filename = filename.strip('_')

    return filename

def get_meaningful_filename(img_tag, img_url, index):
    """Generate a meaningful filename based on alt text or context."""
    # Try alt text first
    alt_text = img_tag.get('alt', '').strip()
    if alt_text and len(alt_text) > 3:
        # Sanitize and use alt text
        base_name = sanitize_filename(alt_text.lower().replace(' ', '-'))
        base_name = re.sub(r'-+', '-', base_name)  # Replace multiple hyphens
        base_name = base_name[:50]  # Limit length
    else:
        # Use original filename if meaningful, otherwise use generic name
        original_name = Path(urlparse(img_url).path).stem
        if original_name and not re.match(r'^(image|img)_?\d*$', original_name.lower()):
            base_name = sanitize_filename(original_name)
        else:
            base_name = f"image-{index:03d}"

    return base_name

def download_images(html_file, base_url, output_dir):
    """Parse HTML and download all images."""
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read and parse HTML
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Find all image tags
    img_tags = soup.find_all('img')
    print(f"Found {len(img_tags)} images on the page")

    # Track downloaded images
    downloaded = []
    failed = []
    manifest = []

    # Set up session with headers
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': base_url
    })

    for idx, img in enumerate(img_tags, 1):
        img_src = img.get('src') or img.get('data-src')
        if not img_src:
            continue

        # Make absolute URL
        img_url = urljoin(base_url, img_src)

        # Get file extension
        parsed_url = urlparse(img_url)
        ext = Path(parsed_url.path).suffix
        if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
            # Try to determine from URL or default to .png
            if 'data:image' in img_url:
                continue  # Skip data URLs for now
            ext = '.png'

        # Generate filename
        base_filename = get_meaningful_filename(img, img_url, idx)
        filename = f"{base_filename}{ext}"

        # Handle filename conflicts
        output_path = output_dir / filename
        counter = 1
        while output_path.exists():
            filename = f"{base_filename}-{counter}{ext}"
            output_path = output_dir / filename
            counter += 1

        # Download image with retries
        print(f"Downloading [{idx}/{len(img_tags)}]: {filename}")
        success = False
        for attempt in range(3):
            try:
                response = session.get(img_url, timeout=30)
                response.raise_for_status()

                # Verify it's actually an image
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    print(f"  Warning: Content type is {content_type}, not an image")

                # Save image
                with open(output_path, 'wb') as f:
                    f.write(response.content)

                # Verify file was written
                if output_path.stat().st_size > 0:
                    downloaded.append(filename)
                    manifest.append({
                        'filename': filename,
                        'original_url': img_url,
                        'alt_text': img.get('alt', ''),
                        'size_bytes': output_path.stat().st_size
                    })
                    print(f"  ✓ Saved: {filename} ({output_path.stat().st_size} bytes)")
                    success = True
                    break
                else:
                    print(f"  ✗ File is empty, retrying...")

            except Exception as e:
                print(f"  Attempt {attempt + 1}/3 failed: {str(e)}")
                if attempt == 2:
                    failed.append({'url': img_url, 'filename': filename, 'error': str(e)})

        if not success:
            print(f"  ✗ Failed to download after 3 attempts")

    # Save manifest
    manifest_path = output_dir / 'images.json'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump({
            'blog_url': base_url,
            'total_found': len(img_tags),
            'downloaded': len(downloaded),
            'failed': len(failed),
            'images': manifest,
            'failed_images': failed
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Download Summary:")
    print(f"  Total images found: {len(img_tags)}")
    print(f"  Successfully downloaded: {len(downloaded)}")
    print(f"  Failed: {len(failed)}")
    print(f"  Output directory: {output_dir.absolute()}")
    print(f"  Manifest: {manifest_path.absolute()}")
    print(f"{'='*60}")

    # Verify no spaces in filenames
    files_with_spaces = [f for f in downloaded if ' ' in f or '\u202f' in f or '\u00a0' in f]
    if files_with_spaces:
        print(f"\n⚠ WARNING: Found {len(files_with_spaces)} files with spaces:")
        for f in files_with_spaces:
            print(f"  - {f}")
    else:
        print("\n✓ All filenames are space-free")

    return len(downloaded), len(failed)

if __name__ == '__main__':
    html_file = '/tmp/surjective_page.html'
    base_url = 'https://astro-eric.github.io/blogs/surjective/'
    output_dir = '/home/limo/ccblog/blog/surjective-transformers'

    download_images(html_file, base_url, output_dir)
