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

# Check for article content
article = soup.find('article')
if article:
    print(f"Found article tag, length: {len(str(article))}")

    # Look for all image-related elements
    imgs = article.find_all('img')
    print(f"\nFound {len(imgs)} img tags")

    figures = article.find_all('figure')
    print(f"Found {len(figures)} figure tags")

    pictures = article.find_all('picture')
    print(f"Found {len(pictures)} picture tags")

    # Look for elements with image URLs in attributes
    elements_with_src = article.find_all(attrs={'src': True})
    print(f"Found {len(elements_with_src)} elements with src attribute")

    elements_with_data_src = article.find_all(attrs={'data-src': True})
    print(f"Found {len(elements_with_data_src)} elements with data-src attribute")

    # Check for Next.js image components or other patterns
    print("\nSample HTML snippet:")
    print(str(article)[:2000])
else:
    print("No article tag found")
    print("\nPage title:", soup.find('title').text if soup.find('title') else "No title")
    print("\nFirst 2000 characters of body:")
    if soup.body:
        print(str(soup.body)[:2000])
