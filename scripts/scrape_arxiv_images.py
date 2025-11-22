#!/usr/bin/env python3
"""
Script to download all images from an arXiv paper HTML page.
"""

import os
import json
import re
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time

def sanitize_filename(filename):
    """Remove special characters from filename."""
    return re.sub(r'[^\w\-_.]', '_', filename)

def download_image(url, save_path, headers=None):
    """Download an image from URL to save_path."""
    try:
        if headers is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            f.write(response.content)

        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def scrape_arxiv_images(paper_url, output_dir):
    """
    Scrape all images from an arXiv paper HTML page.

    Args:
        paper_url: URL to the arXiv HTML page
        output_dir: Directory to save images
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Fetch the HTML page
    print(f"Fetching HTML from {paper_url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    response = requests.get(paper_url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all images
    images = soup.find_all('img')

    downloaded_images = []
    failed_images = []

    print(f"\nFound {len(images)} image tags in the HTML")

    for idx, img in enumerate(images, 1):
        # Get image URL
        img_url = img.get('src')
        if not img_url:
            continue

        # Skip logos and UI elements
        alt_text = img.get('alt', '').lower()
        if any(skip in alt_text for skip in ['logo', 'icon']) or any(skip in img_url.lower() for skip in ['static/', 'logo']):
            continue

        # Make absolute URL
        img_url = urljoin(paper_url, img_url)

        # Get figure caption or alt text for filename
        caption = ""
        figure = img.find_parent('figure')
        if figure:
            caption_elem = figure.find('figcaption') or figure.find(class_='ltx_caption')
            if caption_elem:
                caption = caption_elem.get_text(strip=True)[:100]

        # Generate filename
        if caption and caption.startswith('Figure'):
            # Extract figure number
            fig_match = re.search(r'Figure\s+(\d+)', caption)
            if fig_match:
                filename = f"figure_{fig_match.group(1)}.png"
            else:
                filename = f"image_{idx:03d}.png"
        else:
            # Use URL filename or index
            url_path = urlparse(img_url).path
            url_filename = os.path.basename(url_path)
            if url_filename and '.' in url_filename:
                filename = sanitize_filename(url_filename)
            else:
                filename = f"image_{idx:03d}.png"

        save_path = output_path / filename

        # Download image
        print(f"Downloading {idx}/{len(images)}: {filename}")
        if download_image(img_url, save_path, headers):
            downloaded_images.append({
                'filename': filename,
                'original_url': img_url,
                'caption': caption,
                'alt_text': img.get('alt', '')
            })
        else:
            failed_images.append({
                'url': img_url,
                'filename': filename
            })

        # Be nice to the server
        time.sleep(0.5)

    # Save manifest
    manifest = {
        'paper_url': paper_url,
        'total_images_found': len(images),
        'successfully_downloaded': len(downloaded_images),
        'failed_downloads': len(failed_images),
        'images': downloaded_images,
        'failed': failed_images
    }

    manifest_path = output_path / 'images.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total images found: {len(images)}")
    print(f"  Successfully downloaded: {len(downloaded_images)}")
    print(f"  Failed downloads: {len(failed_images)}")
    print(f"  Output directory: {output_path.absolute()}")
    print(f"  Manifest saved to: {manifest_path.absolute()}")
    print(f"{'='*60}")

    if failed_images:
        print("\nFailed downloads:")
        for fail in failed_images:
            print(f"  - {fail['filename']}: {fail['url']}")

    return manifest

if __name__ == '__main__':
    # Configuration
    paper_url = 'https://arxiv.org/html/2511.14761v1'
    output_dir = '/Users/limo/Documents/GithubRepo/ccblog/blog/arc-vision-problem'

    # Run scraper
    scrape_arxiv_images(paper_url, output_dir)
