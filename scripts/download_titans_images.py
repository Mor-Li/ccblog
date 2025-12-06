#!/usr/bin/env python3
"""
Script to download all images from the Google Research Titans + MIRAS blog post.
"""

import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse
import json
import time
import re

def sanitize_filename(filename):
    """Remove spaces and special characters from filename."""
    # Replace spaces (including special spaces) with underscores
    filename = re.sub(r'[\s\u202f\u00a0]+', '_', filename)
    # Remove other problematic characters
    filename = re.sub(r'[^\w\.-]', '', filename)
    return filename

def get_meaningful_filename(img_tag, img_url, index):
    """Generate a meaningful filename based on alt text or URL."""
    # Try to get alt text
    alt_text = img_tag.get('alt', '')
    if alt_text and alt_text.strip() and len(alt_text) > 3:
        # Clean and sanitize alt text
        filename = alt_text.strip().lower()
        filename = re.sub(r'[^\w\s-]', '', filename)
        filename = re.sub(r'[\s]+', '_', filename)
        filename = filename[:100]  # Limit length
        return filename

    # Try to extract from URL
    path = urlparse(img_url).path
    name = Path(path).stem
    if name and name not in ['image', 'img', 'photo', 'picture']:
        return sanitize_filename(name)

    # Default to numbered
    return f"image_{index:03d}"

def download_images(url, output_dir):
    """Download all images from the blog post."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Fetching page: {url}")

    # Setup headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Get the page
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the main article content
    main_content = soup.find('main') or soup.find('article') or soup.find('body')

    if not main_content:
        print("Could not find main content area")
        return

    # Find all images
    images = main_content.find_all('img')

    print(f"Found {len(images)} images on the page")

    # Filter out non-content images (logos, icons, etc.)
    content_images = []
    exclude_patterns = [
        'logo', 'icon', 'avatar', 'profile', 'social',
        'breadcrumb', 'arrow', 'navigation', 'header', 'footer'
    ]

    for img in images:
        src = img.get('src', '') or img.get('data-src', '')
        alt = img.get('alt', '').lower()

        # Skip if looks like non-content image
        if any(pattern in src.lower() or pattern in alt for pattern in exclude_patterns):
            continue

        # Must have a source
        if not src:
            continue

        content_images.append(img)

    print(f"Filtered to {len(content_images)} content images")

    # Download images
    downloaded = []
    manifest = []

    for idx, img in enumerate(content_images, 1):
        src = img.get('src', '') or img.get('data-src', '')

        if not src:
            continue

        # Make URL absolute
        img_url = urljoin(url, src)

        print(f"\n[{idx}/{len(content_images)}] Processing: {img_url}")

        try:
            # Download with retry logic
            max_retries = 3
            for retry in range(max_retries):
                try:
                    img_response = requests.get(img_url, headers=headers, timeout=30)
                    img_response.raise_for_status()
                    break
                except Exception as e:
                    if retry < max_retries - 1:
                        print(f"  Retry {retry + 1}/{max_retries} after error: {e}")
                        time.sleep(2)
                    else:
                        raise

            # Determine file extension
            content_type = img_response.headers.get('content-type', '')
            if 'image/jpeg' in content_type or 'image/jpg' in content_type:
                ext = '.jpg'
            elif 'image/png' in content_type:
                ext = '.png'
            elif 'image/gif' in content_type:
                ext = '.gif'
            elif 'image/webp' in content_type:
                ext = '.webp'
            elif 'image/svg' in content_type:
                ext = '.svg'
            else:
                # Try to get from URL
                ext = Path(urlparse(img_url).path).suffix or '.jpg'

            # Generate filename
            base_name = get_meaningful_filename(img, img_url, idx)
            filename = f"{base_name}{ext}"

            # Handle duplicates
            output_file = output_path / filename
            counter = 1
            while output_file.exists():
                filename = f"{base_name}_{counter}{ext}"
                output_file = output_path / filename
                counter += 1

            # Verify filename has no spaces
            if ' ' in filename or '\u202f' in filename or '\u00a0' in filename:
                print(f"  WARNING: Filename contains spaces, sanitizing: {filename}")
                filename = sanitize_filename(filename)
                output_file = output_path / filename

            # Save image
            output_file.write_bytes(img_response.content)

            print(f"  ✓ Downloaded: {filename} ({len(img_response.content)} bytes)")

            downloaded.append(filename)
            manifest.append({
                'filename': filename,
                'original_url': img_url,
                'alt_text': img.get('alt', ''),
                'size_bytes': len(img_response.content)
            })

        except Exception as e:
            print(f"  ✗ Failed to download: {e}")

    # Verify no spaces in filenames
    print("\n" + "="*50)
    print("Verifying filenames...")
    for item in manifest:
        filename = item['filename']
        if ' ' in filename or '\u202f' in filename or '\u00a0' in filename:
            print(f"ERROR: Filename contains space characters: {filename}")
        else:
            print(f"✓ {filename}")

    # Save manifest
    manifest_file = output_path / 'images.json'
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("\n" + "="*50)
    print(f"Summary:")
    print(f"  Total images found: {len(images)}")
    print(f"  Content images filtered: {len(content_images)}")
    print(f"  Successfully downloaded: {len(downloaded)}")
    print(f"  Failed: {len(content_images) - len(downloaded)}")
    print(f"  Output directory: {output_path.absolute()}")
    print(f"  Manifest file: {manifest_file.absolute()}")

    if downloaded:
        print(f"\nDownloaded images:")
        for filename in downloaded:
            print(f"  - {filename}")

    return manifest

if __name__ == '__main__':
    url = 'https://research.google/blog/titans-miras-helping-ai-have-long-term-memory/'
    output_dir = '/home/limo/ccblog/blog/titans-miras-memory'

    try:
        download_images(url, output_dir)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
