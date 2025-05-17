"""
Cache Mechanism for the Web Scraping Toolkit.

This module provides functionality to cache scraping results, track processing
status, and implement file-based persistence.
"""

import os
import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Set, Union
from datetime import datetime, timedelta
import threading

from ..utils.logger import get_logger
from ..utils.config import get_cache_config

# Initialize logger
logger = get_logger("cache_mechanism")

class CacheMechanism:
    """
    Manages a caching system for web scraping data with status tracking.
    
    This class provides:
    - Persistent caching of scraped data
    - Multi-stage processing status tracking
    - Automatic cache invalidation based on time
    - File existence checking to confirm results are ready
    """
    
    def __init__(
        self,
        cache_name: str,
        cache_dir: Optional[str] = None,
        expiration_seconds: Optional[int] = None,
        enabled: Optional[bool] = None
    ):
        """
        Initialize the cache mechanism with optional custom settings.
        
        Args:
            cache_name: Unique name for this cache
            cache_dir: Directory to store cache files (overrides config)
            expiration_seconds: Cache expiration time in seconds (overrides config)
            enabled: Whether caching is enabled (overrides config)
        """
        # Load cache configuration
        self.config = get_cache_config()
        
        # Override configuration with constructor parameters if provided
        self.cache_enabled = enabled if enabled is not None else self.config.get("enabled", True)
        self.cache_name = cache_name
        self.cache_dir = cache_dir or self.config.get("directory", "cache")
        self.expiration_seconds = expiration_seconds or self.config.get("expiration", 86400)
        
        # Ensure cache directory exists
        self.cache_path = os.path.join(self.cache_dir, self.cache_name)
        os.makedirs(self.cache_path, exist_ok=True)
        
        # Cache metadata file paths
        self.items_file = os.path.join(self.cache_path, "items.json")
        self.status_file = os.path.join(self.cache_path, "status.json")
        
        # In-memory cache
        self.items_cache: Dict[str, Any] = {}
        self.status_cache: Dict[str, Dict[str, Any]] = {}
        
        # Thread lock for thread safety
        self._lock = threading.RLock()
        
        # Load cache from disk if it exists
        self._load_cache()
        
        if self.cache_enabled:
            logger.info(f"Cache mechanism '{cache_name}' initialized in {self.cache_path}")
            logger.info(f"Cache expiration: {self.expiration_seconds} seconds")
        else:
            logger.info(f"Cache mechanism '{cache_name}' initialized with caching disabled")
    
    def _load_cache(self) -> None:
        """Load cache data from disk."""
        with self._lock:
            # Load items cache
            if os.path.exists(self.items_file):
                try:
                    with open(self.items_file, 'r', encoding='utf-8') as f:
                        self.items_cache = json.load(f)
                    logger.info(f"Loaded {len(self.items_cache)} cached items from {self.items_file}")
                except Exception as e:
                    logger.error(f"Error loading items cache: {e}")
                    self.items_cache = {}
            
            # Load status cache
            if os.path.exists(self.status_file):
                try:
                    with open(self.status_file, 'r', encoding='utf-8') as f:
                        self.status_cache = json.load(f)
                    logger.info(f"Loaded processing status for {len(self.status_cache)} items")
                except Exception as e:
                    logger.error(f"Error loading status cache: {e}")
                    self.status_cache = {}
            
            # Remove expired items
            self._remove_expired_items()
    
    def _save_cache(self) -> None:
        """Save cache data to disk."""
        if not self.cache_enabled:
            return
            
        with self._lock:
            # Save items cache
            try:
                with open(self.items_file, 'w', encoding='utf-8') as f:
                    json.dump(self.items_cache, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Error saving items cache: {e}")
            
            # Save status cache
            try:
                with open(self.status_file, 'w', encoding='utf-8') as f:
                    json.dump(self.status_cache, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Error saving status cache: {e}")
    
    def _remove_expired_items(self) -> None:
        """Remove expired items from the cache."""
        if not self.cache_enabled:
            return
            
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            # Check items for expiration
            for key, item in self.items_cache.items():
                cached_time = item.get('timestamp', 0)
                if current_time - cached_time > self.expiration_seconds:
                    expired_keys.append(key)
            
            # Remove expired items
            for key in expired_keys:
                if key in self.items_cache:
                    del self.items_cache[key]
                if key in self.status_cache:
                    del self.status_cache[key]
            
            if expired_keys:
                logger.info(f"Removed {len(expired_keys)} expired items from cache")
                # Save changes to disk
                self._save_cache()
    
    def _get_cache_key(self, item_id: str) -> str:
        """
        Generate a cache key for an item.
        
        Args:
            item_id: The item identifier (e.g., URL, query, etc.)
            
        Returns:
            str: Normalized cache key
        """
        # Normalize item_id to ensure consistent caching
        # For URLs, this helps handle slight variations (trailing slashes, etc.)
        if item_id.startswith(('http://', 'https://')):
            # Remove query parameters for simpler caching
            if '?' in item_id:
                item_id = item_id.split('?')[0]
            # Remove trailing slash
            if item_id.endswith('/'):
                item_id = item_id[:-1]
                
        # Generate a hash for the key to ensure valid filenames
        return hashlib.md5(item_id.encode('utf-8')).hexdigest()
    
    def is_cached(self, item_id: str) -> bool:
        """
        Check if an item is in the cache.
        
        Args:
            item_id: The item identifier (e.g., URL, query, etc.)
            
        Returns:
            bool: True if the item is cached
        """
        if not self.cache_enabled:
            return False
            
        with self._lock:
            # Remove expired items first
            self._remove_expired_items()
            
            # Get normalized cache key
            cache_key = self._get_cache_key(item_id)
            
            # Check if it's in the cache
            return cache_key in self.items_cache
    
    def get_cached_data(self, item_id: str) -> Optional[Any]:
        """
        Get data for an item from the cache.
        
        Args:
            item_id: The item identifier (e.g., URL, query, etc.)
            
        Returns:
            Optional[Any]: The cached data or None if not cached
        """
        if not self.cache_enabled:
            return None
            
        with self._lock:
            # Check if item is cached
            if not self.is_cached(item_id):
                return None
            
            # Get normalized cache key
            cache_key = self._get_cache_key(item_id)
            
            # Get cached item
            cached_item = self.items_cache.get(cache_key, {})
            
            # Return the data
            return cached_item.get('data')
    
    def cache_data(self, item_id: str, data: Any) -> bool:
        """
        Store data for an item in the cache.
        
        Args:
            item_id: The item identifier (e.g., URL, query, etc.)
            data: The data to cache
            
        Returns:
            bool: True if caching was successful
        """
        if not self.cache_enabled:
            return False
            
        with self._lock:
            # Get normalized cache key
            cache_key = self._get_cache_key(item_id)
            
            # Create cache entry
            cache_entry = {
                'id': item_id,
                'data': data,
                'timestamp': time.time(),
                'date': datetime.now().isoformat()
            }
            
            # Store in cache
            self.items_cache[cache_key] = cache_entry
            
            # Initialize status tracking if not exists
            if cache_key not in self.status_cache:
                self.status_cache[cache_key] = {
                    'id': item_id,
                    'processed_stages': {}
                }
            
            # Save to disk
            self._save_cache()
            
            return True
    
    def mark_as_processed(self, item_id: str, stage: str) -> bool:
        """
        Mark an item as processed by a specific stage.
        
        Args:
            item_id: The item identifier (e.g., URL, query, etc.)
            stage: The processing stage name
            
        Returns:
            bool: True if marking was successful
        """
        if not self.cache_enabled:
            return False
            
        with self._lock:
            # Get normalized cache key
            cache_key = self._get_cache_key(item_id)
            
            # Check if item exists in cache
            if cache_key not in self.status_cache:
                if cache_key in self.items_cache:
                    # Initialize status if item exists but status doesn't
                    self.status_cache[cache_key] = {
                        'id': item_id,
                        'processed_stages': {}
                    }
                else:
                    # Item doesn't exist in cache at all
                    logger.warning(f"Attempted to mark non-existent item as processed: {item_id}")
                    return False
            
            # Mark as processed
            self.status_cache[cache_key]['processed_stages'][stage] = {
                'timestamp': time.time(),
                'date': datetime.now().isoformat()
            }
            
            # Save to disk
            self._save_cache()
            
            return True
    
    def is_processed_by_stage(self, item_id: str, stage: str) -> bool:
        """
        Check if an item has been processed by a specific stage.
        
        Args:
            item_id: The item identifier (e.g., URL, query, etc.)
            stage: The processing stage name
            
        Returns:
            bool: True if the item has been processed by the stage
        """
        if not self.cache_enabled:
            return False
        
        with self._lock:
            # Get normalized cache key
            cache_key = self._get_cache_key(item_id)
            
            # Check if item exists and has been processed
            if cache_key not in self.status_cache:
                return False
                
            return stage in self.status_cache[cache_key].get('processed_stages', {})
    
    def reset_processing_status(self, item_id: str, stage: Optional[str] = None) -> bool:
        """
        Reset the processing status for an item, optionally for a specific stage.
        
        Args:
            item_id: The item identifier (e.g., URL, query, etc.)
            stage: The processing stage name to reset, or None to reset all stages
            
        Returns:
            bool: True if reset was successful
        """
        if not self.cache_enabled:
            return False
            
        with self._lock:
            # Get normalized cache key
            cache_key = self._get_cache_key(item_id)
            
            # Check if item exists
            if cache_key not in self.status_cache:
                return False
                
            # Reset specific stage or all stages
            if stage:
                if stage in self.status_cache[cache_key].get('processed_stages', {}):
                    del self.status_cache[cache_key]['processed_stages'][stage]
                    logger.info(f"Reset processing status for item {item_id} at stage {stage}")
            else:
                self.status_cache[cache_key]['processed_stages'] = {}
                logger.info(f"Reset all processing stages for item {item_id}")
            
            # Save to disk
            self._save_cache()
            
            return True
    
    def get_unprocessed_items(self, stage: str) -> List[str]:
        """
        Get a list of items that have not been processed by a specific stage.
        
        Args:
            stage: The processing stage name
            
        Returns:
            List[str]: List of unprocessed item IDs
        """
        if not self.cache_enabled:
            return []
            
        with self._lock:
            # Remove expired items first
            self._remove_expired_items()
            
            unprocessed = []
            
            # Check each item in cache
            for cache_key, item in self.items_cache.items():
                item_id = item.get('id')
                if not item_id:
                    continue
                    
                # Check if item has status and if it's been processed
                if (cache_key not in self.status_cache or
                        stage not in self.status_cache[cache_key].get('processed_stages', {})):
                    unprocessed.append(item_id)
            
            return unprocessed
    
    def verify_output_exists(self, item_id: str, expected_file: str) -> bool:
        """
        Verify that an expected output file exists for an item.
        
        Args:
            item_id: The item identifier
            expected_file: Path to the expected output file
            
        Returns:
            bool: True if the output file exists
        """
        # Check if file exists
        file_exists = os.path.exists(expected_file)
        
        # If file doesn't exist but item is marked as processed, reset status
        if not file_exists:
            all_stages = self.get_processing_stages(item_id)
            if all_stages:
                logger.warning(f"Expected output file {expected_file} for item {item_id} not found, resetting status")
                for stage in all_stages:
                    self.reset_processing_status(item_id, stage)
                    
        return file_exists
    
    def get_processing_stages(self, item_id: str) -> List[str]:
        """
        Get all processing stages recorded for an item.
        
        Args:
            item_id: The item identifier
            
        Returns:
            List[str]: List of stage names
        """
        if not self.cache_enabled:
            return []
            
        with self._lock:
            # Get normalized cache key
            cache_key = self._get_cache_key(item_id)
            
            # Check if item exists
            if cache_key not in self.status_cache:
                return []
                
            # Get all stages
            return list(self.status_cache[cache_key].get('processed_stages', {}).keys())
    
    def clear_cache(self, age_days: Optional[int] = None) -> int:
        """
        Clear the cache entirely or items older than specified days.
        
        Args:
            age_days: Optional, clear only items older than this many days
            
        Returns:
            int: Number of items cleared
        """
        if not self.cache_enabled:
            return 0
            
        with self._lock:
            original_count = len(self.items_cache)
            
            if age_days is not None:
                # Clear items older than the specified age
                cutoff_time = time.time() - (age_days * 86400)
                keys_to_remove = []
                
                for key, item in self.items_cache.items():
                    cached_time = item.get('timestamp', 0)
                    if cached_time < cutoff_time:
                        keys_to_remove.append(key)
                
                # Remove items and their status
                for key in keys_to_remove:
                    if key in self.items_cache:
                        del self.items_cache[key]
                    if key in self.status_cache:
                        del self.status_cache[key]
                
                cleared_count = len(keys_to_remove)
            else:
                # Clear everything
                cleared_count = original_count
                self.items_cache = {}
                self.status_cache = {}
            
            # Save changes
            self._save_cache()
            
            logger.info(f"Cleared {cleared_count} items from cache")
            return cleared_count 