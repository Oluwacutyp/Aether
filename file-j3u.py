from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class RedditPlugin(WebPlugin):
    name = "reddit"
    version = "2.0.0"
    
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        import httpx
        
        start = asyncio.get_event_loop().time()
        
        try:
            async with httpx.AsyncClient(proxies=proxy, follow_redirects=True) as client:
                # Get CSRF
                resp = await client.get("https://www.reddit.com/login/")
                import re
                csrf_match = re.search(r'"csrfToken": "([^"]+)"', resp.text)
                csrf = csrf_match.group(1) if csrf_match else ""
                
                # Login
                login_data = {
                    "username": username,
                    "password": password,
                    "csrf_token": csrf,
                    "dest": "https://www.reddit.com"
                }
                
                resp = await client.post(
                    "https://www.reddit.com/api/login",
                    data=login_data
                )
                
                elapsed = (asyncio.get_event_loop().time() - start) * 1000
                data = resp.json()
                
                if data.get("success"):
                    return LoginResult(
                        result=AuthResult.SUCCESS,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        session=SessionData(cookies=dict(client.cookies))
                    )
                
                if data.get("error") == 1002:
                    return LoginResult(
                        result=AuthResult.MFA_REQUIRED,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                return LoginResult(
                    result=AuthResult.FAILURE,
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