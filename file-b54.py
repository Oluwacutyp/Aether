from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class TikTokPlugin(WebPlugin):
    name = "tiktok"
    version = "2.0.0"
    
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        import httpx
        
        start = asyncio.get_event_loop().time()
        
        try:
            async with httpx.AsyncClient(proxies=proxy) as client:
                resp = await client.post(
                    "https://www.tiktok.com/passport/web/login",
                    data={
                        "username": username,
                        "password": password,
                        "mix_mode": 1
                    }
                )
                
                elapsed = (asyncio.get_event_loop().time() - start) * 1000
                data = resp.json()
                
                if data.get("data", {}).get("redirect_url"):
                    return LoginResult(
                        result=AuthResult.SUCCESS,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        session=SessionData(cookies=dict(client.cookies))
                    )
                
                error_code = data.get("data", {}).get("error_code")
                if error_code in [1009, 1011]:
                    return LoginResult(
                        result=AuthResult.FAILURE,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                if error_code == 1021:
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