#!/usr/bin/env python3
"""
Scrape images from a Notion page using Playwright
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
from urllib.parse import urlparse, urljoin
import time
import re
import requests
import json

def sanitize_filename(filename):
    """Remove special characters and replace spaces with underscores"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace all types of spaces (including special unicode spaces) with underscores
    filename = re.sub(r'[\s\u00a0\u202f\u2009\u200a]+', '_', filename)
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    return filename.strip('_')

def download_image(url, output_path, max_retries=3):
    """Download an image with retry logic"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.notion.so/'
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()

            # Write to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True

        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    return False

def main():
    url = "https://www.notion.so/sagnikm/Who-is-Adam-SGD-Might-Be-All-We-Need-For-RLVR-In-LLMs-1cd2c74770c080de9cbbf74db14286b6"
    output_dir = Path("/home/limo/ccblog/blog/adam-sgd-rlvr")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()

        print(f"Loading page: {url}")
        page.goto(url, wait_until='networkidle', timeout=60000)

        # Scroll to load all images
        print("Scrolling to load all images...")
        page.evaluate("""
            () => {
                return new Promise((resolve) => {
                    let totalHeight = 0;
                    const distance = 500;
                    const timer = setInterval(() => {
                        const scrollHeight = document.body.scrollHeight;
                        window.scrollBy(0, distance);
                        totalHeight += distance;

                        if(totalHeight >= scrollHeight){
                            clearInterval(timer);
                            setTimeout(resolve, 1000);
                        }
                    }, 100);
                });
            }
        """)

        # Wait for images to load
        time.sleep(3)

        # Extract all image sources
        print("Extracting images...")
        images = page.evaluate("""
            () => {
                const images = [];
                const imgElements = document.querySelectorAll('img');

                imgElements.forEach(img => {
                    const src = img.src || img.getAttribute('data-src');
                    const alt = img.alt || '';

                    if (src && !src.startsWith('data:')) {
                        // Skip obvious icons and logos
                        if (!src.includes('notion-logo') &&
                            !src.includes('icon') &&
                            !alt.includes('icon') &&
                            !alt.includes('Callout')) {
                            images.push({
                                url: src,
                                alt: alt,
                                width: img.naturalWidth,
                                height: img.naturalHeight
                            });
                        }
                    }
                });

                return images;
            }
        """)

        browser.close()

    if not images:
        print("No images found on the page")
        return

    print(f"Found {len(images)} images")

    # Filter out very small images (likely icons)
    images = [img for img in images if img['width'] > 100 and img['height'] > 100]
    print(f"After filtering small images: {len(images)} images remain")

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
            base_name = sanitize_filename(alt_text[:50])
            extension = Path(original_filename).suffix or '.png'
            filename = f"{base_name}{extension}"
        else:
            # Use a descriptive name based on the order
            extension = Path(original_filename).suffix or '.png'
            filename = f"figure_{idx}{extension}"

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
        print(f"  URL: {img_url[:100]}...")
        print(f"  Size: {img_info['width']}x{img_info['height']}")

        if download_image(img_url, output_path):
            successful += 1
            manifest.append({
                'filename': filename,
                'original_url': img_url,
                'alt_text': alt_text,
                'dimensions': f"{img_info['width']}x{img_info['height']}",
                'size_bytes': output_path.stat().st_size
            })
            print(f"  Success: {output_path}")
        else:
            print(f"  Failed to download")

        time.sleep(0.5)

    # Save manifest
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

    # Print summary of downloaded images
    print("\n" + "="*60)
    print("Downloaded Images:")
    print("="*60)
    for item in manifest:
        print(f"  - {item['filename']}")
        if item['alt_text']:
            print(f"    Alt: {item['alt_text']}")
        print(f"    Size: {item['dimensions']} ({item['size_bytes']} bytes)")

if __name__ == "__main__":
    main()
