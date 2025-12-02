#!/usr/bin/env python3
"""
Scrape images from a Notion page
"""
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse
import time
import re

def sanitize_filename(filename):
    """Remove special characters and replace spaces with underscores"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace all types of spaces (including special unicode spaces) with underscores
    filename = re.sub(r'[\s\u00a0\u202f\u2009\u200a]+', '_', filename)
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    return filename.strip('_')

def get_notion_page(url):
    """Fetch Notion page with appropriate headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text

def extract_images(html_content, base_url):
    """Extract all image URLs from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    images = []

    # Find all img tags
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src')
        if src:
            # Convert relative URLs to absolute
            full_url = urljoin(base_url, src)

            # Skip data URIs and very small images (likely icons)
            if full_url.startswith('data:'):
                continue

            # Get alt text for filename
            alt_text = img.get('alt', '')

            images.append({
                'url': full_url,
                'alt': alt_text
            })

    # Also look for picture elements
    for picture in soup.find_all('picture'):
        sources = picture.find_all('source')
        for source in sources:
            srcset = source.get('srcset')
            if srcset:
                # Take the first URL from srcset
                url = srcset.split(',')[0].split()[0]
                full_url = urljoin(base_url, url)
                if not full_url.startswith('data:'):
                    images.append({
                        'url': full_url,
                        'alt': ''
                    })

    return images

def download_image(url, output_path, headers=None, max_retries=3):
    """Download an image with retry logic"""
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.notion.so/'
        }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()

            # Verify it's actually an image
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type and 'octet-stream' not in content_type:
                print(f"  Warning: URL doesn't appear to be an image: {content_type}")

            # Write to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True

        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

    return False

def main():
    url = "https://www.notion.so/sagnikm/Who-is-Adam-SGD-Might-Be-All-We-Need-For-RLVR-In-LLMs-1cd2c74770c080de9cbbf74db14286b6"
    output_dir = Path("/home/limo/ccblog/blog/adam-sgd-rlvr")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching Notion page: {url}")
    try:
        html_content = get_notion_page(url)
    except Exception as e:
        print(f"Error fetching page: {e}")
        return

    print("Extracting images...")
    images = extract_images(html_content, url)

    if not images:
        print("No images found on the page")
        return

    print(f"Found {len(images)} images")

    # Download images
    manifest = []
    successful = 0

    for idx, img_info in enumerate(images, 1):
        img_url = img_info['url']
        alt_text = img_info['alt']

        # Generate filename
        parsed_url = urlparse(img_url)
        original_filename = Path(parsed_url.path).name

        # Use alt text if available and meaningful
        if alt_text and len(alt_text) > 3:
            # Sanitize alt text for filename
            base_name = sanitize_filename(alt_text[:50])  # Limit length
            extension = Path(original_filename).suffix or '.png'
            filename = f"{base_name}{extension}"
        else:
            filename = original_filename or f"image_{idx}.png"

        # Sanitize the final filename
        filename = sanitize_filename(filename)

        # Avoid conflicts
        output_path = output_dir / filename
        counter = 1
        while output_path.exists():
            stem = Path(filename).stem
            ext = Path(filename).suffix
            filename = f"{stem}_{counter}{ext}"
            output_path = output_dir / filename
            counter += 1

        print(f"Downloading [{idx}/{len(images)}]: {filename}")
        print(f"  URL: {img_url}")

        if download_image(img_url, output_path):
            successful += 1
            manifest.append({
                'filename': filename,
                'original_url': img_url,
                'alt_text': alt_text,
                'size_bytes': output_path.stat().st_size
            })
            print(f"  Success: {output_path}")
        else:
            print(f"  Failed to download")

        # Be polite to the server
        time.sleep(0.5)

    # Save manifest
    import json
    manifest_path = output_dir / "images.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Download complete!")
    print(f"Successfully downloaded: {successful}/{len(images)} images")
    print(f"Saved to: {output_dir}")
    print(f"Manifest: {manifest_path}")
    print(f"{'='*60}")

    # Verify no spaces in filenames
    files_with_spaces = []
    for file in output_dir.glob("*"):
        if file.is_file() and ' ' in file.name:
            files_with_spaces.append(file.name)

    if files_with_spaces:
        print(f"\nWARNING: Found {len(files_with_spaces)} files with spaces in names:")
        for fname in files_with_spaces:
            print(f"  - {fname}")
    else:
        print("\nAll filenames are properly sanitized (no spaces)")

if __name__ == "__main__":
    main()
