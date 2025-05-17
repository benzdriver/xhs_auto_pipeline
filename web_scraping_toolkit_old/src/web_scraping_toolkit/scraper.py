"""
Web Scraper for the Web Scraping Toolkit.

This module provides the main scraper functionality, integrating proxy rotation,
CAPTCHA solving, and caching.
"""

import os
import time
import random
import json
import threading
from typing import Dict, List, Any, Optional, Union, Tuple
import hashlib
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import tempfile

from .proxy.proxy_manager import ProxyManager
from .captcha.captcha_solver import CaptchaSolver
from .cache.cache_mechanism import CacheMechanism
from .utils.logger import get_logger

# Initialize logger
logger = get_logger("web_scraper")

class WebScraper:
    """
    Main web scraping class that integrates all toolkit components.
    
    This class provides:
    - High-level methods for fetching web content
    - Integration of proxy rotation, CAPTCHA solving, and caching
    - Browser-based scraping for JavaScript-heavy sites
    - Multiple fallback strategies for resilient scraping
    """
    
    def __init__(
        self,
        proxy_manager: Optional[ProxyManager] = None,
        captcha_solver: Optional[CaptchaSolver] = None,
        cache_mechanism: Optional[CacheMechanism] = None,
        user_agent: Optional[str] = None,
        browser_headless: bool = True
    ):
        """
        Initialize the web scraper with optional components.
        
        Args:
            proxy_manager: Optional proxy manager for IP rotation
            captcha_solver: Optional CAPTCHA solver
            cache_mechanism: Optional cache mechanism
            user_agent: Custom user agent string
            browser_headless: Whether to run browser in headless mode
        """
        # Store components
        self.proxy_manager = proxy_manager
        self.captcha_solver = captcha_solver
        self.cache_mechanism = cache_mechanism
        self.browser_headless = browser_headless
        
        # Set up default user agent if not provided
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
        
        # Randomize user agent slightly to avoid fingerprinting
        self._randomize_user_agent()
        
        # Initialize requests session
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        
        # Track requests to avoid overloading servers
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds
        
        # Thread lock for thread safety
        self._lock = threading.RLock()
        
        logger.info("Web scraper initialized")
        if self.proxy_manager:
            logger.info("Using proxy rotation")
        if self.captcha_solver:
            logger.info("CAPTCHA solving enabled")
        if self.cache_mechanism:
            logger.info("Caching enabled")
    
    def _randomize_user_agent(self) -> None:
        """Slightly randomize the user agent to avoid detection patterns."""
        # Extract base components
        if "Chrome/" in self.user_agent:
            # For Chrome-like user agents
            chrome_version = self.user_agent.split("Chrome/")[1].split(" ")[0]
            major, minor, build, patch = chrome_version.split(".")
            
            # Randomize minor version slightly
            new_minor = str(int(minor) + random.randint(-2, 2))
            new_build = str(int(build) + random.randint(-10, 10))
            new_patch = str(int(patch) + random.randint(-50, 50))
            
            # Ensure values are valid
            new_minor = max(0, int(new_minor))
            new_build = max(0, int(new_build))
            new_patch = max(0, int(new_patch))
            
            # Create new version string
            new_version = f"{major}.{new_minor}.{new_build}.{new_patch}"
            
            # Replace in user agent
            self.user_agent = self.user_agent.replace(
                f"Chrome/{chrome_version}", 
                f"Chrome/{new_version}"
            )
    
    def get(
        self, 
        url: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        use_cache: Optional[bool] = None,
        force_browser: bool = False,
        retry_count: int = 3,
        timeout: int = 30
    ) -> requests.Response:
        """
        Fetch a URL using HTTP GET, with proxy rotation and caching.
        
        Args:
            url: The URL to fetch
            params: Optional query parameters
            headers: Optional HTTP headers
            use_cache: Whether to use cache (overrides cache_mechanism setting)
            force_browser: Whether to force browser-based fetching
            retry_count: Number of retries on failure
            timeout: Request timeout in seconds
            
        Returns:
            requests.Response: The HTTP response
            
        Raises:
            requests.RequestException: If the request fails after all retries
        """
        # Check if the URL is already in cache
        should_use_cache = use_cache if use_cache is not None else bool(self.cache_mechanism)
        if should_use_cache and self.cache_mechanism and self.cache_mechanism.is_cached(url):
            cached_data = self.cache_mechanism.get_cached_data(url)
            if cached_data and isinstance(cached_data, dict) and 'content' in cached_data:
                logger.info(f"Using cached response for {url}")
                
                # Create a Response-like object from cached data
                response = requests.Response()
                response.url = url
                response._content = cached_data['content'].encode('utf-8')
                response.status_code = cached_data.get('status_code', 200)
                response.headers = cached_data.get('headers', {})
                response.encoding = 'utf-8'
                
                return response
        
        # Throttle requests to avoid overloading servers
        self._respect_rate_limits()
        
        # Try browser-based fetching if forced
        if force_browser:
            return self._get_with_browser(url, headers, retry_count)
        
        # Try regular HTTP fetching with retries
        for attempt in range(retry_count):
            try:
                response = self._get_with_requests(url, params, headers, timeout)
                
                # Check if we need to handle CAPTCHA
                if self._is_captcha_page(response) and self.captcha_solver:
                    logger.info(f"CAPTCHA detected, switching to browser mode for {url}")
                    return self._get_with_browser(url, headers, retry_count - attempt)
                
                # Check for other issues that might require browser
                if self._needs_browser(response):
                    logger.info(f"Content requires JavaScript, switching to browser mode for {url}")
                    return self._get_with_browser(url, headers, retry_count - attempt)
                
                # If successful, cache the response
                if response.status_code == 200 and should_use_cache and self.cache_mechanism:
                    self._cache_response(url, response)
                    
                return response
                
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt+1}/{retry_count}): {e}")
                
                # Blacklist the current proxy if it's a connection issue
                if self.proxy_manager and isinstance(e, (
                    requests.exceptions.ProxyError,
                    requests.exceptions.ConnectTimeout,
                    requests.exceptions.ConnectionError
                )):
                    logger.info("Blacklisting current proxy and retrying")
                    self.proxy_manager.blacklist_current_proxy()
                
                # Last attempt failed, try with browser
                if attempt == retry_count - 1:
                    logger.info(f"All HTTP requests failed, trying browser mode for {url}")
                    return self._get_with_browser(url, headers, 1)
                
                # Sleep before retry
                time.sleep(2 ** attempt)  # Exponential backoff
        
        # This should not happen as _get_with_browser will either return or raise
        raise requests.RequestException(f"Failed to fetch {url} after all retries")
    
    def _get_with_requests(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> requests.Response:
        """
        Perform an HTTP GET request using the requests library.
        
        Args:
            url: The URL to fetch
            params: Optional query parameters
            headers: Optional HTTP headers
            timeout: Request timeout in seconds
            
        Returns:
            requests.Response: The HTTP response
            
        Raises:
            requests.RequestException: If the request fails
        """
        # Prepare headers
        request_headers = {"User-Agent": self.user_agent}
        if headers:
            request_headers.update(headers)
        
        # Get proxies if proxy manager is available
        proxies = None
        if self.proxy_manager:
            proxies = self.proxy_manager.get_requests_proxies()
            if proxies:
                logger.debug(f"Using proxy for request to {url}")
        
        # Make the request
        response = self.session.get(
            url,
            params=params,
            headers=request_headers,
            proxies=proxies,
            timeout=timeout,
            verify=True
        )
        
        # Update last request time
        self.last_request_time = time.time()
        
        # Log the result
        logger.info(f"Fetched {url} (Status: {response.status_code})")
        
        return response
    
    def _get_with_browser(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 1
    ) -> requests.Response:
        """
        Fetch a URL using a browser (Playwright) for JavaScript support.
        
        Args:
            url: The URL to fetch
            headers: Optional HTTP headers
            retry_count: Number of retries on failure
            
        Returns:
            requests.Response: A requests.Response-like object
            
        Raises:
            requests.RequestException: If all fetching attempts fail
        """
        try:
            # Only import Playwright when needed
            from playwright.sync_api import sync_playwright, Error as PlaywrightError
            
            with sync_playwright() as p:
                for attempt in range(retry_count):
                    try:
                        # Launch browser
                        browser_options = {
                            'headless': self.browser_headless
                        }
                        
                        # Add proxy if available
                        if self.proxy_manager:
                            proxy_config = self.proxy_manager.get_playwright_proxy()
                            if proxy_config:
                                browser_options['proxy'] = proxy_config
                                logger.debug(f"Using proxy for browser fetching: {url}")
                        
                        # Launch browser
                        browser = p.chromium.launch(**browser_options)
                        
                        # Randomize viewport to avoid fingerprinting
                        context_options = {
                            'viewport': {
                                'width': random.randint(1280, 1920),
                                'height': random.randint(720, 1080)
                            },
                            'user_agent': self.user_agent
                        }
                        
                        # Create context and page
                        context = browser.new_context(**context_options)
                        
                        # Set extra headers if provided
                        if headers:
                            context.set_extra_http_headers(headers)
                        
                        # Create page
                        page = context.new_page()
                        
                        # Navigate to URL
                        logger.info(f"Fetching {url} with browser")
                        page.goto(url, wait_until="networkidle", timeout=60000)
                        
                        # Check for and solve CAPTCHA if needed
                        if self.captcha_solver and self._is_browser_captcha_page(page):
                            logger.info(f"CAPTCHA detected in browser, attempting to solve")
                            captcha_solved = self.captcha_solver.detect_and_solve_recaptcha(page)
                            
                            if captcha_solved:
                                logger.info("CAPTCHA solved, waiting for page to load")
                                page.wait_for_load_state("networkidle")
                                time.sleep(2)  # Give extra time for page to update
                            else:
                                logger.warning("Failed to solve CAPTCHA")
                                
                                # Try with another proxy if available
                                if self.proxy_manager:
                                    self.proxy_manager.blacklist_current_proxy()
                        
                        # Get page content
                        content = page.content()
                        
                        # Get cookies
                        cookies = context.cookies()
                        
                        # Create a Response-like object
                        response = requests.Response()
                        response.url = page.url
                        response._content = content.encode('utf-8')
                        response.status_code = 200
                        
                        # Add cookies to session
                        for cookie in cookies:
                            domain = cookie.get('domain', '')
                            if domain and domain in url:
                                self.session.cookies.set(
                                    cookie.get('name', ''), 
                                    cookie.get('value', ''),
                                    domain=domain
                                )
                        
                        # Close browser
                        browser.close()
                        
                        # Cache the response if enabled
                        if self.cache_mechanism:
                            self._cache_response(url, response)
                        
                        return response
                        
                    except PlaywrightError as e:
                        logger.warning(f"Browser fetch failed (attempt {attempt+1}/{retry_count}): {e}")
                        
                        # Blacklist proxy if it appears to be the issue
                        if "proxy" in str(e).lower() and self.proxy_manager:
                            self.proxy_manager.blacklist_current_proxy()
                        
                        # Sleep before retry
                        time.sleep(2 ** attempt)  # Exponential backoff
        
        except ImportError:
            logger.error("Playwright is not installed. Install with: pip install playwright")
            logger.error("After installation, run: playwright install")
            raise requests.RequestException("Browser-based fetching requires Playwright")
            
        except Exception as e:
            logger.error(f"Browser fetching error: {e}")
            raise requests.RequestException(f"Browser fetch failed: {e}")
    
    def _is_captcha_page(self, response: requests.Response) -> bool:
        """
        Check if a response page contains a CAPTCHA.
        
        Args:
            response: The HTTP response
            
        Returns:
            bool: True if a CAPTCHA is detected
        """
        # Check status code (many CAPTCHA pages return 403)
        if response.status_code in (403, 429):
            return True
            
        # Check content for CAPTCHA keywords
        content_lower = response.text.lower()
        captcha_keywords = [
            "captcha", "robot", "human verification", "are you human",
            "security check", "verify you are human", "bot check",
            "recaptcha", "hcaptcha", "challenge"
        ]
        
        return any(keyword in content_lower for keyword in captcha_keywords)
    
    def _is_browser_captcha_page(self, page: Any) -> bool:
        """
        Check if a Playwright page contains a CAPTCHA.
        
        Args:
            page: The Playwright page object
            
        Returns:
            bool: True if a CAPTCHA is detected
        """
        try:
            # Check for common CAPTCHA elements and text
            content = page.content().lower()
            captcha_keywords = [
                "captcha", "robot", "human verification", "are you human",
                "security check", "verify you are human", "bot check",
                "recaptcha", "hcaptcha", "challenge"
            ]
            
            # Check for text indicators
            if any(keyword in content for keyword in captcha_keywords):
                return True
                
            # Check for specific CAPTCHA elements
            captcha_elements = [
                ".g-recaptcha",
                ".h-captcha",
                "iframe[src*='captcha']",
                "iframe[src*='recaptcha']",
                "iframe[src*='hcaptcha']"
            ]
            
            for selector in captcha_elements:
                if page.query_selector(selector):
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error checking for CAPTCHA in browser: {e}")
            return False
    
    def _needs_browser(self, response: requests.Response) -> bool:
        """
        Check if a response indicates we need browser rendering.
        
        Args:
            response: The HTTP response
            
        Returns:
            bool: True if browser rendering is needed
        """
        # Check for error status code
        if response.status_code >= 400:
            return True
            
        # Check for very short content
        if len(response.text) < 1000:
            return True
            
        # Check for JavaScript-only pages
        content_lower = response.text.lower()
        js_indicators = [
            "javascript is required", 
            "enable javascript", 
            "please enable javascript",
            "you need to enable javascript"
        ]
        
        # Check for JavaScript indicators
        if any(indicator in content_lower for indicator in js_indicators):
            return True
            
        # Count specific tags that might indicate a JS-only page
        soup = BeautifulSoup(response.text, 'html.parser')
        body_content = soup.find('body')
        
        if body_content:
            # If too many script tags compared to other content
            script_tags = body_content.find_all('script')
            other_tags = body_content.find_all(['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            
            if len(script_tags) > len(other_tags) * 2:
                return True
                
        return False
    
    def _respect_rate_limits(self) -> None:
        """
        Ensure a minimum interval between requests to be respectful.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
    
    def _cache_response(self, url: str, response: requests.Response) -> None:
        """
        Cache a response for future use.
        
        Args:
            url: The URL that was fetched
            response: The HTTP response
        """
        if not self.cache_mechanism:
            return
            
        try:
            # Extract response data to cache
            cached_data = {
                'content': response.text,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'url': response.url
            }
            
            # Store in cache
            self.cache_mechanism.cache_data(url, cached_data)
            logger.debug(f"Cached response for {url}")
            
        except Exception as e:
            logger.error(f"Error caching response: {e}")
    
    def extract_text(self, response: requests.Response) -> str:
        """
        Extract readable text from an HTML response.
        
        Args:
            response: The HTTP response
            
        Returns:
            str: Extracted text content
        """
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script_or_style in soup(['script', 'style', 'meta', 'noscript']):
                script_or_style.extract()
                
            # Get text
            text = soup.get_text()
            
            # Break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            
            # Remove blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from response: {e}")
            return response.text
    
    def extract_links(self, response: requests.Response, base_url: Optional[str] = None) -> List[str]:
        """
        Extract links from an HTML response.
        
        Args:
            response: The HTTP response
            base_url: Optional base URL for resolving relative links
            
        Returns:
            List[str]: List of extracted URLs
        """
        links = []
        
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Use response URL as base if not provided
            base = base_url or response.url
            
            # Extract all links
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href'].strip()
                
                # Skip empty or javascript links
                if not href or href.startswith('javascript:'):
                    continue
                    
                # Resolve relative URLs
                if not href.startswith(('http://', 'https://')):
                    from urllib.parse import urljoin
                    href = urljoin(base, href)
                    
                links.append(href)
                
            return links
            
        except Exception as e:
            logger.error(f"Error extracting links from response: {e}")
            return links
    
    def download_file(
        self, 
        url: str, 
        output_path: str,
        use_cache: bool = True,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """
        Download a file from a URL.
        
        Args:
            url: The URL of the file to download
            output_path: Where to save the downloaded file
            use_cache: Whether to use cache
            progress_callback: Optional callback function for progress updates
            
        Returns:
            bool: True if download was successful
        """
        # Check if file already exists and we're using cache
        if use_cache and os.path.exists(output_path):
            logger.info(f"File already exists at {output_path}, using cache")
            return True
            
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Download to a temporary file first
        temp_file = f"{output_path}.download"
        
        try:
            # Get proxies if proxy manager is available
            proxies = None
            if self.proxy_manager:
                proxies = self.proxy_manager.get_requests_proxies()
            
            # Make request with stream=True to download in chunks
            headers = {"User-Agent": self.user_agent}
            with requests.get(url, stream=True, proxies=proxies, headers=headers) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                
                with open(temp_file, 'wb') as f:
                    downloaded_size = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # Call progress callback if provided
                            if progress_callback and total_size:
                                progress_callback(downloaded_size, total_size)
            
            # Move the temporary file to the final location
            os.replace(temp_file, output_path)
            logger.info(f"Downloaded {url} to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            
            # Remove temporary file if it exists
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
            return False 