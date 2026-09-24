from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import ProtocolPlugin, LoginResult, AuthResult


class SMTPPlugin(ProtocolPlugin):
    name = "smtp"
    version = "2.0.0"
    
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        target = session or "localhost:587"
        host, port = self._parse_target(target)
        
        start = asyncio.get_event_loop().time()
        
        try:
            import aiosmtplib
            
            smtp = aiosmtplib.SMTP(hostname=host, port=port, timeout=self.timeout)
            await smtp.connect()
            
            if port == 587:
                await smtp.starttls()
            
            await smtp.login(username, password)
            
            elapsed = (asyncio.get_event_loop().time() - start) * 1000
            
            await smtp.quit()
            
            return LoginResult(
                result=AuthResult.SUCCESS,
                username=username,
                password=password,
                response_time_ms=elapsed
            )
            
        except aiosmtplib.SMTPAuthenticationError:
            elapsed = (asyncio.get_event_loop().time() - start) * 1000
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
    
    def _parse_target(self, target: str):
        if ':' in target:
            host, port = target.rsplit(':', 1)
            return host, int(port)
        return target, 587