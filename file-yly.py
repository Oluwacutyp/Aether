"""
Aether Reddit Plugin
Full implementation with OAuth and cookie-based auth.
"""

import re
import json
import base64
from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class RedditPlugin(WebPlugin):
    """Reddit authentication plugin."""
    
    name = "reddit"
    version = "2.0.0"
    protocols = ["https"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = "https://www.reddit.com"
        self.oauth_url = "https://oauth.reddit.com"
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        """
        Reddit login via OAuth and cookie auth.
        """
        import httpx
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/html",
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            async with httpx.AsyncClient(
                proxies=proxy,
                headers=headers,
                follow_redirects=True,
                timeout=30
            ) as client:
                
                # Get CSRF token and session
                login_page = await client.get(f"{self.base_url}/login")
                
                # Extract CSRF
                csrf_match = re.search(r'"csrf_token": "([^"]+)"', login_page.text)
                csrf_token = csrf_match.group(1) if csrf_match else ""
                
                # Reddit uses a JSON API for login
                login_data = {
                    "username": username,
                    "password": password,
                    "csrf_token": csrf_token,
                    "otp": "",
                    "dest": "https://www.reddit.com"
                }
                
                login_resp = await client.post(
                    f"{self.base_url}/login",
                    json=login_data,
                    headers={
                        **headers,
                        "Content-Type": "application/json",
                        "X-Requested-With": "XMLHttpRequest",
                        "Referer": f"{self.base_url}/login"
                    }
                )
                
                elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
                
                try:
                    data = login_resp.json()
                except:
                    data = {}
                
                # Check for success
                if login_resp.status_code == 200 and data.get("success"):
                    # Check for 2FA
                    if data.get("details", {}).get("2fa_required"):
                        return LoginResult(
                            result=AuthResult.MFA_REQUIRED,
                            username=username,
                            password=password,
                            response_time_ms=elapsed,
                            message="2FA required"
                        )
                    
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
                
                # Check for specific errors
                if data.get("details", {}).get("password"):
                    return LoginResult(
                        result=AuthResult.FAILURE,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        message="Invalid password"
                    )
                
                if data.get("details", {}).get("username"):
                    return LoginResult(
                        result=AuthResult.FAILURE,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        message="Username not found"
                    )
                
                if "rate limit" in str(data).lower():
                    return LoginResult(
                        result=AuthResult.RATE_LIMITED,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                return LoginResult(
                    result=AuthResult.UNKNOWN,
                    username=username,
                    password=password,
                    response_time_ms=elapsed,
                    metadata={"response": data}
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
        Check if Reddit username exists.
        """
        from ...core.plugin_interface import EnumerateResult
        
        try:
            import httpx
            
            async with httpx.AsyncClient(proxies=proxy, timeout=10) as client:
                resp = await client.get(
                    f"https://www.reddit.com/user/{username}/about.json",
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("data"):
                        return EnumerateResult(
                            username=username,
                            exists=True,
                            confidence=0.95,
                            indicators=["User profile accessible"]
                        )
                
                elif resp.status_code == 404:
                    return EnumerateResult(
                        username=username,
                        exists=False,
                        confidence=0.9,
                        indicators=["User not found"]
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