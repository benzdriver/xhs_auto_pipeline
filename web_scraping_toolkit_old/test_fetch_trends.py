#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for fetch_trends.py using web_scraping_toolkit

This script tests the key functionalities of fetch_trends.py by:
1. Using the web_scraping_toolkit to handle proxy rotation, caching, and CAPTCHA solving
2. Testing Google Trends data fetching
3. Testing news article scraping
"""

import os
import sys
import json
import time
from dotenv import load_dotenv
from datetime import datetime

# Add the parent directory to Python path to import the fetch_trends.py module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import from our new toolkit
from src.web_scraping_toolkit import ProxyManager, CaptchaSolver, CacheMechanism, WebScraper

# Create a separate test directory
TEST_DIR = os.path.join(current_dir, "test_results")
os.makedirs(TEST_DIR, exist_ok=True)

# Load environment variables
load_dotenv()

def setup_toolkit_components():
    """Set up the web scraping toolkit components"""
    print("\n=== Setting up Web Scraping Toolkit ===")
    
    # Initialize proxy manager
    proxy_manager = ProxyManager()
    print(f"Proxy manager initialized with {proxy_manager.proxy_count} proxies")
    
    # Initialize CAPTCHA solver
    captcha_solver = CaptchaSolver()
    print(f"CAPTCHA solver available: {captcha_solver.is_available()}")
    
    # Initialize caching
    cache = CacheMechanism("fetch_trends_test")
    print(f"Cache mechanism initialized")
    
    # Create web scraper
    scraper = WebScraper(
        proxy_manager=proxy_manager,
        captcha_solver=captcha_solver,
        cache_mechanism=cache,
        browser_headless=True
    )
    
    return proxy_manager, captcha_solver, cache, scraper

def test_google_trends_fetch():
    """Test fetching trend scores from Google Trends"""
    from stages.fetch_trends import get_trend_score_via_browser, get_trend_score_via_serpapi
    
    print("\n=== Testing Google Trends Fetch ===")
    
    # Keywords to test
    test_keywords = [
        "Canadian immigration",
        "Express Entry Canada",
        "Canada PNP",
        "Study permit Canada"
    ]
    
    results = {}
    
    # First check if SerpAPI is available
    serpapi_key = os.environ.get("SERPAPI_KEY")
    if serpapi_key:
        print("SerpAPI key found, testing SerpAPI method...")
        for keyword in test_keywords[:2]:  # Just test two keywords with SerpAPI
            print(f"Fetching trend score for: {keyword} (with SerpAPI)")
            try:
                score = get_trend_score_via_serpapi(keyword)
                print(f"Trend score: {score}")
                results[keyword] = score
                time.sleep(2)
            except Exception as e:
                print(f"Error getting trend score for '{keyword}' with SerpAPI: {e}")
    else:
        print("No SerpAPI key found, skipping SerpAPI testing")
    
    # Then try with proxies
    print("\nAttempting with proxies...")
    for keyword in test_keywords:
        if keyword in results and results[keyword] is not None:
            continue  # Skip if already successful with SerpAPI
            
        print(f"Fetching trend score for: {keyword} (with proxy)")
        try:
            score = get_trend_score_via_browser(keyword)
            print(f"Trend score: {score}")
            results[keyword] = score
            time.sleep(2)
        except Exception as e:
            print(f"Error getting trend score for '{keyword}' with proxy: {e}")
            results[keyword] = None
    
    # Finally try without proxies
    print("\nNow testing without proxies...")
    for keyword in test_keywords:
        if keyword in results and results[keyword] is not None:
            continue  # Skip if already successful
            
        print(f"Fetching trend score for: {keyword} (without proxy)")
        try:
            score = get_trend_score_via_browser(keyword, bypass_proxy=True)
            print(f"Trend score: {score}")
            results[keyword] = score
            time.sleep(2)
        except Exception as e:
            print(f"Error getting trend score for '{keyword}' without proxy: {e}")
            results[keyword] = None
    
    # Save results
    output_file = os.path.join(TEST_DIR, "trends_test_results.json")
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)
    
    print(f"Saved trend results to {output_file}")
    return results

def test_article_extraction():
    """Test article content extraction"""
    from stages.fetch_trends import fetch_article_content
    
    print("\n=== Testing Article Content Extraction ===")
    
    # Test URLs for news articles
    test_urls = [
        "https://www.cicnews.com/2023/05/canada-welcomes-over-26000-new-immigrants-in-march-0526544.html",
        "https://www.canada.ca/en/immigration-refugees-citizenship/news/2023/04/canada-launches-new-international-health-care-worker-immigration-pathway.html",
        "https://www.ctvnews.ca/canada/canada-unveils-new-pathways-for-foreign-healthcare-workers-to-get-permanent-residency-1.6364977"
    ]
    
    results = {}
    
    for url in test_urls:
        print(f"Fetching article content from: {url}")
        try:
            # Use the original function to extract article
            content = fetch_article_content(url)
            if content:
                print(f"Extracted {len(content)} characters")
                
                # Store a preview of the content
                preview = content[:200] + "..." if len(content) > 200 else content
                results[url] = {
                    "success": True,
                    "length": len(content),
                    "preview": preview
                }
            else:
                print("Failed to extract content")
                results[url] = {
                    "success": False,
                    "reason": "No content returned"
                }
                
            # Add a small delay between requests
            time.sleep(2)
        except Exception as e:
            print(f"Error extracting content from '{url}': {e}")
            results[url] = {
                "success": False,
                "reason": str(e)
            }
    
    # Save results
    output_file = os.path.join(TEST_DIR, "article_extraction_test_results.json")
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)
    
    print(f"Saved article extraction results to {output_file}")
    return results

def test_trending_keywords():
    """Test trending keywords generation"""
    from stages.fetch_trends import fetch_weighted_trending_keywords
    
    print("\n=== Testing Trending Keywords Generation ===")
    
    try:
        # Use the original function with reduced count for testing
        keywords = fetch_weighted_trending_keywords(max_keywords=5)
        
        print(f"Generated {len(keywords)} weighted keywords:")
        for kw in keywords:
            print(f"- {kw['keyword']} (Score: {kw['score']:.2f}, Type: {kw['type']})")
        
        # Save results
        output_file = os.path.join(TEST_DIR, "trending_keywords_test_results.json")
        with open(output_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "keywords": keywords
            }, f, indent=2)
        
        print(f"Saved trending keywords to {output_file}")
        return keywords
    except Exception as e:
        print(f"Error generating trending keywords: {e}")
        return None

def test_news_fetch():
    """Test fetching news items for a keyword"""
    from stages.fetch_trends import fetch_news_items
    
    print("\n=== Testing News Fetch ===")
    
    # Create a keyword data entry (similar to what fetch_weighted_trending_keywords produces)
    keyword_data = {
        "keyword": "Canada Express Entry",
        "score": 80,
        "type": "news_article",
        "category": "移民路径"
    }
    
    try:
        # Use the original function
        news_items = fetch_news_items(keyword_data, max_items=3)
        
        print(f"Fetched {len(news_items)} news items:")
        for item in news_items:
            print(f"- {item['title']} | Source: {item['source']}")
            print(f"  URL: {item['url']}")
            print(f"  Content length: {len(item['full_content']) if item['full_content'] else 0} characters")
            print()
        
        # Save results
        output_file = os.path.join(TEST_DIR, "news_fetch_test_results.json")
        with open(output_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "keyword_data": keyword_data,
                "news_items": news_items
            }, f, indent=2)
        
        print(f"Saved news fetch results to {output_file}")
        return news_items
    except Exception as e:
        print(f"Error fetching news: {e}")
        return None

def test_full_pipeline():
    """Test the full fetch_trends pipeline"""
    from stages.fetch_trends import run
    
    print("\n=== Testing Full Pipeline ===")
    
    try:
        # Run the full pipeline 
        print("Starting the full fetch_trends pipeline...")
        news_data = run()
        
        print(f"Pipeline completed with {len(news_data)} valid news items")
        
        # Save a copy of the output
        output_file = os.path.join(TEST_DIR, "pipeline_test_results.json")
        with open(output_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "news_count": len(news_data),
                "news_data": news_data
            }, f, indent=2)
        
        print(f"Saved pipeline test results to {output_file}")
        return news_data
    except Exception as e:
        print(f"Error running full pipeline: {e}")
        return None

def main():
    print("=== Testing fetch_trends.py using web_scraping_toolkit ===")
    start_time = time.time()
    
    # Set up toolkit components first
    proxy_manager, captcha_solver, cache, scraper = setup_toolkit_components()
    
    try:
        # Choose which tests to run
        test_options = {
            '1': ('Google Trends Fetch', test_google_trends_fetch),
            '2': ('Article Extraction', test_article_extraction),
            '3': ('Trending Keywords Generation', test_trending_keywords),
            '4': ('News Fetch', test_news_fetch),
            '5': ('Full Pipeline', test_full_pipeline),
            'all': ('Run All Tests', None)
        }
        
        # Present menu
        print("\nAvailable tests:")
        for key, (name, _) in test_options.items():
            print(f"{key}. {name}")
        
        choice = input("\nSelect a test to run (1-5 or 'all'): ").strip().lower()
        
        if choice == 'all':
            print("\nRunning all tests...")
            test_google_trends_fetch()
            test_article_extraction()
            test_trending_keywords()
            test_news_fetch()
            test_full_pipeline()
        elif choice in test_options:
            name, test_func = test_options[choice]
            print(f"\nRunning test: {name}")
            test_func()
        else:
            print(f"Invalid choice: {choice}")
        
    except Exception as e:
        print(f"Test execution failed: {e}")
    
    elapsed_time = time.time() - start_time
    print(f"\nAll tests completed in {elapsed_time:.2f} seconds")
    print(f"Results saved in: {TEST_DIR}")

if __name__ == "__main__":
    main() 