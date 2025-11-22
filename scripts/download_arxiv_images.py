#!/usr/bin/env python3
"""
Download all images from arXiv article 2510.02425v1
"""

import requests
import json
from pathlib import Path
from urllib.parse import urljoin
import time

# Base URL for the article
BASE_URL = "https://arxiv.org/html/2510.02425v1/"

# Output directory
OUTPUT_DIR = Path("/Users/limo/Documents/GithubRepo/ccblog/blog/arxiv-2510.02425-perceive")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# List of all images to download based on the article structure
images = []

# Main figures (x1.png through x39.png)
for i in range(1, 40):
    images.append(f"x{i}.png")

# Additional artwork image
images.append("figures/artwork_10256.jpg")

# Download configuration
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Track download results
results = {
    "successful": [],
    "failed": [],
    "skipped": []
}

def download_image(image_path):
    """Download a single image with retry logic"""
    url = urljoin(BASE_URL, image_path)

    # Determine output filename
    if "/" in image_path:
        # For paths like "figures/artwork_10256.jpg", flatten the name
        filename = image_path.replace("/", "_")
    else:
        filename = image_path

    output_path = OUTPUT_DIR / filename

    # Skip if already exists
    if output_path.exists():
        print(f"✓ Skipping (already exists): {filename}")
        results["skipped"].append(filename)
        return True

    # Try to download with retries
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Downloading: {url} -> {filename} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                # Verify it's actually an image (not an error page)
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type or len(response.content) > 1000:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    print(f"✓ Successfully downloaded: {filename} ({len(response.content)} bytes)")
                    results["successful"].append({
                        "filename": filename,
                        "original_url": url,
                        "size": len(response.content),
                        "content_type": content_type
                    })
                    return True
                else:
                    print(f"✗ Invalid content type or size: {content_type}, {len(response.content)} bytes")
                    if attempt == max_retries - 1:
                        results["failed"].append({
                            "filename": filename,
                            "url": url,
                            "error": f"Invalid content: {content_type}"
                        })
                    continue
            elif response.status_code == 404:
                print(f"✗ Not found (404): {filename}")
                results["failed"].append({
                    "filename": filename,
                    "url": url,
                    "error": "404 Not Found"
                })
                return False
            else:
                print(f"✗ HTTP {response.status_code}: {filename}")
                if attempt == max_retries - 1:
                    results["failed"].append({
                        "filename": filename,
                        "url": url,
                        "error": f"HTTP {response.status_code}"
                    })
                time.sleep(1)
                continue

        except Exception as e:
            print(f"✗ Error downloading {filename}: {e}")
            if attempt == max_retries - 1:
                results["failed"].append({
                    "filename": filename,
                    "url": url,
                    "error": str(e)
                })
            time.sleep(1)

    return False

def main():
    print(f"Starting download of {len(images)} images from arXiv article 2510.02425v1")
    print(f"Output directory: {OUTPUT_DIR}")
    print("-" * 80)

    for image_path in images:
        download_image(image_path)
        time.sleep(0.5)  # Be respectful to the server

    print("\n" + "=" * 80)
    print("DOWNLOAD SUMMARY")
    print("=" * 80)
    print(f"✓ Successfully downloaded: {len(results['successful'])} images")
    print(f"○ Skipped (already exist): {len(results['skipped'])} images")
    print(f"✗ Failed: {len(results['failed'])} images")

    if results['failed']:
        print("\nFailed downloads:")
        for item in results['failed']:
            print(f"  - {item['filename']}: {item['error']}")

    # Save manifest
    manifest_path = OUTPUT_DIR / "images.json"
    with open(manifest_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nManifest saved to: {manifest_path}")

    # List all downloaded files
    downloaded_files = sorted(OUTPUT_DIR.glob("*"))
    image_files = [f for f in downloaded_files if f.suffix in ['.png', '.jpg', '.jpeg', '.gif', '.webp']]

    print(f"\nTotal files in directory: {len(image_files)} images")
    print("\nDownloaded images:")
    for f in image_files:
        size_kb = f.stat().st_size / 1024
        print(f"  - {f.name} ({size_kb:.1f} KB)")

if __name__ == "__main__":
    main()
