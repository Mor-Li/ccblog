#!/usr/bin/env python3
"""
Scrape Hugging Face blog post content
"""
import requests
from bs4 import BeautifulSoup
import sys

def scrape_hf_blog(url):
    """Scrape the main content from a Hugging Face blog post"""
    try:
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the main article content
        # Hugging Face blog posts typically use article tag or specific content divs
        article = soup.find('article')
        if not article:
            article = soup.find('main')
        if not article:
            article = soup.find('div', class_='prose')

        if not article:
            print("Could not find main article content", file=sys.stderr)
            return None

        # Extract text content preserving structure
        content_parts = []

        # Get title
        title = soup.find('h1')
        if title:
            content_parts.append(title.get_text().strip())
            content_parts.append('=' * len(title.get_text().strip()))
            content_parts.append('')

        # Extract all text from article, preserving paragraphs
        for element in article.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'code', 'li', 'blockquote']):
            text = element.get_text().strip()
            if text:
                # Add extra spacing for headers
                if element.name.startswith('h'):
                    content_parts.append('')
                    content_parts.append(text)
                    if element.name == 'h2':
                        content_parts.append('-' * len(text))
                    content_parts.append('')
                elif element.name == 'pre':
                    content_parts.append('')
                    content_parts.append(text)
                    content_parts.append('')
                else:
                    content_parts.append(text)

        full_text = '\n'.join(content_parts)

        return full_text

    except requests.RequestException as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error parsing content: {e}", file=sys.stderr)
        return None

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://huggingface.co/blog/continuous_batching'

    content = scrape_hf_blog(url)

    if content:
        print(content)
        print(f"\n\n[Stats: {len(content)} characters, {len(content.split())} words]", file=sys.stderr)
    else:
        sys.exit(1)
