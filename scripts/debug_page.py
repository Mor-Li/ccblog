#!/usr/bin/env python3
"""
Debug script to see what HTML we're getting from the page
"""

import requests
from bs4 import BeautifulSoup

url = 'https://red.anthropic.com/2025/smart-contracts/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

print(f"Fetching: {url}")
try:
    response = requests.get(url, headers=headers, timeout=30)
    print(f"Status code: {response.status_code}")
    print(f"Content length: {len(response.content)}")

    # Save HTML for inspection
    with open('/home/limo/ccblog/scripts/page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("HTML saved to: /home/limo/ccblog/scripts/page.html")

    # Parse and look for images
    soup = BeautifulSoup(response.content, 'html.parser')

    # Check for all img tags
    all_imgs = soup.find_all('img')
    print(f"\nTotal <img> tags found: {len(all_imgs)}")

    # Check for picture tags
    all_pictures = soup.find_all('picture')
    print(f"Total <picture> tags found: {len(all_pictures)}")

    # Check for figure tags
    all_figures = soup.find_all('figure')
    print(f"Total <figure> tags found: {len(all_figures)}")

    # Print first few img tags
    print("\nFirst 5 <img> tags:")
    for i, img in enumerate(all_imgs[:5], 1):
        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        alt = img.get('alt', 'No alt')
        print(f"{i}. src={src}, alt={alt}")

    # Look for Next.js or React image components
    print("\nLooking for common class patterns:")
    for class_name in ['next-image', 'gatsby-image', 'wp-image', 'post-image', 'article-image']:
        elements = soup.find_all(class_=lambda x: x and class_name in x)
        if elements:
            print(f"  Found {len(elements)} elements with '{class_name}' in class")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
