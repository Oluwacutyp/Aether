from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class SpotifyPlugin(WebPlugin):
    name = "spotify"
    version = "2.0.0"
    
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        import httpx
        
        start = asyncio.get_event_loop().time()
        
        try:
            async with httpx.AsyncClient(proxies=proxy) as client:
                # Get CSRF
                resp = await client.get("https://accounts.spotify.com/en/login")
                
                # Login
                resp = await client.post(
                    "https://accounts.spotify.com/api/login",
                    data={
                        "username": username,
                        "password": password,
                        "remember": False
                    }
                )
                
                elapsed = (asyncio.get_event_loop().time() - start) * 1000
                
                if "error" not in resp.text and resp.status_code == 200:
                    return LoginResult(
                        result=AuthResult.SUCCESS,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        session=SessionData(cookies=dict(client.cookies))
                    )
                
                if "errorInvalidCredentials" in resp.text:
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