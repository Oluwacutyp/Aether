from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class GmailPlugin(WebPlugin):
    name = "gmail"
    version = "2.0.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = "https://accounts.google.com"
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        import httpx
        
        start = asyncio.get_event_loop().time()
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            async with httpx.AsyncClient(proxies=proxy, headers=headers, timeout=30) as client:
                # Step 1: Get login page
                resp = await client.get(
                    "https://accounts.google.com/signin/v2/identifier",
                    params={"hl": "en", "flowName": "GlifWebSignIn"}
                )
                
                # Extract flow token
                import re
                match = re.search(r'\"flowToken\":\"([^\"]+)\"', resp.text)
                flow_token = match.group(1) if match else ""
                
                # Step 2: Submit identifier
                id_data = {
                    "identifier": username,
                    "flowToken": flow_token,
                    "flowName": "GlifWebSignIn"
                }
                
                resp = await client.post(
                    "https://accounts.google.com/signin/v2/identifier",
                    data=id_data
                )
                
                # Check if account exists
                if "Couldn't find your Google Account" in resp.text:
                    elapsed = (asyncio.get_event_loop().time() - start) * 1000
                    return LoginResult(
                        result=AuthResult.FAILURE,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        message="Account not found"
                    )
                
                # Step 3: Submit password (simplified - real flow has more steps)
                pass_data = {
                    "password": password,
                    "flowToken": flow_token
                }
                
                # Note: Full implementation requires handling multiple redirects
                # and JavaScript challenges. This is the HTTP structure.
                
                elapsed = (asyncio.get_event_loop().time() - start) * 1000
                
                # Check response indicators
                if "myaccount.google.com" in str(resp.url) or "mail.google.com" in str(resp.url):
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
                
                if "Wrong password" in resp.text or "password is incorrect" in resp.text:
                    return LoginResult(
                        result=AuthResult.FAILURE,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                if "2-Step" in resp.text or "two step" in resp.text.lower():
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