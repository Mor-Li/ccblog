#!/usr/bin/env python3
"""
Download all images from HuggingFace continuous batching blog post.
"""

import os
import json
import time
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

# Configuration
BLOG_URL = "https://huggingface.co/blog/continuous_batching"
OUTPUT_DIR = Path("/home/limo/ccblog/blog/continuous-batching")
MANIFEST_FILE = OUTPUT_DIR / "images.json"

# Headers to mimic browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://huggingface.co/',
}

def sanitize_filename(filename):
    """Remove or replace invalid characters in filename and remove all spaces."""
    # First normalize unicode spaces
    filename = filename.replace('\u202f', '_')  # narrow no-break space
    filename = filename.replace('\u00a0', '_')  # non-breaking space
    filename = filename.replace(' ', '_')       # regular space
    # Remove other invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    return filename

def generate_meaningful_filename(img_url, alt_text, index):
    """Generate a meaningful filename based on context."""
    # Try to extract filename from URL
    url_path = urlparse(img_url).path
    original_name = os.path.basename(url_path)

    # If alt text is meaningful, use it
    if alt_text and len(alt_text) > 3 and alt_text.lower() not in ['image', 'img', 'picture']:
        base_name = sanitize_filename(alt_text[:50])  # Limit length
        ext = os.path.splitext(original_name)[1] or '.jpg'
        return f"{base_name}{ext}"

    # If original filename is meaningful (not generic like image1.jpg)
    if original_name and not re.match(r'^(image|img|picture|photo)\d*\.(jpg|png|gif|webp)$', original_name.lower()):
        return sanitize_filename(original_name)

    # Use index-based naming
    ext = os.path.splitext(original_name)[1] or '.jpg'
    return f"image-{index:02d}{ext}"

def download_image(img_url, output_path, retries=3):
    """Download an image with retry logic."""
    for attempt in range(retries):
        try:
            response = requests.get(img_url, headers=HEADERS, timeout=30)
            response.raise_for_status()

            # Verify it's a valid image
            img = Image.open(BytesIO(response.content))
            img.verify()

            # Save the image
            with open(output_path, 'wb') as f:
                f.write(response.content)

            return True, len(response.content)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            return False, str(e)

    return False, "Max retries exceeded"

def scrape_blog_images():
    """Scrape images from the blog post."""
    print(f"Fetching blog post: {BLOG_URL}")

    try:
        response = requests.get(BLOG_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching blog post: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the main article content
    # HuggingFace blog posts typically use specific container classes
    article = soup.find('article') or soup.find('main') or soup.find('div', class_='container')

    if not article:
        # Fall back to searching entire page
        article = soup

    images = []

    # Find all img tags in the article
    for img in article.find_all('img'):
        img_url = img.get('src') or img.get('data-src')
        if not img_url:
            continue

        # Skip small images (likely icons or UI elements)
        width = img.get('width')
        height = img.get('height')
        if width and height:
            try:
                if int(width) < 50 or int(height) < 50:
                    continue
            except ValueError:
                pass

        # Make URL absolute
        img_url = urljoin(BLOG_URL, img_url)

        # Skip data URLs and external tracking pixels
        if img_url.startswith('data:') or 'tracking' in img_url.lower():
            continue

        # Get alt text and context
        alt_text = img.get('alt', '')

        images.append({
            'url': img_url,
            'alt': alt_text,
        })

    # Also check for picture elements (responsive images)
    for picture in article.find_all('picture'):
        source = picture.find('source')
        if source:
            img_url = source.get('srcset', '').split(',')[0].split()[0]
            if img_url:
                img_url = urljoin(BLOG_URL, img_url)
                images.append({
                    'url': img_url,
                    'alt': picture.find('img').get('alt', '') if picture.find('img') else '',
                })

    return images

def main():
    """Main function to orchestrate the image download."""
    print("="*60)
    print("HuggingFace Continuous Batching Blog Image Downloader")
    print("="*60)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Scrape images
    images = scrape_blog_images()

    if not images:
        print("No images found in the blog post.")
        return

    print(f"\nFound {len(images)} images")

    # Download images
    manifest = []
    successful = 0
    failed = 0

    for idx, img_info in enumerate(images, 1):
        img_url = img_info['url']
        alt_text = img_info['alt']

        # Generate filename
        filename = generate_meaningful_filename(img_url, alt_text, idx)

        # Handle duplicates
        output_path = OUTPUT_DIR / filename
        counter = 1
        base_name, ext = os.path.splitext(filename)
        while output_path.exists():
            filename = f"{base_name}-{counter}{ext}"
            output_path = OUTPUT_DIR / filename
            counter += 1

        print(f"\n[{idx}/{len(images)}] Downloading: {img_url}")
        print(f"  -> Saving as: {filename}")

        success, result = download_image(img_url, output_path)

        if success:
            print(f"  ✓ Success ({result} bytes)")
            successful += 1
            manifest.append({
                'filename': filename,
                'original_url': img_url,
                'alt_text': alt_text,
                'size_bytes': result,
            })
        else:
            print(f"  ✗ Failed: {result}")
            failed += 1

    # Save manifest
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)

    # Print summary
    print("\n" + "="*60)
    print("DOWNLOAD SUMMARY")
    print("="*60)
    print(f"Total images found: {len(images)}")
    print(f"Successfully downloaded: {successful}")
    print(f"Failed downloads: {failed}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Manifest file: {MANIFEST_FILE}")

    if successful > 0:
        print("\nDownloaded images:")
        for item in manifest:
            print(f"  - {item['filename']}")
            if item['alt_text']:
                print(f"    Alt: {item['alt_text']}")

    # Verify no filenames contain spaces
    space_files = [f for f in os.listdir(OUTPUT_DIR) if ' ' in f and not f.endswith('.json')]
    if space_files:
        print(f"\n⚠ WARNING: Found {len(space_files)} files with spaces in names:")
        for f in space_files:
            print(f"  - {f}")
    else:
        print("\n✓ All filenames are space-free")

if __name__ == "__main__":
    main()
