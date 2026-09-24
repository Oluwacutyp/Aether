from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class YahooPlugin(WebPlugin):
    name = "yahoo"
    version = "2.0.0"
    
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        import httpx
        
        start = asyncio.get_event_loop().time()
        
        try:
            async with httpx.AsyncClient(proxies=proxy, follow_redirects=True) as client:
                # Get login page
                resp = await client.get("https://login.yahoo.com/")
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Extract tokens
                import re
                crumb_match = re.search(r'"crumb":"([^"]+)"', resp.text)
                crumb = crumb_match.group(1) if crumb_match else ""
                
                session_match = re.search(r'"sessionId":"([^"]+)"', resp.text)
                session_id = session_match.group(1) if session_match else ""
                
                # Step 1: Submit username
                user_data = {
                    "identifier": username,
                    "crumb": crumb,
                    "sessionId": session_id
                }
                
                resp = await client.post(
                    "https://login.yahoo.com/",
                    json=user_data
                )
                
                # Step 2: Submit password
                pass_data = {
                    "password": password,
                    "crumb": crumb,
                    "sessionId": session_id
                }
                
                resp = await client.post(
                    "https://login.yahoo.com/",
                    json=pass_data
                )
                
                elapsed = (asyncio.get_event_loop().time() - start) * 1000
                
                if "mail.yahoo.com" in str(resp.url) or "success" in resp.text:
                    return LoginResult(
                        result=AuthResult.SUCCESS,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        session=SessionData(cookies=dict(client.cookies))
                    )
                
                if "password" in resp.text.lower() and "incorrect" in resp.text.lower():
                    return LoginResult(
                        result=AuthResult.FAILURE,
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