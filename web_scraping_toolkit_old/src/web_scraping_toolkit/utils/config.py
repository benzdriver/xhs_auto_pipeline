"""
Configuration utilities for the Web Scraping Toolkit.

This module provides functionality to load and manage configuration settings
from environment variables or .env files.
"""

import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables or .env file.
    
    Returns:
        Dict[str, Any]: A dictionary containing all configuration settings.
    """
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Construct the configuration dictionary
    config = {
        # Proxy configuration
        "proxy": {
            "enabled": os.getenv("USE_PROXY", "").lower() == "true",
            "rotation_interval": int(os.getenv("PROXY_ROTATION_INTERVAL", "300")),  # in seconds
            "max_requests_per_ip": int(os.getenv("MAX_REQUESTS_PER_IP", "10")),
            "ip_cooldown_minutes": int(os.getenv("IP_COOLDOWN_MINUTES", "60")),
            "smartproxy": {
                "username": os.getenv("SMARTPROXY_USERNAME", ""),
                "password": os.getenv("SMARTPROXY_PASSWORD", ""),
                "endpoint": os.getenv("SMARTPROXY_ENDPOINT", "gate.smartproxy.com"),
                "port": os.getenv("SMARTPROXY_PORT", "7000"),
                "additional_ports": _parse_list_env("SMARTPROXY_ADDITIONAL_PORTS")
            },
            "custom_proxies": _parse_custom_proxies()
        },
        
        # Captcha solver configuration
        "captcha": {
            "service": os.getenv("CAPTCHA_SERVICE", "2captcha"),
            "api_key": os.getenv("TWOCAPTCHA_API_KEY", "")
        },
        
        # Cache configuration
        "cache": {
            "enabled": os.getenv("USE_CACHE", "").lower() == "true",
            "directory": os.getenv("CACHE_DIRECTORY", "cache"),
            "expiration": int(os.getenv("CACHE_EXPIRATION_SECONDS", "86400"))  # Default: 24 hours
        }
    }
    
    return config

def _parse_list_env(env_name: str) -> List[str]:
    """
    Parse a comma-separated environment variable into a list.
    
    Args:
        env_name: Name of the environment variable.
        
    Returns:
        List[str]: The parsed list or an empty list if the variable is not set.
    """
    env_value = os.getenv(env_name, "")
    if not env_value:
        return []
    
    return [item.strip() for item in env_value.split(",") if item.strip()]

def _parse_custom_proxies() -> List[Dict[str, str]]:
    """
    Parse custom proxies from the CUSTOM_PROXIES environment variable.
    The variable should contain a JSON-encoded list of proxy objects.
    
    Returns:
        List[Dict[str, str]]: A list of proxy configurations.
    """
    custom_proxies_json = os.getenv("CUSTOM_PROXIES", "")
    if not custom_proxies_json:
        return []
    
    try:
        return json.loads(custom_proxies_json)
    except json.JSONDecodeError:
        print("Warning: Invalid format for CUSTOM_PROXIES. Should be a valid JSON array.")
        return []

def get_proxy_config() -> Dict[str, Any]:
    """
    Get proxy-specific configuration.
    
    Returns:
        Dict[str, Any]: Proxy configuration dictionary.
    """
    return load_config()["proxy"]

def get_captcha_config() -> Dict[str, Any]:
    """
    Get captcha-specific configuration.
    
    Returns:
        Dict[str, Any]: Captcha configuration dictionary.
    """
    return load_config()["captcha"]

def get_cache_config() -> Dict[str, Any]:
    """
    Get cache-specific configuration.
    
    Returns:
        Dict[str, Any]: Cache configuration dictionary.
    """
    return load_config()["cache"] 