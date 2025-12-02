#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

url = "https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

response = session.get(url, timeout=30)
soup = BeautifulSoup(response.content, 'html.parser')

article = soup.find('article')
figures = article.find_all('figure')

print(f"Found {len(figures)} figures\n")

for i, fig in enumerate(figures[:3]):  # Print first 3
    print(f"Figure {i+1}:")
    print(f"HTML: {str(fig)[:500]}")
    print(f"\nAttributes: {fig.attrs}")

    # Check for images
    img = fig.find('img')
    if img:
        print(f"IMG tag found: {img.attrs}")

    # Check all elements with src or data-src
    for elem in fig.find_all():
        if elem.has_attr('src') or elem.has_attr('data-src'):
            print(f"Element with src: {elem.name} - {elem.attrs}")

    print("\n" + "="*80 + "\n")
