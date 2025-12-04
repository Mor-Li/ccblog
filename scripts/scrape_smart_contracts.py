#!/usr/bin/env python3
"""
Script to scrape images from Anthropic's smart contracts blog post
"""

import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import time
import re

def sanitize_filename(filename):
    """Remove special characters and spaces from filename"""
    # Replace spaces and special space characters with underscores
    filename = re.sub(r'[\s\u202f\u00a0]+', '_', filename)
    # Remove other invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    return filename

def get_blog_name_from_url(url):
    """Extract blog name from URL"""
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split('/') if p]
    if path_parts:
        return path_parts[-1]
    return parsed.netloc.replace('.', '_')

def download_image(img_url, save_path, headers, max_retries=3):
    """Download an image with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.get(img_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()

            # Write image to file
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verify the file was written
            if os.path.getsize(save_path) > 0:
                print(f"✓ Downloaded: {os.path.basename(save_path)} ({os.path.getsize(save_path)} bytes)")
                return True
            else:
                print(f"✗ Downloaded file is empty: {save_path}")
                return False

        except Exception as e:
            print(f"  Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                print(f"✗ Failed to download: {img_url}")
                return False
    return False

def scrape_blog_images(url, output_dir):
    """Main function to scrape images from a blog post"""

    # Setup headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://google.com',
    }

    print(f"Fetching: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return

    # Parse HTML
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the main content area (adjust selector based on page structure)
    # Try common article content selectors
    main_content = (
        soup.find('article') or
        soup.find('main') or
        soup.find('d-article') or  # Distill article format
        soup.find(class_=re.compile('content|article|post', re.I)) or
        soup.find('body') or
        soup
    )

    # Find all images in various formats
    images = []

    # Find traditional img tags
    img_tags = main_content.find_all('img')

    # Filter out likely non-content images (favicons, logos, etc.)
    content_images = []
    for img in img_tags:
        src = img.get('src', '')
        # Skip favicons, icons, and other small UI elements
        if any(skip in src.lower() for skip in ['favicon', 'logo', 'icon', 'avatar']):
            continue
        content_images.append(img)

    images.extend(content_images)

    # Find picture elements with source tags
    picture_tags = main_content.find_all('picture')
    for picture in picture_tags:
        sources = picture.find_all('source')
        for source in sources:
            # Create a fake img tag with the source srcset
            srcset = source.get('srcset')
            if srcset:
                # Take the first URL from srcset
                url = srcset.split(',')[0].split()[0]
                fake_img = soup.new_tag('img')
                fake_img['src'] = url
                fake_img['alt'] = picture.find('img').get('alt', '') if picture.find('img') else ''
                images.append(fake_img)

    # Find figure elements (but don't double count imgs already found)
    figures = main_content.find_all('figure')

    print(f"Found {len(images)} images in the content area (img tags: {len(img_tags)}, filtered: {len(content_images)}, picture elements: {len(picture_tags)}, figures: {len(figures)})")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Track downloaded images
    downloaded_images = []
    failed_images = []
    counter = 1

    for img in images:
        # Get image URL
        img_url = img.get('src') or img.get('data-src')
        if not img_url:
            continue

        # Convert relative URLs to absolute
        img_url = urljoin(url, img_url)

        # Skip SVG data URLs and very small images (likely icons)
        if img_url.startswith('data:'):
            continue

        # Get alt text for better filename
        alt_text = img.get('alt', '')

        # Determine filename
        original_filename = os.path.basename(urlparse(img_url).path)

        # Create descriptive filename from alt text if available
        if alt_text and len(alt_text) > 3:
            # Sanitize alt text for filename
            base_name = sanitize_filename(alt_text.lower()[:50])
            extension = os.path.splitext(original_filename)[1] or '.jpg'
            filename = f"{base_name}{extension}"
        else:
            filename = original_filename if original_filename else f"image_{counter}.jpg"

        # Ensure no spaces in filename
        filename = sanitize_filename(filename)

        # Handle duplicate filenames
        save_path = os.path.join(output_dir, filename)
        if os.path.exists(save_path):
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{counter}{ext}"
            save_path = os.path.join(output_dir, filename)

        # Download image
        if download_image(img_url, save_path, headers):
            downloaded_images.append({
                'filename': filename,
                'original_url': img_url,
                'alt_text': alt_text,
                'size': os.path.getsize(save_path)
            })
        else:
            failed_images.append({
                'url': img_url,
                'alt_text': alt_text
            })

        counter += 1
        time.sleep(0.5)  # Be polite, don't hammer the server

    # Create manifest file
    manifest = {
        'source_url': url,
        'download_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_found': len(images),
        'total_downloaded': len(downloaded_images),
        'total_failed': len(failed_images),
        'images': downloaded_images,
        'failed': failed_images
    }

    manifest_path = os.path.join(output_dir, 'images.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Verify no filenames contain spaces
    files_with_spaces = [f for f in os.listdir(output_dir) if ' ' in f and f.endswith(('.jpg', '.png', '.gif', '.webp', '.svg'))]
    if files_with_spaces:
        print(f"\n⚠️  WARNING: Found {len(files_with_spaces)} files with spaces in their names:")
        for f in files_with_spaces:
            print(f"  - {f}")

    # Print summary
    print("\n" + "="*60)
    print("SCRAPING SUMMARY")
    print("="*60)
    print(f"Source URL: {url}")
    print(f"Output Directory: {output_dir}")
    print(f"Total images found: {len(images)}")
    print(f"Successfully downloaded: {len(downloaded_images)}")
    print(f"Failed downloads: {len(failed_images)}")
    print(f"Manifest saved to: {manifest_path}")

    if downloaded_images:
        print("\nDownloaded images:")
        for img in downloaded_images:
            print(f"  - {img['filename']} ({img['size']} bytes)")
            if img['alt_text']:
                print(f"    Alt: {img['alt_text']}")

    if failed_images:
        print("\nFailed downloads:")
        for img in failed_images:
            print(f"  - {img['url']}")

if __name__ == '__main__':
    url = 'https://red.anthropic.com/2025/smart-contracts/'
    blog_name = 'smart-contracts'
    output_dir = f'/home/limo/ccblog/blog/{blog_name}'

    scrape_blog_images(url, output_dir)
