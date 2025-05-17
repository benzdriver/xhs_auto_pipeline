#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced usage example: News Scraper using Web Scraping Toolkit.

This example demonstrates how to build a news article scraper that:
1. Uses proxy rotation to avoid IP blocks
2. Solves CAPTCHAs when encountered
3. Caches results to avoid duplicate requests
4. Handles JavaScript-heavy websites
5. Tracks processing status across multiple stages
"""

import os
import time
import json
import datetime
import argparse
from urllib.parse import urlparse
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Import the toolkit components
from web_scraping_toolkit import ProxyManager, CaptchaSolver, CacheMechanism, WebScraper

# Load environment variables
load_dotenv()

# Output directory for scraped articles
OUTPUT_DIR = "scraped_news"

class NewsArticle:
    """Represents a news article with metadata and content."""
    
    def __init__(self, url, title=None, date=None, author=None, content=None):
        """Initialize a news article."""
        self.url = url
        self.title = title
        self.date = date
        self.author = author
        self.content = content
        self.domain = urlparse(url).netloc if url else None
        self.images = []
        self.timestamp = datetime.datetime.now().isoformat()
    
    def to_dict(self):
        """Convert article to dictionary for serialization."""
        return {
            "url": self.url,
            "title": self.title,
            "date": self.date,
            "author": self.author,
            "content": self.content,
            "domain": self.domain,
            "images": self.images,
            "timestamp": self.timestamp
        }
    
    def save_to_file(self, directory=OUTPUT_DIR):
        """Save article to a JSON file."""
        os.makedirs(directory, exist_ok=True)
        
        # Create a filename from the URL
        filename = f"{hash(self.url)}.json"
        filepath = os.path.join(directory, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        
        return filepath

class NewsScraperPipeline:
    """
    Pipeline for scraping news articles with multiple processing stages.
    """
    
    def __init__(self):
        """Initialize the news scraper pipeline."""
        # Set up toolkit components
        self.proxy_manager = ProxyManager()
        self.captcha_solver = CaptchaSolver()
        self.cache = CacheMechanism("news_scraper_cache")
        
        # Create the web scraper
        self.scraper = WebScraper(
            proxy_manager=self.proxy_manager,
            captcha_solver=self.captcha_solver,
            cache_mechanism=self.cache,
            browser_headless=True
        )
        
        # Create output directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        print(f"News scraper pipeline initialized")
    
    def extract_article_content(self, url):
        """
        Extract article content from a news URL.
        
        Args:
            url: The URL of the news article
            
        Returns:
            NewsArticle: The extracted article with content
        """
        # Check if this URL has already been processed
        if self.cache.is_processed_by_stage(url, "content_extraction"):
            print(f"Article already processed: {url}")
            
            # Check if the output file exists
            filename = f"{hash(url)}.json"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            if os.path.exists(filepath):
                print(f"Loading article from file: {filepath}")
                with open(filepath, 'r', encoding='utf-8') as f:
                    article_data = json.load(f)
                
                # Create article from data
                article = NewsArticle(
                    url=article_data.get("url"),
                    title=article_data.get("title"),
                    date=article_data.get("date"),
                    author=article_data.get("author"),
                    content=article_data.get("content")
                )
                article.images = article_data.get("images", [])
                article.timestamp = article_data.get("timestamp")
                
                return article
            else:
                # Output file is missing, reset processing status
                self.cache.reset_processing_status(url, "content_extraction")
        
        # Initialize an empty article
        article = NewsArticle(url=url)
        
        try:
            print(f"Fetching article: {url}")
            
            # Fetch the article - force browser mode for reliable content extraction
            response = self.scraper.get(url, force_browser=True)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title - different sites have different structures
            title_candidates = [
                soup.find('h1'),  # Most common
                soup.find('meta', property='og:title'),  # Open Graph
                soup.find('meta', name='twitter:title')  # Twitter cards
            ]
            
            for candidate in title_candidates:
                if candidate:
                    if candidate.name == 'meta':
                        article.title = candidate.get('content')
                    else:
                        article.title = candidate.text.strip()
                    break
            
            # Extract publication date
            date_candidates = [
                soup.find('meta', property='article:published_time'),  # Open Graph
                soup.find('meta', itemprop='datePublished'),  # Schema.org
                soup.find('time')  # HTML5 time tag
            ]
            
            for candidate in date_candidates:
                if candidate:
                    if candidate.name == 'meta':
                        article.date = candidate.get('content')
                    elif candidate.name == 'time':
                        article.date = candidate.get('datetime') or candidate.text.strip()
                    break
            
            # Extract author
            author_candidates = [
                soup.find('meta', property='article:author'),  # Open Graph
                soup.find('meta', name='author'),  # Meta author
                soup.find(['a', 'span'], class_=['author', 'byline'])  # Common author classes
            ]
            
            for candidate in author_candidates:
                if candidate:
                    if candidate.name == 'meta':
                        article.author = candidate.get('content')
                    else:
                        article.author = candidate.text.strip()
                    break
            
            # Extract content
            content_containers = [
                soup.find('article'),  # Most common for news sites
                soup.find('div', class_=['article-content', 'content', 'story-body']),  # Common content classes
                soup.find('div', id=['article-content', 'content', 'story-body']),  # Common content IDs
                soup.find('div', itemprop='articleBody')  # Schema.org
            ]
            
            # Find the first valid content container
            content_container = None
            for container in content_containers:
                if container:
                    content_container = container
                    break
            
            # If no specific container found, use the entire body
            if not content_container:
                content_container = soup.find('body')
            
            if content_container:
                # Remove unwanted elements
                for unwanted in content_container.find_all(['script', 'style', 'nav', 'header', 'footer', 'form']):
                    unwanted.extract()
                
                # Extract text
                paragraphs = []
                for p in content_container.find_all(['p', 'h2', 'h3', 'h4', 'blockquote']):
                    text = p.text.strip()
                    if text and len(text) > 10:  # Filter out very short paragraphs
                        paragraphs.append(text)
                
                article.content = '\n\n'.join(paragraphs)
            
            # Extract images
            for img in soup.find_all('img', src=True):
                src = img['src']
                if src.startswith('//'):
                    src = 'https:' + src
                elif not src.startswith(('http://', 'https://')):
                    # Make relative URLs absolute
                    from urllib.parse import urljoin
                    src = urljoin(url, src)
                
                if src not in article.images:
                    article.images.append(src)
            
            # Save to file
            filepath = article.save_to_file()
            print(f"Saved article to {filepath}")
            
            # Mark as processed
            self.cache.mark_as_processed(url, "content_extraction")
            
            return article
            
        except Exception as e:
            print(f"Error extracting article content: {e}")
            # Don't mark as processed when there's an error
            return article
    
    def process_article_list(self, urls):
        """
        Process a list of article URLs through the pipeline.
        
        Args:
            urls: List of URLs to process
            
        Returns:
            list: List of processed articles
        """
        articles = []
        
        for i, url in enumerate(urls):
            print(f"\n[{i+1}/{len(urls)}] Processing {url}")
            article = self.extract_article_content(url)
            
            if article.title:
                print(f"Title: {article.title}")
                print(f"Author: {article.author}")
                print(f"Date: {article.date}")
                print(f"Content length: {len(article.content) if article.content else 0} characters")
                print(f"Images: {len(article.images)}")
                
                articles.append(article)
            else:
                print(f"Failed to extract article")
            
            # Sleep between articles
            if i < len(urls) - 1:
                time.sleep(3)
        
        return articles

def main():
    """Main function for the news scraper example."""
    parser = argparse.ArgumentParser(description="Web Scraping Toolkit - News Scraper Example")
    parser.add_argument('urls', nargs='*', help='URLs of news articles to scrape')
    parser.add_argument('--file', '-f', help='File containing URLs of articles to scrape (one per line)')
    args = parser.parse_args()
    
    # Collect URLs from arguments and/or file
    urls = args.urls or []
    
    if args.file:
        try:
            with open(args.file, 'r') as f:
                file_urls = [line.strip() for line in f if line.strip()]
                urls.extend(file_urls)
        except Exception as e:
            print(f"Error reading URLs file: {e}")
    
    # Check if we have any URLs to process
    if not urls:
        print("No URLs provided. Please specify URLs or provide a file with URLs.")
        example_urls = [
            "https://www.bbc.com/news/world-us-canada-65402017",
            "https://www.theguardian.com/world/2023/apr/27/china-population-shrink-india"
        ]
        print("\nExample usage:")
        print(f"python {os.path.basename(__file__)} {' '.join(example_urls)}")
        print(f"python {os.path.basename(__file__)} --file urls.txt")
        return
    
    # Initialize the pipeline
    pipeline = NewsScraperPipeline()
    
    # Process all articles
    print(f"\nProcessing {len(urls)} articles...")
    articles = pipeline.process_article_list(urls)
    
    # Print summary
    print("\nSummary:")
    print(f"Successfully processed {len(articles)} out of {len(urls)} articles")
    print(f"Articles saved to {os.path.abspath(OUTPUT_DIR)}")

if __name__ == "__main__":
    main() 