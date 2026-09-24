from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class FacebookPlugin(WebPlugin):
    name = "facebook"
    version = "2.0.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = "https://www.facebook.com"
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        import httpx
        
        start = asyncio.get_event_loop().time()
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            
            async with httpx.AsyncClient(proxies=proxy, headers=headers, follow_redirects=True) as client:
                # Get login page
                resp = await client.get("https://www.facebook.com/login.php")
                
                # Extract form data
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'html.parser')
                form = soup.find('form', {'id': 'login_form'})
                
                if not form:
                    return LoginResult(
                        result=AuthResult.ERROR,
                        username=username,
                        password=password,
                        message="Login form not found"
                    )
                
                login_data = {
                    "email": username,
                    "pass": password,
                    "login": "Log In"
                }
                
                # Add hidden fields
                for hidden in form.find_all('input', type='hidden'):
                    if hidden.get('name'):
                        login_data[hidden['name']] = hidden.get('value', '')
                
                # Submit
                resp = await client.post(
                    "https://www.facebook.com/login.php",
                    data=login_data
                )
                
                elapsed = (asyncio.get_event_loop().time() - start) * 1000
                
                # Check for c_user cookie (success indicator)
                if "c_user" in [c.name for c in client.cookies.jar]:
                    return LoginResult(
                        result=AuthResult.SUCCESS,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        session=SessionData(
                            cookies={c.name: c.value for c in client.cookies.jar},
                            user_agent=headers["User-Agent"],
                            proxy_used=proxy
                        )
                    )
                
                text = resp.text.lower()
                
                if "the password you" in text or "incorrect password" in text:
                    return LoginResult(
                        result=AuthResult.FAILURE,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                if "temporarily blocked" in text:
                    return LoginResult(
                        result=AuthResult.LOCKOUT,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                if "two-factor" in text or "security code" in text:
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