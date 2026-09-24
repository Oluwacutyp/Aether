"""
Aether Twitter/X Plugin
Full implementation with API v1.1 and v2 endpoints.
"""

import re
import json
import base64
from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class TwitterPlugin(WebPlugin):
    """Twitter/X authentication plugin."""
    
    name = "twitter"
    version = "2.0.0"
    protocols = ["https"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = "https://twitter.com"
        self.api_url = "https://api.twitter.com"
        self.auth_url = "https://api.twitter.com/auth/1.1"
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        """
        Twitter login via web flow with CSRF handling.
        """
        import httpx
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
            }
            
            async with httpx.AsyncClient(
                proxies=proxy,
                headers=headers,
                follow_redirects=True,
                timeout=30
            ) as client:
                
                # Step 1: Get login page for tokens
                login_page = await client.get(
                    "https://twitter.com/i/flow/login",
                    headers={"Referer": "https://twitter.com/"}
                )
                
                # Extract CSRF token and flow token
                ct0_match = re.search(r'ct0=([a-f0-9]+)', str(client.cookies))
                csrf_token = ct0_match.group(1) if ct0_match else ""
                
                # Get att (authentication token)
                att_match = re.search(r'"att":"([^"]+)"', login_page.text)
                att = att_match.group(1) if att_match else ""
                
                # Step 2: Submit username
                user_payload = {
                    "flow_token": self._extract_flow_token(login_page.text),
                    "subtask_inputs": [
                        {
                            "subtask_id": "LoginEnterUserIdentifier",
                            "settings_list": {
                                "setting_responses": [
                                    {
                                        "key": "user_identifier",
                                        "response_data": {
                                            "text_data": {"result": username}
                                        }
                                    }
                                ],
                                "link": "next_link"
                            }
                        }
                    ]
                }
                
                headers["Content-Type"] = "application/json"
                headers["X-CSRF-Token"] = csrf_token
                headers["X-Twitter-Client-Version"] = "Twitter-TweetDeck-blackbird-chrome/1.0.0"
                
                user_resp = await client.post(
                    "https://api.twitter.com/1.1/onboarding/task.json",
                    json=user_payload,
                    headers=headers
                )
                
                user_data = user_resp.json()
                
                # Step 3: Submit password
                if "LoginEnterPassword" in str(user_data):
                    pass_payload = {
                        "flow_token": user_data.get("flow_token"),
                        "subtask_inputs": [
                            {
                                "subtask_id": "LoginEnterPassword",
                                "enter_password": {
                                    "password": password,
                                    "link": "next_link"
                                }
                            }
                        ]
                    }
                    
                    pass_resp = await client.post(
                        "https://api.twitter.com/1.1/onboarding/task.json",
                        json=pass_payload,
                        headers=headers
                    )
                    
                    pass_data = pass_resp.json()
                    
                    elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
                    
                    # Check result
                    if "LoginSuccessSubtask" in str(pass_data):
                        # Extract auth tokens
                        auth_token = None
                        for cookie in client.cookies.jar:
                            if cookie.name == "auth_token":
                                auth_token = cookie.value
                                break
                        
                        session_data = SessionData(
                            cookies=dict(client.cookies),
                            headers={k: v for k, v in headers.items() if k.startswith('X-')},
                            tokens={"auth_token": auth_token} if auth_token else {},
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
                    
                    elif "LoginEnterAlternateIdentifierSubtask" in str(pass_data):
                        return LoginResult(
                            result=AuthResult.MFA_REQUIRED,
                            username=username,
                            password=password,
                            response_time_ms=elapsed,
                            message="Additional verification required"
                        )
                    
                    elif "error" in pass_data:
                        error_code = pass_data.get("errors", [{}])[0].get("code", 0)
                        if error_code == 32:  # Could not authenticate you
                            return LoginResult(
                                result=AuthResult.FAILURE,
                                username=username,
                                password=password,
                                response_time_ms=elapsed,
                                message="Invalid credentials"
                            )
                        
                        elif error_code == 326:  # Account temporarily locked
                            return LoginResult(
                                result=AuthResult.LOCKOUT,
                                username=username,
                                password=password,
                                response_time_ms=elapsed
                            )
                
                elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
                
                return LoginResult(
                    result=AuthResult.UNKNOWN,
                    username=username,
                    password=password,
                    response_time_ms=elapsed,
                    metadata={"response": user_data}
                )
                
        except Exception as e:
            return LoginResult(
                result=AuthResult.ERROR,
                username=username,
                password=password,
                message=str(e)
            )
    
    def _extract_flow_token(self, html: str) -> str:
        """Extract flow token from HTML."""
        match = re.search(r'"flow_token":"([^"]+)"', html)
        return match.group(1) if match else ""
    
    async def enumerate(self, username: str,
                       session: Optional[Any] = None,
                       proxy: Optional[str] = None) -> Any:
        """
        Check if Twitter username exists via API.
        """
        from ...core.plugin_interface import EnumerateResult
        
        try:
            import httpx
            
            async with httpx.AsyncClient(proxies=proxy, timeout=10) as client:
                # Check via user lookup
                resp = await client.get(
                    f"https://api.twitter.com/1.1/users/lookup.json",
                    params={"screen_name": username}
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data and len(data) > 0:
                        return EnumerateResult(
                            username=username,
                            exists=True,
                            confidence=0.95,
                            indicators=["API returned user data"]
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