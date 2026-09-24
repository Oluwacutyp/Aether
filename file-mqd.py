from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class InstagramPlugin(WebPlugin):
    name = "instagram"
    version = "2.0.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = "https://www.instagram.com"
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        import httpx
        import re
        
        start = asyncio.get_event_loop().time()
        
        try:
            headers = {
                "User-Agent": "Instagram 279.0.0.0.12 Android",
                "Accept": "*/*",
                "X-IG-App-ID": "567067343352427"
            }
            
            async with httpx.AsyncClient(proxies=proxy, headers=headers) as client:
                # Get CSRF
                resp = await client.get(f"{self.base_url}/accounts/login/")
                csrf_match = re.search(r'"csrf_token":"([^"]+)"', resp.text)
                csrf = csrf_match.group(1) if csrf_match else ""
                
                headers["X-CSRFToken"] = csrf
                headers["Referer"] = "https://www.instagram.com/accounts/login/"
                
                # Login via API
                login_data = {
                    "username": username,
                    "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{int(asyncio.get_event_loop().time())}:{password}",
                    "queryParams": "{}",
                    "optIntoOneTap": "false"
                }
                
                resp = await client.post(
                    f"{self.base_url}/accounts/login/ajax/",
                    data=login_data
                )
                
                elapsed = (asyncio.get_event_loop().time() - start) * 1000
                
                data = resp.json()
                
                if data.get("authenticated") is True:
                    return LoginResult(
                        result=AuthResult.SUCCESS,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        session=SessionData(
                            cookies=dict(client.cookies),
                            user_agent=headers["User-Agent"],
                            proxy_used=proxy
                        )
                    )
                
                if data.get("authenticated") is False:
                    return LoginResult(
                        result=AuthResult.FAILURE,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                if data.get("checkpoint_url"):
                    return LoginResult(
                        result=AuthResult.MFA_REQUIRED,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                if "rate_limit" in str(data).lower():
                    return LoginResult(
                        result=AuthResult.RATE_LIMITED,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                return LoginResult(
                    result=AuthResult.UNKNOWN,
                    username=username,
                    password=password,
                    response_time_ms=elapsed,
                    metadata=data
                )
                
        except Exception as e:
            return LoginResult(
                result=AuthResult.ERROR,
                username=username,
                password=password,
                message=str(e)
            )