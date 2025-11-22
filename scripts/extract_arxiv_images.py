#!/usr/bin/env python3
"""
Script to download and extract images from arXiv papers.
"""

import os
import json
import requests
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io

def download_pdf(arxiv_id, output_path):
    """Download PDF from arXiv."""
    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    print(f"Downloading PDF from {url}...")

    response = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    response.raise_for_status()

    with open(output_path, 'wb') as f:
        f.write(response.content)

    print(f"PDF downloaded to {output_path}")
    return output_path

def extract_images_from_pdf(pdf_path, output_dir):
    """Extract all images from a PDF file."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    images_info = []
    image_count = 0

    print(f"Processing {len(doc)} pages...")

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)

        print(f"Page {page_num + 1}: Found {len(image_list)} images")

        for img_index, img in enumerate(image_list):
            xref = img[0]

            # Extract image bytes
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            # Generate filename
            image_count += 1
            filename = f"figure_{image_count:03d}.{image_ext}"
            filepath = output_dir / filename

            # Save image
            with open(filepath, "wb") as img_file:
                img_file.write(image_bytes)

            # Try to get image dimensions
            try:
                with Image.open(io.BytesIO(image_bytes)) as pil_img:
                    width, height = pil_img.size
            except:
                width, height = None, None

            # Store metadata
            images_info.append({
                "filename": filename,
                "page": page_num + 1,
                "format": image_ext,
                "width": width,
                "height": height,
                "size_bytes": len(image_bytes)
            })

            print(f"  Saved: {filename} ({image_ext}, {len(image_bytes)} bytes)")

    doc.close()

    # Save manifest
    manifest_path = output_dir / "images.json"
    with open(manifest_path, 'w') as f:
        json.dump({
            "arxiv_id": "2306.02572",
            "paper_title": "Introduction to Latent Variable Energy-Based Models: A Path Towards Autonomous Machine Intelligence",
            "total_images": image_count,
            "images": images_info
        }, f, indent=2)

    print(f"\nManifest saved to {manifest_path}")

    return image_count, images_info

def main():
    arxiv_id = "2306.02572"
    output_dir = Path("/Users/limo/Documents/GithubRepo/ccblog/blog/latent-variable-ebm")
    pdf_path = output_dir / f"{arxiv_id}.pdf"

    # Download PDF
    download_pdf(arxiv_id, pdf_path)

    # Extract images
    image_count, images_info = extract_images_from_pdf(pdf_path, output_dir)

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total images extracted: {image_count}")
    print(f"Output directory: {output_dir}")
    print(f"\nImage files:")
    for img in images_info:
        print(f"  - {img['filename']} (Page {img['page']}, {img['format']}, {img['size_bytes']} bytes)")

if __name__ == "__main__":
    main()
