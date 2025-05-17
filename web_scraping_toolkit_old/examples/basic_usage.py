#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Basic usage example for the Web Scraping Toolkit package.

This example demonstrates how to:
1. Set up proxy rotation
2. Configure CAPTCHA solving
3. Use caching
4. Scrape a website with automatic IP rotation and CAPTCHA solving
"""

import os
import time
from dotenv import load_dotenv

# Import the toolkit components
from web_scraping_toolkit import ProxyManager, CaptchaSolver, CacheMechanism, WebScraper

# Load environment variables
load_dotenv()

def main():
    """Main example function."""
    print("Web Scraping Toolkit - Basic Example")
    print("====================================")
    
    # Set up proxy manager
    proxy_manager = ProxyManager()
    print(f"Proxy manager initialized with {proxy_manager.proxy_count} proxies")
    
    # Set up CAPTCHA solver
    captcha_solver = CaptchaSolver()
    print(f"CAPTCHA solver available: {captcha_solver.is_available()}")
    
    # Set up cache mechanism
    cache = CacheMechanism("example_cache")
    print(f"Cache mechanism initialized")
    
    # Create web scraper with all components
    scraper = WebScraper(
        proxy_manager=proxy_manager,
        captcha_solver=captcha_solver,
        cache_mechanism=cache
    )
    
    # Example URLs to scrape
    urls = [
        "https://httpbin.org/ip",  # Shows your IP
        "https://httpbin.org/user-agent",  # Shows your user agent
        "https://httpbin.org/headers",  # Shows your headers
    ]
    
    # Scrape each URL
    for url in urls:
        print(f"\nScraping {url}")
        try:
            # Fetch the URL
            response = scraper.get(url)
            
            # Print response details
            print(f"Status: {response.status_code}")
            print(f"Content type: {response.headers.get('content-type', 'unknown')}")
            print(f"Response size: {len(response.text)} bytes")
            
            # Print content sample
            content_sample = response.text[:200] + "..." if len(response.text) > 200 else response.text
            print(f"Content sample:\n{content_sample}")
            
            # Extract text if it's HTML
            if "text/html" in response.headers.get('content-type', ''):
                extracted_text = scraper.extract_text(response)
                print(f"Extracted text sample: {extracted_text[:100]}...")
                
            # Extract links if it's HTML
            if "text/html" in response.headers.get('content-type', ''):
                links = scraper.extract_links(response)
                print(f"Found {len(links)} links")
                for i, link in enumerate(links[:5]):
                    print(f"  Link {i+1}: {link}")
                if len(links) > 5:
                    print(f"  ...and {len(links) - 5} more")
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            
        # Sleep between requests to be respectful
        time.sleep(2)
    
    # Example of using cache
    print("\nTesting cache mechanism:")
    cache_key = "test_key"
    cache_data = {"message": "This is cached data", "timestamp": time.time()}
    
    # Cache some data
    cache.cache_data(cache_key, cache_data)
    print(f"Data cached with key: {cache_key}")
    
    # Retrieve the data
    retrieved_data = cache.get_cached_data(cache_key)
    print(f"Retrieved data: {retrieved_data}")
    
    # Mark as processed
    cache.mark_as_processed(cache_key, "example_stage")
    print(f"Marked as processed by 'example_stage'")
    
    # Check processing status
    is_processed = cache.is_processed_by_stage(cache_key, "example_stage")
    print(f"Is processed by 'example_stage': {is_processed}")
    
    print("\nExample completed successfully!")

if __name__ == "__main__":
    main() 