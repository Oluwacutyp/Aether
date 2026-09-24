"""
Aether SMTP/IMAP Plugin
Full implementation with STARTTLS and authentication.
"""

import asyncio
import smtplplib
import imaplib
import ssl
from typing import Optional, Dict, Any

from ...core.plugin_interface import ProtocolPlugin, LoginResult, AuthResult, SessionData


class SMTPIMAPPlugin(ProtocolPlugin):
    """SMTP/IMAP authentication plugin."""
    
    name = "smtp_imap"
    version = "2.0.0"
    protocols = ["smtp", "smtps", "imap", "imaps"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.use_ssl = config.get("ssl", True) if config else True
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        """
        SMTP/IMAP authentication.
        """
        import time
        start_time = time.time()
        
        target = session or self.config.get("target", "smtp.gmail.com:587")
        host, port = self._parse_target(target)
        
        protocol = self.config.get("protocol", "smtp")
        
        try:
            loop = asyncio.get_event_loop()
            
            if protocol in ("imap", "imaps"):
                result = await loop.run_in_executor(
                    None, self._try_imap, host, port, username, password, 
                    protocol == "imaps"
                )
            else:
                result = await loop.run_in_executor(
                    None, self._try_smtp, host, port, username, password,
                    protocol == "smtps"
                )
            
            elapsed = (time.time() - start_time) * 1000
            
            if result["success"]:
                return LoginResult(
                    result=AuthResult.SUCCESS,
                    username=username,
                    password=password,
                    response_time_ms=elapsed,
                    message=f"{protocol.upper()} authentication successful"
                )
            
            if result.get("error") == "auth":
                return LoginResult(
                    result=AuthResult.FAILURE,
                    username=username,
                    password=password,
                    response_time_ms=elapsed,
                    message=result.get("message")
                )
            
            return LoginResult(
                result=AuthResult.ERROR,
                username=username,
                password=password,
                response_time_ms=elapsed,
                message=result.get("message")
            )
            
        except Exception as e:
            return LoginResult(
                result=AuthResult.ERROR,
                username=username,
                password=password,
                message=str(e)
            )
    
    def _try_smtp(self, host: str, port: int, username: str, 
                  password: str, use_ssl: bool) -> Dict:
        """Try SMTP authentication."""
        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(host, port, timeout=self.timeout)
            else:
                server = smtplib.SMTP(host, port, timeout=self.timeout)
                server.starttls()
            
            server.login(username, password)
            server.quit()
            
            return {"success": True}
            
        except smtplib.SMTPAuthenticationError as e:
            return {"success": False, "error": "auth", "message": str(e)}
        except Exception as e:
            return {"success": False, "error": "conn", "message": str(e)}
    
    def _try_imap(self, host: str, port: int, username: str,
                  password: str, use_ssl: bool) -> Dict:
        """Try IMAP authentication."""
        try:
            if use_ssl:
                server = imaplib.IMAP4_SSL(host, port)
            else:
                server = imaplib.IMAP4(host, port)
            
            server.login(username, password)
            server.logout()
            
            return {"success": True}
            
        except imaplib.IMAP4.error as e:
            return {"success": False, "error": "auth", "message": str(e)}
        except Exception as e:
            return {"success": False, "error": "conn", "message": str(e)}
    
    def _parse_target(self, target: str) -> tuple:
        if ':' in target:
            host, port = target.rsplit(':', 1)
            return host, int(port)
        return target, 587