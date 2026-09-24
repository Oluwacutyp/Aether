"""
Aether Discord Plugin
Full implementation with full login flow and token extraction.
"""

import re
import json
from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class DiscordPlugin(WebPlugin):
    """Discord authentication plugin."""
    
    name = "discord"
    version = "2.0.0"
    protocols = ["https"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = "https://discord.com"
        self.api_url = "https://discord.com/api/v9"
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        """
        Discord login with MFA support and token extraction.
        """
        import httpx
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/json",
                "Origin": "https://discord.com",
                "Referer": "https://discord.com/login"
            }
            
            async with httpx.AsyncClient(
                proxies=proxy,
                headers=headers,
                follow_redirects=True,
                timeout=30
            ) as client:
                
                # Discord uses email for login, not username
                # But we'll try to handle both
                
                login_data = {
                    "login": username,  # Can be email or phone
                    "password": password,
                    "undelete": False,
                    "captcha_key": None,
                    "login_source": None,
                    "gift_code_sku_id": None
                }
                
                resp = await client.post(
                    f"{self.api_url}/auth/login",
                    json=login_data
                )
                
                elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
                
                try:
                    data = resp.json()
                except:
                    data = {}
                
                # Check for token (success)
                token = data.get("token")
                
                if token:
                    session_data = SessionData(
                        cookies=dict(client.cookies),
                        headers=headers,
                        tokens={"auth_token": token},
                        user_agent=headers["User-Agent"],
                        proxy_used=proxy
                    )
                    
                    return LoginResult(
                        result=AuthResult.SUCCESS,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        session=session_data,
                        message="Login successful"
                    )
                
                # Check for MFA
                if data.get("mfa") or data.get("ticket"):
                    return LoginResult(
                        result=AuthResult.MFA_REQUIRED,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        message="2FA required",
                        metadata={"ticket": data.get("ticket")}
                    )
                
                # Check for CAPTCHA
                if data.get("captcha_key") or data.get("captcha_sitekey"):
                    return LoginResult(
                        result=AuthResult.CAPTCHA,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                # Check errors
                errors = data.get("errors", {})
                
                if "login" in errors or "password" in errors:
                    return LoginResult(
                        result=AuthResult.FAILURE,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        message="Invalid credentials"
                    )
                
                if data.get("code") == 429:
                    return LoginResult(
                        result=AuthResult.RATE_LIMITED,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        message=data.get("message", "Rate limited")
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
        Discord doesn't really support enumeration via public API.
        """
        from ...core.plugin_interface import EnumerateResult
        
        return EnumerateResult(
            username=username,
            exists=None,
            confidence=0.0,
            indicators=["Discord does not support enumeration"]
        )