"""
CAPTCHA Solver for the Web Scraping Toolkit.

This module provides functionality to solve various types of CAPTCHA challenges,
including reCAPTCHA, hCAPTCHA, and image-based CAPTCHAs.
"""

import os
import time
from typing import Optional, Dict, Any, Union, cast
from twocaptcha import TwoCaptcha, NetworkException

from ..utils.logger import get_logger
from ..utils.config import get_captcha_config

# Initialize logger
logger = get_logger("captcha_solver")

class CaptchaSolver:
    """
    CAPTCHA solving service that integrates with 2Captcha and similar services.
    
    This class can:
    - Solve reCAPTCHA v2 and v3
    - Solve hCaptcha
    - Solve image-based CAPTCHAs
    - Automatically detect and solve CAPTCHAs in a Playwright page
    """
    
    def __init__(self, api_key: Optional[str] = None, service: Optional[str] = None):
        """
        Initialize the CAPTCHA solver with optional custom settings.
        
        Args:
            api_key: API key for the CAPTCHA solving service (overrides config)
            service: CAPTCHA service name (e.g., '2captcha') (overrides config)
        """
        # Load configuration
        config = get_captcha_config()
        
        # Override configuration with constructor parameters if provided
        self.api_key = api_key or config.get("api_key", "")
        self.service = service or config.get("service", "2captcha")
        
        # Initialize solver client
        self.solver = None
        if self.api_key:
            try:
                self.solver = TwoCaptcha(self.api_key)
                logger.info(f"{self.service} CAPTCHA solver initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize {self.service} client: {e}")
        else:
            logger.warning(f"No {self.service} API key provided, CAPTCHA solving will be unavailable")
    
    def is_available(self) -> bool:
        """
        Check if the CAPTCHA solving service is available.
        
        Returns:
            bool: True if the service is available
        """
        return self.solver is not None
    
    def get_balance(self) -> Optional[float]:
        """
        Get the account balance for the CAPTCHA solving service.
        
        Returns:
            Optional[float]: Account balance or None if unavailable
        """
        if not self.is_available():
            logger.warning("CAPTCHA solving service is not available, cannot get balance")
            return None
        
        try:
            balance = cast(float, self.solver.balance())
            logger.info(f"{self.service} account balance: ${balance:.2f}")
            return balance
        except Exception as e:
            logger.error(f"Failed to get {self.service} account balance: {e}")
            return None
    
    def solve_recaptcha(
        self,
        site_key: str,
        page_url: str,
        invisible: bool = False,
        timeout: int = 120
    ) -> Optional[str]:
        """
        Solve a reCAPTCHA challenge.
        
        Args:
            site_key: The site key for the reCAPTCHA
            page_url: The URL of the page containing the reCAPTCHA
            invisible: Whether the reCAPTCHA is invisible
            timeout: Maximum time to wait for a solution in seconds
            
        Returns:
            Optional[str]: The solution token or None if solving fails
        """
        if not self.is_available():
            logger.warning("CAPTCHA solving service is not available, cannot solve reCAPTCHA")
            return None
        
        try:
            logger.info(f"Solving reCAPTCHA on {page_url} with site key {site_key[:10]}...")
            
            # Send the task to 2Captcha
            result = self.solver.recaptcha(
                sitekey=site_key,
                url=page_url,
                invisible=invisible,
                version="v2"
            )
            
            if result and "code" in result:
                logger.info(f"reCAPTCHA solved successfully, got token: {result['code'][:15]}...")
                return result["code"]
            else:
                logger.warning("reCAPTCHA solving failed, no valid result returned")
                return None
                
        except NetworkException as e:
            logger.error(f"Network error while solving reCAPTCHA: {e}")
            return None
        except Exception as e:
            logger.error(f"Error solving reCAPTCHA: {e}")
            return None
    
    def solve_recaptcha_v3(
        self,
        site_key: str,
        page_url: str,
        action: str = "verify",
        min_score: float = 0.7,
        timeout: int = 120
    ) -> Optional[str]:
        """
        Solve a reCAPTCHA v3 challenge.
        
        Args:
            site_key: The site key for the reCAPTCHA
            page_url: The URL of the page containing the reCAPTCHA
            action: The action value for the reCAPTCHA
            min_score: Minimum required score
            timeout: Maximum time to wait for a solution in seconds
            
        Returns:
            Optional[str]: The solution token or None if solving fails
        """
        if not self.is_available():
            logger.warning("CAPTCHA solving service is not available, cannot solve reCAPTCHA v3")
            return None
        
        try:
            logger.info(f"Solving reCAPTCHA v3 on {page_url} with site key {site_key[:10]}...")
            
            # Send the task to 2Captcha
            result = self.solver.recaptcha(
                sitekey=site_key,
                url=page_url,
                version="v3",
                action=action,
                score=min_score
            )
            
            if result and "code" in result:
                logger.info(f"reCAPTCHA v3 solved successfully, got token: {result['code'][:15]}...")
                return result["code"]
            else:
                logger.warning("reCAPTCHA v3 solving failed, no valid result returned")
                return None
                
        except NetworkException as e:
            logger.error(f"Network error while solving reCAPTCHA v3: {e}")
            return None
        except Exception as e:
            logger.error(f"Error solving reCAPTCHA v3: {e}")
            return None
    
    def solve_hcaptcha(
        self,
        site_key: str,
        page_url: str,
        timeout: int = 120
    ) -> Optional[str]:
        """
        Solve an hCaptcha challenge.
        
        Args:
            site_key: The site key for the hCaptcha
            page_url: The URL of the page containing the hCaptcha
            timeout: Maximum time to wait for a solution in seconds
            
        Returns:
            Optional[str]: The solution token or None if solving fails
        """
        if not self.is_available():
            logger.warning("CAPTCHA solving service is not available, cannot solve hCaptcha")
            return None
        
        try:
            logger.info(f"Solving hCaptcha on {page_url} with site key {site_key[:10]}...")
            
            # Send the task to 2Captcha
            result = self.solver.hcaptcha(
                sitekey=site_key,
                url=page_url
            )
            
            if result and "code" in result:
                logger.info(f"hCaptcha solved successfully, got token: {result['code'][:15]}...")
                return result["code"]
            else:
                logger.warning("hCaptcha solving failed, no valid result returned")
                return None
                
        except NetworkException as e:
            logger.error(f"Network error while solving hCaptcha: {e}")
            return None
        except Exception as e:
            logger.error(f"Error solving hCaptcha: {e}")
            return None
    
    def solve_image_captcha(
        self,
        image_path: str,
        timeout: int = 60
    ) -> Optional[str]:
        """
        Solve an image-based CAPTCHA.
        
        Args:
            image_path: Path to the image file
            timeout: Maximum time to wait for a solution in seconds
            
        Returns:
            Optional[str]: The solution text or None if solving fails
        """
        if not self.is_available():
            logger.warning("CAPTCHA solving service is not available, cannot solve image CAPTCHA")
            return None
        
        try:
            logger.info(f"Solving image CAPTCHA from {image_path}")
            
            # Send the task to 2Captcha
            result = self.solver.normal(image_path)
            
            if result and "code" in result:
                logger.info(f"Image CAPTCHA solved successfully: {result['code']}")
                return result["code"]
            else:
                logger.warning("Image CAPTCHA solving failed, no valid result returned")
                return None
                
        except NetworkException as e:
            logger.error(f"Network error while solving image CAPTCHA: {e}")
            return None
        except Exception as e:
            logger.error(f"Error solving image CAPTCHA: {e}")
            return None
    
    def apply_recaptcha_solution(self, page: Any, solution: str) -> bool:
        """
        Apply a reCAPTCHA solution to a Playwright page.
        
        Args:
            page: Playwright page object
            solution: The reCAPTCHA solution token
            
        Returns:
            bool: True if the solution was successfully applied
        """
        try:
            # Apply the solution via JavaScript
            script = f"""
                () => {{
                    // First try the standard approach
                    const textarea = document.querySelector('textarea#g-recaptcha-response');
                    if (textarea) {{
                        textarea.innerHTML = '{solution}';
                        textarea.value = '{solution}';
                        textarea.dispatchEvent(new Event('change'));
                    }}
                    
                    // For invisible reCAPTCHA and callbacks
                    if (typeof ___grecaptcha_cfg !== 'undefined') {{
                        Object.keys(___grecaptcha_cfg.clients).forEach(function(key) {{
                            const client = ___grecaptcha_cfg.clients[key];
                            
                            // Handle different versions of reCAPTCHA structure
                            if (client && typeof client === 'object') {{
                                // Modern structure
                                Object.values(client).forEach(function(obj) {{
                                    if (obj && typeof obj.callback === 'function') {{
                                        obj.callback('{solution}');
                                    }}
                                }});
                                
                                // Legacy structure
                                if (client.S && client.S.S) {{
                                    client.S.S.callback('{solution}');
                                }}
                            }}
                        }});
                    }}
                    
                    return true;
                }}
            """
            
            result = page.evaluate(script)
            if result:
                logger.info("Successfully applied reCAPTCHA solution to page")
                return True
            else:
                logger.warning("Failed to apply reCAPTCHA solution to page")
                return False
                
        except Exception as e:
            logger.error(f"Error applying reCAPTCHA solution: {e}")
            return False

    def detect_and_solve_recaptcha(self, page: Any) -> bool:
        """
        Detect if a page has a reCAPTCHA and attempt to solve it.
        
        Args:
            page: Playwright page object
            
        Returns:
            bool: True if a CAPTCHA was detected and solved successfully
        """
        try:
            # Detect reCAPTCHA presence using various indicators
            has_recaptcha = page.evaluate("""
                () => {
                    // Check for common reCAPTCHA elements
                    const recaptchaDiv = document.querySelector('.g-recaptcha');
                    const recaptchaIframe = document.querySelector('iframe[src*="recaptcha"]');
                    const recaptchaScript = document.querySelector('script[src*="recaptcha"]');
                    const recaptchaCallback = typeof window.grecaptcha !== 'undefined';
                    
                    // Return detection result
                    return {
                        detected: !!(recaptchaDiv || recaptchaIframe || recaptchaScript || recaptchaCallback),
                        siteKey: recaptchaDiv ? recaptchaDiv.getAttribute('data-sitekey') : null,
                        isInvisible: recaptchaDiv ? recaptchaDiv.getAttribute('data-size') === 'invisible' : false
                    };
                }
            """)
            
            if not has_recaptcha or not has_recaptcha.get('detected', False):
                logger.info("No reCAPTCHA detected on page")
                return False
            
            site_key = has_recaptcha.get('siteKey')
            is_invisible = has_recaptcha.get('isInvisible', False)
            
            if not site_key:
                logger.warning("reCAPTCHA detected but could not extract site key")
                
                # Take a screenshot for debugging
                screenshot_dir = "captcha_screenshots"
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_path = f"{screenshot_dir}/recaptcha_unknown_{int(time.time())}.png"
                page.screenshot(path=screenshot_path)
                logger.info(f"Saved screenshot of CAPTCHA page to {screenshot_path}")
                
                return False
            
            # Solve the reCAPTCHA
            solution = self.solve_recaptcha(
                site_key=site_key,
                page_url=page.url,
                invisible=is_invisible
            )
            
            if not solution:
                return False
            
            # Apply the solution
            return self.apply_recaptcha_solution(page, solution)
            
        except Exception as e:
            logger.error(f"Error detecting and solving reCAPTCHA: {e}")
            return False 