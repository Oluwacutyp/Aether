from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import ProtocolPlugin, LoginResult, AuthResult


class FTPPlugin(ProtocolPlugin):
    name = "ftp"
    version = "2.0.0"
    
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        target = session or "localhost:21"
        host, port = self._parse_target(target)
        
        start = asyncio.get_event_loop().time()
        
        try:
            from ftplib import FTP
            
            ftp = FTP()
            ftp.connect(host, port, timeout=self.timeout)
            ftp.login(username, password)
            
            elapsed = (asyncio.get_event_loop().time() - start) * 1000
            
            # Test access
            welcome = ftp.getwelcome()
            ftp.quit()
            
            return LoginResult(
                result=AuthResult.SUCCESS,
                username=username,
                password=password,
                response_time_ms=elapsed,
                message=welcome
            )
            
        except Exception as e:
            elapsed = (asyncio.get_event_loop().time() - start) * 1000
            error = str(e).lower()
            
            if "530" in error or "authentication" in error:
                return LoginResult(
                    result=AuthResult.FAILURE,
                    username=username,
                    password=password,
                    response_time_ms=elapsed
                )
            
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
        return target, 21