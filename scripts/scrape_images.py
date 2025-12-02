#!/usr/bin/env python3
"""
Image scraper for blog articles
Downloads images from article content to organized directories
"""

import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse
import json
import re
from typing import List, Dict
import time

class ImageScraper:
    def __init__(self, url: str, output_dir: str):
        self.url = url
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.downloaded_images = []
        self.failed_images = []

    def sanitize_filename(self, filename: str) -> str:
        """Remove special characters and spaces from filename"""
        # Remove any path components
        filename = Path(filename).name
        # Replace spaces and special space characters with underscores
        filename = re.sub(r'[\s\u00a0\u202f\u2009\u200a]+', '_', filename)
        # Remove other problematic characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Remove multiple consecutive underscores
        filename = re.sub(r'_+', '_', filename)
        return filename

    def get_page_content(self) -> BeautifulSoup:
        """Fetch and parse the webpage"""
        print(f"Fetching URL: {self.url}")
        response = self.session.get(self.url, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')

    def extract_images(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract image URLs from article content"""
        images = []

        # Try to find the main article content
        article_selectors = [
            'article',
            '.article-content',
            '.post-content',
            '.entry-content',
            'main',
            '[role="main"]'
        ]

        content = None
        for selector in article_selectors:
            content = soup.select_one(selector)
            if content:
                print(f"Found content using selector: {selector}")
                break

        if not content:
            print("No specific content area found, using entire body")
            content = soup

        # Find all img tags in content
        img_tags = content.find_all('img')
        print(f"Found {len(img_tags)} img tags")

        for idx, img in enumerate(img_tags):
            # Get image source
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if not src:
                continue

            # Skip data URIs and SVG placeholders
            if src.startswith('data:') or 'placeholder' in src.lower():
                continue

            # Convert relative URLs to absolute
            src = urljoin(self.url, src)

            # Get alt text for filename generation
            alt = img.get('alt', '').strip()

            images.append({
                'url': src,
                'alt': alt,
                'index': idx,
                'type': 'img'
            })

        # Also check figure tags (which might contain images in data-src or other attributes)
        figures = content.find_all('figure')
        print(f"Found {len(figures)} figure tags")

        for idx, fig in enumerate(figures):
            # Look for img within figure
            img = fig.find('img')
            if img:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src and not src.startswith('data:'):
                    src = urljoin(self.url, src)
                    alt = img.get('alt', '').strip()
                    # Check if not already added
                    if not any(i['url'] == src for i in images):
                        images.append({
                            'url': src,
                            'alt': alt,
                            'index': len(images),
                            'type': 'img'
                        })
            else:
                # Check for data-src on figure itself or child elements
                for elem in [fig] + fig.find_all():
                    src = elem.get('data-src') or elem.get('src')
                    if src and not src.startswith('data:'):
                        # Filter out non-image files
                        src_lower = src.lower()
                        if any(src_lower.endswith(ext) for ext in ['.js', '.css', '.txt', '.json', '.xml']):
                            continue

                        src = urljoin(self.url, src)
                        # Try to get caption text for alt
                        figcaption = fig.find('figcaption')
                        alt = figcaption.get_text().strip() if figcaption else ''
                        if not any(i.get('url') == src for i in images):
                            images.append({
                                'url': src,
                                'alt': alt,
                                'index': len(images),
                                'type': 'img'
                            })
                            break

        # Extract inline SVG elements
        svgs = content.find_all('svg')
        print(f"Found {len(svgs)} inline SVG elements")

        for idx, svg in enumerate(svgs):
            # Get caption or nearby text for naming
            parent_fig = svg.find_parent('figure')
            alt = ''
            if parent_fig:
                figcaption = parent_fig.find('figcaption')
                if figcaption:
                    alt = figcaption.get_text().strip()[:100]  # Limit length

            images.append({
                'svg_content': str(svg),
                'alt': alt,
                'index': len(images),
                'type': 'svg'
            })

        # Also check meta tags for cover/social images
        og_image = soup.find('meta', property='og:image')
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})

        for meta_tag in [og_image, twitter_image]:
            if meta_tag and meta_tag.get('content'):
                src = urljoin(self.url, meta_tag['content'])
                if not any(i.get('url') == src for i in images):
                    images.append({
                        'url': src,
                        'alt': 'cover-image',
                        'index': len(images),
                        'type': 'cover'
                    })
                    print(f"Found cover/social image: {src}")

        return images

    def generate_filename(self, img_info: Dict, existing_files: set) -> str:
        """Generate a meaningful filename for the image"""
        img_type = img_info.get('type', 'img')
        alt = img_info['alt']
        idx = img_info['index']

        # Handle SVG type separately
        if img_type == 'svg':
            ext = '.svg'
            if alt and len(alt) > 3:
                base_name = re.sub(r'[^\w\s-]', '', alt.lower())
                base_name = re.sub(r'[\s_-]+', '-', base_name).strip('-')
                base_name = base_name[:50]
            else:
                base_name = f'diagram-{idx+1}'
        else:
            url = img_info['url']
            # Get original filename from URL
            parsed = urlparse(url)
            original_name = Path(parsed.path).name

            # Get file extension
            ext = Path(original_name).suffix
            if not ext or ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                ext = '.jpg'

            # Generate base name from alt text if available and meaningful
            if alt and len(alt) > 3 and not alt.lower() in ['image', 'img', 'photo', 'picture', 'cover-image']:
                # Clean alt text for filename
                base_name = re.sub(r'[^\w\s-]', '', alt.lower())
                base_name = re.sub(r'[\s_-]+', '-', base_name).strip('-')
                base_name = base_name[:50]  # Limit length
            else:
                # Use original filename without extension
                base_name = Path(original_name).stem
                if not base_name or len(base_name) < 3:
                    base_name = f'image-{idx+1}'

        # Sanitize the base name
        base_name = self.sanitize_filename(base_name)

        # Ensure uniqueness
        filename = f"{base_name}{ext}"
        counter = 1
        while filename in existing_files:
            filename = f"{base_name}-{counter}{ext}"
            counter += 1

        return filename

    def download_image(self, url: str, filepath: Path, max_retries: int = 3) -> bool:
        """Download a single image with retry logic"""
        for attempt in range(max_retries):
            try:
                print(f"  Downloading: {url}")
                response = self.session.get(url, timeout=30, stream=True)
                response.raise_for_status()

                # Write to file
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                # Verify file size
                if filepath.stat().st_size < 100:
                    print(f"  Warning: File size too small ({filepath.stat().st_size} bytes)")
                    filepath.unlink()
                    return False

                print(f"  Saved to: {filepath}")
                return True

            except Exception as e:
                print(f"  Attempt {attempt+1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return False

        return False

    def scrape(self) -> Dict:
        """Main scraping method"""
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Fetch and parse page
        soup = self.get_page_content()

        # Extract images
        images = self.extract_images(soup)
        print(f"\nFound {len(images)} images to process\n")

        if not images:
            return {
                'success': False,
                'message': 'No images found in article',
                'total_found': 0,
                'total_downloaded': 0
            }

        # Download/save images
        existing_files = set()

        for img_info in images:
            filename = self.generate_filename(img_info, existing_files)
            filepath = self.output_dir / filename
            existing_files.add(filename)

            img_type = img_info.get('type', 'img')

            if img_type == 'svg':
                # Save inline SVG content
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(img_info['svg_content'])
                    print(f"  Saved SVG to: {filepath}")
                    self.downloaded_images.append({
                        'filename': filename,
                        'type': 'svg',
                        'alt_text': img_info['alt'],
                        'size_bytes': filepath.stat().st_size
                    })
                except Exception as e:
                    print(f"  Failed to save SVG: {str(e)}")
                    self.failed_images.append({
                        'type': 'svg',
                        'intended_filename': filename,
                        'error': str(e)
                    })
            else:
                # Download image from URL
                if self.download_image(img_info['url'], filepath):
                    self.downloaded_images.append({
                        'filename': filename,
                        'original_url': img_info['url'],
                        'type': img_type,
                        'alt_text': img_info['alt'],
                        'size_bytes': filepath.stat().st_size
                    })
                else:
                    self.failed_images.append({
                        'url': img_info['url'],
                        'intended_filename': filename
                    })

        # Verify no spaces in filenames
        for file in self.output_dir.glob('*'):
            if ' ' in file.name or '\u00a0' in file.name or '\u202f' in file.name:
                new_name = self.sanitize_filename(file.name)
                print(f"Renaming '{file.name}' to '{new_name}' (removing spaces)")
                file.rename(self.output_dir / new_name)

        # Save manifest
        manifest = {
            'source_url': self.url,
            'total_found': len(images),
            'total_downloaded': len(self.downloaded_images),
            'total_failed': len(self.failed_images),
            'images': self.downloaded_images,
            'failed': self.failed_images
        }

        manifest_path = self.output_dir / 'images.json'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Total images found: {len(images)}")
        print(f"Successfully downloaded/saved: {len(self.downloaded_images)}")
        print(f"Failed: {len(self.failed_images)}")
        print(f"Output directory: {self.output_dir.absolute()}")
        print(f"Manifest saved to: {manifest_path.absolute()}")

        if self.failed_images:
            print(f"\nFailed downloads:")
            for failed in self.failed_images:
                if 'url' in failed:
                    print(f"  - {failed['url']}")
                else:
                    print(f"  - {failed.get('intended_filename', 'unknown')} (SVG)")

        return manifest


def main():
    import sys

    if len(sys.argv) < 3:
        print("Usage: python scrape_images.py <url> <output_dir>")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2]

    scraper = ImageScraper(url, output_dir)
    scraper.scrape()


if __name__ == '__main__':
    main()
