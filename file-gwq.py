from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class DiscordPlugin(WebPlugin):
    name = "discord"
    version = "2.0.0"
    
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        import httpx
        
        start = asyncio.get_event_loop().time()
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Origin": "https://discord.com"
            }
            
            async with httpx.AsyncClient(proxies=proxy, headers=headers) as client:
                resp = await client.post(
                    "https://discord.com/api/v9/auth/login",
                    json={
                        "login": username,
                        "password": password,
                        "undelete": False
                    }
                )
                
                elapsed = (asyncio.get_event_loop().time() - start) * 1000
                data = resp.json()
                
                if "token" in data:
                    return LoginResult(
                        result=AuthResult.SUCCESS,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        session=SessionData(
                            tokens={"token": data["token"]}
                        )
                    )
                
                if data.get("mfa") or data.get("sms"):
                    return LoginResult(
                        result=AuthResult.MFA_REQUIRED,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                if data.get("captcha_key"):
                    return LoginResult(
                        result=AuthResult.CAPTCHA,
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