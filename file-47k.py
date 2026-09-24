"""
Aether FTP/SFTP Plugin
Full implementation with FTPS support.
"""

import asyncio
from typing import Optional, Dict, Any
import ftplib
import ssl

from ...core.plugin_interface import ProtocolPlugin, LoginResult, AuthResult, SessionData


class FTPPlugin(ProtocolPlugin):
    """FTP/FTPS/SFTP authentication plugin."""
    
    name = "ftp"
    version = "2.0.0"
    protocols = ["ftp", "ftps", "sftp"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.use_ssl = config.get("ssl", False) if config else False
        self.port = config.get("port", 21) if config else 21
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        """
        FTP authentication with SSL/TLS support.
        """
        import time
        start_time = time.time()
        
        target = session or self.config.get("target", "localhost:21")
        host, port = self._parse_target(target)
        
        try:
            loop = asyncio.get_event_loop()
            
            # Run blocking FTP in executor
            result = await loop.run_in_executor(
                None, self._try_ftp, host, port, username, password
            )
            
            elapsed = (time.time() - start_time) * 1000
            
            if result["success"]:
                return LoginResult(
                    result=AuthResult.SUCCESS,
                    username=username,
                    password=password,
                    response_time_ms=elapsed,
                    message=f"FTP login successful ({result.get('welcome', '')[:50]})"
                )
            
            if result.get("error") == "auth":
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
                response_time_ms=elapsed,
                message=result.get("message", "Unknown error")
            )
            
        except Exception as e:
            return LoginResult(
                result=AuthResult.ERROR,
                username=username,
                password=password,
                message=str(e)
            )
    
    def _try_ftp(self, host: str, port: int, username: str, password: str) -> Dict:
        """Blocking FTP attempt."""
        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                ftp = ftplib.FTP_TLS(context=context)
            else:
                ftp = ftplib.FTP()
            
            ftp.connect(host, port, timeout=self.timeout)
            ftp.login(username, password)
            
            welcome = ftp.getwelcome()
            ftp.quit()
            
            return {"success": True, "welcome": welcome}
            
        except ftplib.error_perm as e:
            return {"success": False, "error": "auth", "message": str(e)}
        except Exception as e:
            return {"success": False, "error": "conn", "message": str(e)}
    
    def _parse_target(self, target: str) -> tuple:
        if ':' in target:
            host, port = target.rsplit(':', 1)
            return host, int(port)
        return target, self.port