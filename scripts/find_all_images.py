#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re

url = "https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

response = session.get(url, timeout=30)
soup = BeautifulSoup(response.content, 'html.parser')

# Find all elements with image-like URLs
image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']

print("Looking for image URLs in HTML...\n")

# Search in all attributes
for tag in soup.find_all():
    for attr_name, attr_value in tag.attrs.items():
        if isinstance(attr_value, str):
            # Check if it looks like an image URL
            if any(ext in attr_value.lower() for ext in image_extensions):
                print(f"Tag: {tag.name}, Attr: {attr_name}, Value: {attr_value[:200]}")

# Also search in the raw HTML for image URLs
print("\n\nSearching raw HTML for image URLs...\n")
html_text = response.text
image_urls = set()

# Pattern to find URLs with image extensions
pattern = r'(https?://[^\s\'"<>]+?\.(?:jpg|jpeg|png|gif|webp|svg))'
matches = re.findall(pattern, html_text, re.IGNORECASE)

for match in matches:
    image_urls.add(match)

print(f"Found {len(image_urls)} unique image URLs:")
for url in sorted(image_urls):
    print(f"  - {url}")

# Check for inline SVGs
svgs = soup.find_all('svg')
print(f"\n\nFound {len(svgs)} inline SVG elements")
