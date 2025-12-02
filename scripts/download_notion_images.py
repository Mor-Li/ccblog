#!/usr/bin/env python3
"""
Script to download images from the Notion page about SGD vs Adam in RLVR
"""

import requests
import json
from pathlib import Path
from urllib.parse import unquote, urlparse
import time

# Image URLs extracted from the page
images = [
    {
        "url": "https://www.notion.so/image/attachment%3A32ff8228-aeb7-4aaa-a141-12ceae347ff3%3Aimage_(11).png?table=block&id=2b92c747-70c0-80c3-a85b-d7d559348d6a&spaceId=55926427-5248-4664-8776-832f9f128827&width=1250&userId=&cache=v2",
        "alt": "training-dynamics-comparison",
        "index": 1
    },
    {
        "url": "https://www.notion.so/image/attachment%3Ab077f5ba-a6a7-46fb-ad01-8bd46e3eb42b%3Aimage_(12).png?table=block&id=2b92c747-70c0-80ac-8945-e82a89bfd48f&spaceId=55926427-5248-4664-8776-832f9f128827&width=1420&userId=&cache=v2",
        "alt": "validation-curves",
        "index": 2
    },
    {
        "url": "https://www.notion.so/image/attachment%3A8a76d0ab-3d66-4446-84ba-d7a8c1bd8e29%3ACode_Generated_Image-9.png?table=block&id=2ba2c747-70c0-8041-b338-c2ef511909dc&spaceId=55926427-5248-4664-8776-832f9f128827&width=1420&userId=&cache=v2",
        "alt": "evaluation-results-1024",
        "index": 3
    },
    {
        "url": "https://www.notion.so/image/attachment%3A37bae3fb-0398-4b7f-b507-0fd66919e04a%3ACode_Generated_Image-8.png?table=block&id=2ba2c747-70c0-804f-88c1-cd5f0e8cd358&spaceId=55926427-5248-4664-8776-832f9f128827&width=1420&userId=&cache=v2",
        "alt": "evaluation-results-8192",
        "index": 4
    },
    {
        "url": "https://www.notion.so/image/attachment%3A5a0782ab-d919-4cbc-ade2-e1520e5abfdb%3Aimage.png?table=block&id=2b92c747-70c0-80ab-a68c-dedce734a85f&spaceId=55926427-5248-4664-8776-832f9f128827&width=670&userId=&cache=v2",
        "alt": "loss-landscape-illustration",
        "index": 5
    },
    {
        "url": "https://www.notion.so/image/attachment%3A502bf169-1e0d-45d8-ad64-99bd9da7ec75%3Aimage_(14).png?table=block&id=2b92c747-70c0-808c-894c-ea5e61a5918d&spaceId=55926427-5248-4664-8776-832f9f128827&width=1420&userId=&cache=v2",
        "alt": "sparsity-comparison",
        "index": 6
    }
]

def download_image(url: str, output_path: Path, max_retries: int = 3) -> bool:
    """Download an image with retry logic"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for attempt in range(max_retries):
        try:
            print(f"Downloading {output_path.name}... (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Verify it's actually an image
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type.lower():
                print(f"Warning: URL did not return an image (content-type: {content_type})")
                return False

            # Write the image
            output_path.write_bytes(response.content)

            # Verify file size
            file_size = output_path.stat().st_size
            if file_size == 0:
                print(f"Error: Downloaded file is empty")
                return False

            print(f"✓ Successfully downloaded {output_path.name} ({file_size:,} bytes)")
            return True

        except Exception as e:
            print(f"✗ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait before retrying

    return False

def main():
    # Create output directory
    output_dir = Path("/home/limo/ccblog/blog/adam-sgd-rlvr")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {len(images)} images to {output_dir}")
    print("-" * 80)

    # Track results
    successful = []
    failed = []
    manifest = []

    for img_info in images:
        url = img_info['url']
        alt = img_info['alt']
        index = img_info['index']

        # Generate filename - replace spaces with underscores
        if alt and alt.strip():
            filename = f"{index:02d}_{alt.replace(' ', '_').replace('/', '_')}.png"
        else:
            filename = f"{index:02d}_image.png"

        # Remove any remaining special characters that might cause issues
        filename = filename.replace('\u202f', '_').replace('\u00a0', '_')

        output_path = output_dir / filename

        # Download the image
        success = download_image(url, output_path)

        if success:
            successful.append(filename)
            manifest.append({
                'filename': filename,
                'original_url': url,
                'alt': alt,
                'index': index
            })
        else:
            failed.append(filename)

        # Be nice to the server
        time.sleep(1)

    print("\n" + "=" * 80)
    print(f"Download Summary:")
    print(f"  Total images: {len(images)}")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(failed)}")

    if successful:
        print(f"\n✓ Successfully downloaded images:")
        for filename in successful:
            print(f"  - {filename}")

    if failed:
        print(f"\n✗ Failed to download:")
        for filename in failed:
            print(f"  - {filename}")

    # Save manifest
    manifest_path = output_dir / "images.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"\n✓ Manifest saved to: {manifest_path}")

    return len(successful) == len(images)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
