"""
Proxy Manager for the Web Scraping Toolkit.

This module provides functionality to manage and rotate proxies,
support multiple proxy providers, and handle proxy failures.
"""

import random
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import requests

from ..utils.logger import get_logger
from ..utils.config import get_proxy_config

# Initialize logger
logger = get_logger("proxy_manager")

class ProxyManager:
    """
    Manages a pool of proxies with automatic rotation, testing, and blacklisting.
    
    This class handles:
    - Loading proxies from configuration
    - Automatic proxy rotation based on time or request count
    - Testing proxy connectivity
    - Blacklisting problematic proxies
    - Formatting proxies for different clients (requests, playwright, etc.)
    """
    
    def __init__(
        self,
        rotation_interval: Optional[int] = None,
        max_requests_per_ip: Optional[int] = None,
        enabled: Optional[bool] = None
    ):
        """
        Initialize the proxy manager with optional custom settings.
        
        Args:
            rotation_interval: Seconds between proxy rotations (overrides config)
            max_requests_per_ip: Maximum requests per IP before rotation (overrides config)
            enabled: Whether proxy usage is enabled (overrides config)
        """
        # Load proxy configuration
        self.config = get_proxy_config()
        
        # Override configuration with constructor parameters if provided
        self.proxy_enabled = enabled if enabled is not None else self.config.get("enabled", False)
        self.rotation_interval = rotation_interval or self.config.get("rotation_interval", 300)
        self.max_requests_per_ip = max_requests_per_ip or self.config.get("max_requests_per_ip", 10)
        
        # Proxy management state
        self.proxy_list: List[Dict[str, str]] = []
        self.blacklisted_proxies: Dict[Dict[str, str], datetime] = {}
        self.current_proxy: Optional[Dict[str, str]] = None
        self.last_rotation_time = datetime.now()
        self.request_count = 0
        
        # Thread lock for thread safety
        self._lock = threading.RLock()
        
        # Initialize proxy list
        self._init_proxy_list()
        
        if self.proxy_enabled:
            logger.info(f"Proxy manager initialized with {len(self.proxy_list)} available proxies")
            logger.info(f"Rotation interval: {self.rotation_interval} seconds")
            logger.info(f"Max requests per IP: {self.max_requests_per_ip}")
        else:
            logger.info("Proxy functionality is disabled")
    
    def _init_proxy_list(self) -> None:
        """Initialize the proxy list from configuration."""
        if not self.proxy_enabled:
            return
        
        # Add SmartProxy if configured
        if 'smartproxy' in self.config:
            self._init_smartproxy()
        
        # Add custom proxies if configured
        if 'custom_proxies' in self.config and isinstance(self.config['custom_proxies'], list):
            self.proxy_list.extend(self.config['custom_proxies'])
            logger.info(f"Added {len(self.config['custom_proxies'])} custom proxies")
    
    def _init_smartproxy(self) -> None:
        """Initialize SmartProxy configuration."""
        smartproxy_config = self.config.get('smartproxy', {})
        username = smartproxy_config.get('username')
        password = smartproxy_config.get('password')
        endpoint = smartproxy_config.get('endpoint', 'gate.smartproxy.com')
        port = smartproxy_config.get('port', '10001')
        protocol = smartproxy_config.get('protocol', 'http')
        
        if not (username and password and endpoint):
            logger.warning("SmartProxy configuration is incomplete, cannot initialize")
            return
        
        # Create SmartProxy configuration
        proxy = {
            'server': f'{endpoint}:{port}',
            'username': username,
            'password': password,
            'protocol': protocol
        }
        
        # Add to proxy list
        self.proxy_list.append(proxy)
        logger.info(f"Added SmartProxy: {endpoint}:{port}")
        
        # Add additional ports if configured
        additional_ports = smartproxy_config.get('additional_ports', [])
        if additional_ports and isinstance(additional_ports, list):
            for additional_port in additional_ports:
                if additional_port and additional_port.strip():
                    additional_proxy = {
                        'server': f'{endpoint}:{additional_port}',
                        'username': username,
                        'password': password,
                        'protocol': protocol
                    }
                    self.proxy_list.append(additional_proxy)
                    logger.info(f"Added additional SmartProxy: {endpoint}:{additional_port}")
    
    def get_proxy(self, force_rotate: bool = False) -> Optional[Dict[str, str]]:
        """
        Get the current proxy configuration, rotating if necessary.
        
        Args:
            force_rotate: Whether to force a proxy rotation
            
        Returns:
            Optional[Dict[str, str]]: Proxy configuration or None if proxies are disabled
        """
        if not self.proxy_enabled or not self.proxy_list:
            return None
        
        with self._lock:
            # Check if we need to rotate proxy
            now = datetime.now()
            time_since_rotation = (now - self.last_rotation_time).total_seconds()
            
            if (force_rotate or 
                self.current_proxy is None or 
                time_since_rotation > self.rotation_interval or 
                self.request_count >= self.max_requests_per_ip):
                self._rotate_proxy()
                self.request_count = 0
            else:
                self.request_count += 1
            
            return self.current_proxy
    
    def _rotate_proxy(self) -> None:
        """Rotate to a new proxy from the available pool."""
        with self._lock:
            # Remove expired blacklisted proxies
            self._remove_expired_blacklisted()
            
            # Get available proxies (not blacklisted)
            # 修复: 使用字典序列化为字符串作为键的方式进行比较
            available_proxies = []
            blacklisted_servers = [p['server'] for p in self.blacklisted_proxies.keys()]
            
            for p in self.proxy_list:
                if p['server'] not in blacklisted_servers:
                    available_proxies.append(p)
            
            if not available_proxies:
                logger.warning("No available proxies to rotate to, using blacklisted proxies")
                available_proxies = self.proxy_list
                # Clear blacklist if we're forced to use them
                self.blacklisted_proxies = {}
            
            if not available_proxies:
                logger.error("No proxies available at all")
                self.current_proxy = None
                return
            
            # Randomly select a proxy that's different from the current one
            if len(available_proxies) > 1 and self.current_proxy in available_proxies:
                new_proxies = [p for p in available_proxies if p['server'] != (self.current_proxy['server'] if self.current_proxy else None)]
                if new_proxies:
                    self.current_proxy = random.choice(new_proxies)
                else:
                    self.current_proxy = random.choice(available_proxies)
            else:
                self.current_proxy = random.choice(available_proxies)
            
            self.last_rotation_time = datetime.now()
            
            # Log rotation (with password masked)
            safe_proxy = self._get_masked_proxy(self.current_proxy)
            logger.info(f"Rotated to new proxy: {safe_proxy}")
    
    def _get_masked_proxy(self, proxy: Dict[str, str]) -> Dict[str, str]:
        """
        Create a copy of the proxy with password masked for logging.
        
        Args:
            proxy: The proxy configuration
            
        Returns:
            Dict[str, str]: Copy of proxy with masked password
        """
        if not proxy:
            return {}
        
        safe_proxy = proxy.copy()
        if 'password' in safe_proxy:
            safe_proxy['password'] = '****'
        return safe_proxy
    
    def _remove_expired_blacklisted(self) -> None:
        """Remove expired proxies from the blacklist."""
        now = datetime.now()
        # 修复: 使用列表来保存即将删除的键，而不是直接在遍历时修改字典
        expired_proxies = []
        for proxy, expiry in self.blacklisted_proxies.items():
            if now > expiry:
                expired_proxies.append(proxy)
        
        for proxy in expired_proxies:
            del self.blacklisted_proxies[proxy]
            logger.info(f"Removed expired proxy from blacklist: {self._get_masked_proxy(proxy)}")
    
    def blacklist_current_proxy(self, duration_minutes: int = 30) -> bool:
        """
        Add the current proxy to the blacklist for a specified duration.
        
        Args:
            duration_minutes: Minutes to blacklist the proxy
            
        Returns:
            bool: True if blacklisting was successful
        """
        with self._lock:
            if not self.current_proxy or not self.proxy_list:
                return False
            
            # If only one proxy available, don't blacklist
            if len(self.proxy_list) <= 1:
                logger.warning("Only one proxy available, cannot blacklist")
                return False
            
            # Add to blacklist with expiry time
            expiry_time = datetime.now() + timedelta(minutes=duration_minutes)
            # 使用字符串作为键
            self.blacklisted_proxies[self.current_proxy] = expiry_time
            
            # Log blacklisting
            safe_proxy = self._get_masked_proxy(self.current_proxy)
            logger.info(f"Blacklisted proxy for {duration_minutes} minutes: {safe_proxy}")
            
            # Force rotation to a new proxy
            self._rotate_proxy()
            
            return True
    
    def test_proxy(self, proxy: Optional[Dict[str, str]] = None) -> bool:
        """
        Test the connectivity of a proxy.
        
        Args:
            proxy: The proxy to test (uses current proxy if None)
            
        Returns:
            bool: True if the proxy is working
        """
        proxy_to_test = proxy or self.current_proxy
        
        if not proxy_to_test:
            logger.warning("No proxy available to test")
            return False
        
        try:
            # Format proxy for requests
            protocol = proxy_to_test.get('protocol', 'http')
            proxy_url = f"{protocol}://{proxy_to_test['username']}:{proxy_to_test['password']}@{proxy_to_test['server']}"
            
            # Log the test (with password masked)
            safe_proxy = proxy_url.replace(proxy_to_test['password'], '****')
            logger.info(f"Testing proxy connection: {safe_proxy}")
            
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            # Test with a reliable endpoint
            response = requests.get('https://api.ipify.org?format=json', proxies=proxies, timeout=10)
            if response.status_code == 200:
                ip_data = response.json()
                logger.info(f"Proxy test successful, IP: {ip_data.get('ip')}")
                return True
            else:
                logger.warning(f"Proxy test failed, status code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Proxy test error: {e}")
            return False
    
    def get_playwright_proxy(self) -> Optional[Dict[str, str]]:
        """
        Get a proxy configuration formatted for Playwright.
        
        Returns:
            Optional[Dict[str, str]]: Playwright proxy configuration or None if disabled
        """
        proxy = self.get_proxy()
        if not proxy:
            return None
        
        # Format for Playwright
        protocol = proxy.get('protocol', 'http')
        playwright_proxy = {
            'server': f"{protocol}://{proxy['server']}",
            'username': proxy['username'],
            'password': proxy['password']
        }
        
        return playwright_proxy
    
    def get_requests_proxies(self) -> Optional[Dict[str, str]]:
        """
        Get a proxy configuration formatted for the requests library.
        
        Returns:
            Optional[Dict[str, str]]: Requests proxy dictionary or None if disabled
        """
        proxy = self.get_proxy()
        if not proxy:
            return None
        
        # Format for requests
        protocol = proxy.get('protocol', 'http')
        proxy_url = f"{protocol}://{proxy['username']}:{proxy['password']}@{proxy['server']}"
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def add_custom_proxy(
        self,
        server: str,
        username: str,
        password: str,
        protocol: str = "http"
    ) -> None:
        """
        Add a custom proxy to the proxy pool.
        
        Args:
            server: Proxy server (host:port)
            username: Proxy username
            password: Proxy password
            protocol: Proxy protocol (http, https, socks5)
        """
        with self._lock:
            new_proxy = {
                'server': server,
                'username': username,
                'password': password,
                'protocol': protocol
            }
            
            self.proxy_list.append(new_proxy)
            logger.info(f"Added new custom proxy: {server}")
    
    @property
    def proxy_count(self) -> int:
        """
        Get the count of available proxies.
        
        Returns:
            int: Number of available proxies
        """
        return len(self.proxy_list)
    
    @property
    def available_proxy_count(self) -> int:
        """
        Get the count of non-blacklisted proxies.
        
        Returns:
            int: Number of available, non-blacklisted proxies
        """
        # 修复: 使用server属性进行比较
        blacklisted_servers = [p['server'] for p in self.blacklisted_proxies.keys()]
        count = 0
        for p in self.proxy_list:
            if p['server'] not in blacklisted_servers:
                count += 1
        return count 