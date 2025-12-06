#!/usr/bin/env python3
"""
Script to scrape Google Research blog post content
"""

import requests
from bs4 import BeautifulSoup
import sys

def scrape_article(url):
    """Scrape the main article content from a Google Research blog post"""

    # Fetch the page
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    content = []

    # Get title
    title = soup.find('h1')
    if title:
        content.append(title.get_text(strip=True))
        content.append('')

    # Get metadata (date and authors)
    main_section = soup.find('main')
    if main_section:
        paragraphs = main_section.find_all('p', recursive=False)
        # First few paragraphs are usually metadata
        for i, p in enumerate(paragraphs[:3]):
            text = p.get_text(strip=True)
            if 'December' in text or '2025' in text or 'Researcher' in text:
                content.append(text)
        content.append('')

    # Find the main article content area
    # Google Research uses a specific structure, let's find the article body
    article_body = soup.find('main')

    if article_body:
        # Get all elements in order
        for element in article_body.find_all(['p', 'h2', 'h3', 'ul', 'ol', 'li']):
            # Skip navigation elements
            if element.find_parent(['nav', 'footer']):
                continue

            text = element.get_text(strip=True)

            # Skip empty elements
            if not text:
                continue

            # Skip unwanted sections
            if any(skip in text for skip in ['Quick links', 'Other posts of interest',
                                              'Labels:', 'Follow us', 'Copy link',
                                              'December 3, 2025', 'November', 'Share']):
                continue

            # Skip labels section
            if text in ['Generative AI', 'Machine Intelligence', 'Natural Language Processing']:
                continue

            # Format based on element type
            if element.name == 'h2':
                content.append('')
                content.append(f'## {text}')
                content.append('')
            elif element.name == 'h3':
                content.append('')
                content.append(f'### {text}')
                content.append('')
            elif element.name in ['ul', 'ol']:
                # Skip, we'll handle list items directly
                continue
            elif element.name == 'li':
                # Check if it's in the main content area
                parent_list = element.find_parent(['ul', 'ol'])
                if parent_list and not parent_list.find_parent(['nav', 'footer']):
                    # Avoid duplicate list items from nested structures
                    if len(text) > 10:  # Only meaningful list items
                        content.append(f'- {text}')
            elif element.name == 'p':
                content.append(text)
                content.append('')

    # Join and clean up
    result = '\n'.join(content)

    # Remove excessive blank lines
    while '\n\n\n' in result:
        result = result.replace('\n\n\n', '\n\n')

    return result.strip()

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://research.google/blog/titans-miras-helping-ai-have-long-term-memory/'

    try:
        content = scrape_article(url)
        print(content)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
