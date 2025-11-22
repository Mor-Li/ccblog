#!/usr/bin/env python3
"""
Script to download all images from an arXiv paper using the PDF.
"""

import os
import json
import subprocess
from pathlib import Path
import fitz  # PyMuPDF

def extract_images_from_pdf(pdf_url, output_dir):
    """
    Extract all images from an arXiv PDF.

    Args:
        pdf_url: URL to the arXiv PDF
        output_dir: Directory to save images
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Download PDF
    pdf_path = output_path / 'paper.pdf'
    print(f"Downloading PDF from {pdf_url}...")
    subprocess.run(['curl', '-L', '-o', str(pdf_path), pdf_url], check=True)

    # Open PDF
    print(f"Opening PDF: {pdf_path}")
    pdf_document = fitz.open(pdf_path)

    downloaded_images = []
    image_count = 0

    # Iterate through pages
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        print(f"Processing page {page_num + 1}/{len(pdf_document)}...")

        # Get images from page
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            image_count += 1
            filename = f"figure_{image_count:03d}.{image_ext}"
            save_path = output_path / filename

            # Save image
            with open(save_path, "wb") as f:
                f.write(image_bytes)

            downloaded_images.append({
                'filename': filename,
                'page': page_num + 1,
                'size': len(image_bytes),
                'format': image_ext
            })

            print(f"  Extracted: {filename}")

    # Save total pages before closing
    total_pages = len(pdf_document)

    # Close PDF
    pdf_document.close()

    # Remove PDF file
    pdf_path.unlink()

    # Save manifest
    manifest = {
        'pdf_url': pdf_url,
        'total_pages': total_pages,
        'total_images': image_count,
        'images': downloaded_images
    }

    manifest_path = output_path / 'images.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total pages: {total_pages}")
    print(f"  Total images extracted: {image_count}")
    print(f"  Output directory: {output_path.absolute()}")
    print(f"  Manifest saved to: {manifest_path.absolute()}")
    print(f"{'='*60}")

    return manifest

if __name__ == '__main__':
    # Configuration
    pdf_url = 'https://arxiv.org/pdf/2511.14761'
    output_dir = '/Users/limo/Documents/GithubRepo/ccblog/blog/arc-vision-problem'

    # Run extraction
    extract_images_from_pdf(pdf_url, output_dir)
