from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class GitHubPlugin(WebPlugin):
    name = "github"
    version = "2.0.0"
    
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        import httpx
        
        start = asyncio.get_event_loop().time()
        
        try:
            async with httpx.AsyncClient(proxies=proxy, follow_redirects=True) as client:
                # Get login page for authenticity token
                resp = await client.get("https://github.com/login")
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'html.parser')
                token_input = soup.find('input', {'name': 'authenticity_token'})
                token = token_input.get('value') if token_input else ''
                
                # Login
                login_data = {
                    "login": username,
                    "password": password,
                    "authenticity_token": token,
                    "commit": "Sign in"
                }
                
                resp = await client.post(
                    "https://github.com/session",
                    data=login_data
                )
                
                elapsed = (asyncio.get_event_loop().time() - start) * 1000
                
                # Check for session cookie
                if "user_session" in [c.name for c in client.cookies.jar]:
                    return LoginResult(
                        result=AuthResult.SUCCESS,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        session=SessionData(cookies=dict(client.cookies))
                    )
                
                if "Incorrect username or password" in resp.text:
                    return LoginResult(
                        result=AuthResult.FAILURE,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                if "two-factor" in resp.text.lower():
                    return LoginResult(
                        result=AuthResult.MFA_REQUIRED,
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