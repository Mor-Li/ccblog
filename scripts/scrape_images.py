#!/usr/bin/env python3
"""
Script to scrape images from a Notion page and download them.
"""
import os
import json
import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
import time

def sanitize_filename(filename):
    """Remove special characters and spaces from filename."""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace all types of spaces (including special unicode spaces) with underscores
    filename = re.sub(r'[\s\u00a0\u202f\u2000-\u200f\u2028-\u202f\u3000]+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    return filename

def extract_images_from_notion(html_file, base_url):
    """Extract all image URLs from Notion HTML."""
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    images = []

    # Find all img tags
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src')
        if src:
            # Make absolute URL
            full_url = urljoin(base_url, src)
            alt_text = img.get('alt', '')

            images.append({
                'url': full_url,
                'alt': alt_text,
                'tag': 'img'
            })

    # Look for Notion-specific image patterns
    # Notion often uses divs with background images or data attributes
    for div in soup.find_all('div', class_=re.compile(r'.*image.*', re.I)):
        style = div.get('style', '')
        bg_match = re.search(r'background-image:\s*url\(["\']?([^"\']+)["\']?\)', style)
        if bg_match:
            url = bg_match.group(1)
            full_url = urljoin(base_url, url)
            images.append({
                'url': full_url,
                'alt': 'background-image',
                'tag': 'div'
            })

    # Look for picture tags
    for picture in soup.find_all('picture'):
        for source in picture.find_all('source'):
            srcset = source.get('srcset')
            if srcset:
                # Take the first URL from srcset
                url = srcset.split(',')[0].strip().split()[0]
                full_url = urljoin(base_url, url)
                images.append({
                    'url': full_url,
                    'alt': 'picture-source',
                    'tag': 'picture'
                })

    # Remove duplicates
    seen = set()
    unique_images = []
    for img in images:
        # Clean up Notion image URLs (remove query params for deduplication)
        url_base = img['url'].split('?')[0]
        if url_base not in seen:
            seen.add(url_base)
            unique_images.append(img)

    return unique_images

def download_image(url, output_path, retries=3):
    """Download an image with retry logic."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://notion.site/',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    }

    for attempt in range(retries):
        try:
            print(f"  Downloading (attempt {attempt + 1}/{retries})...")
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()

            # Write to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verify file size
            file_size = os.path.getsize(output_path)
            if file_size < 100:  # Suspiciously small
                print(f"  Warning: File size is only {file_size} bytes")
                return False

            print(f"  Success! Downloaded {file_size} bytes")
            return True

        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2)  # Wait before retry
            else:
                print(f"  Failed after {retries} attempts")
                return False

    return False

def main():
    html_file = '/tmp/notion_page.html'
    base_url = 'https://yingru.notion.site/The-Optimal-Token-Baseline-399211a558b782cfa936014c0d42dfb8'
    output_dir = Path('/home/limo/ccblog/blog/optimal-token-baseline')

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract images
    print("Extracting image URLs from HTML...")
    images = extract_images_from_notion(html_file, base_url)
    print(f"Found {len(images)} unique images")

    # Download images
    manifest = []
    successful = 0
    failed = []

    for idx, img_info in enumerate(images, 1):
        url = img_info['url']
        alt = img_info['alt']

        print(f"\n[{idx}/{len(images)}] Processing image:")
        print(f"  URL: {url}")
        print(f"  Alt: {alt}")

        # Generate filename
        # Try to get filename from URL
        parsed = urlparse(url)
        url_filename = os.path.basename(parsed.path)

        # Decode URL encoding
        url_filename = unquote(url_filename)

        # If filename is not meaningful, use alt text or index
        if not url_filename or url_filename in ['', 'image']:
            if alt and alt != 'background-image' and alt != 'picture-source':
                filename = f"{sanitize_filename(alt)}.png"
            else:
                filename = f"image_{idx:03d}.png"
        else:
            # Sanitize the filename
            filename = sanitize_filename(url_filename)

            # Ensure it has an extension
            if not any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
                filename += '.png'

        # Handle duplicates
        output_path = output_dir / filename
        counter = 1
        while output_path.exists():
            name, ext = os.path.splitext(filename)
            output_path = output_dir / f"{name}_{counter}{ext}"
            counter += 1

        print(f"  Saving to: {output_path}")

        # Download
        if download_image(url, output_path):
            successful += 1
            manifest.append({
                'filename': output_path.name,
                'original_url': url,
                'alt_text': alt,
                'tag': img_info['tag']
            })
        else:
            failed.append({'url': url, 'alt': alt})
            # Remove failed download file if it exists
            if output_path.exists():
                output_path.unlink()

    # Save manifest
    manifest_path = output_dir / 'images.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total images found: {len(images)}")
    print(f"Successfully downloaded: {successful}")
    print(f"Failed: {len(failed)}")
    print(f"Output directory: {output_dir}")
    print(f"Manifest file: {manifest_path}")

    if failed:
        print("\nFailed downloads:")
        for f in failed:
            print(f"  - {f['url']}")
            print(f"    Alt: {f['alt']}")

    # Verify no spaces in filenames
    print("\nVerifying filenames...")
    files_with_spaces = []
    for file in output_dir.glob('*'):
        if file.is_file() and ' ' in file.name:
            files_with_spaces.append(file.name)

    if files_with_spaces:
        print("WARNING: Found files with spaces in names:")
        for fname in files_with_spaces:
            print(f"  - {fname}")
    else:
        print("All filenames are space-free!")

    print("\nImage list:")
    for item in manifest:
        print(f"  - {item['filename']}")
        if item['alt_text']:
            print(f"    Description: {item['alt_text']}")

if __name__ == '__main__':
    main()
