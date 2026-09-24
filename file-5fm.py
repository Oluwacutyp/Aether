"""
Aether WinRM Plugin
Full implementation with Basic and NTLM auth.
"""

import asyncio
from typing import Optional, Dict, Any

from ...core.plugin_interface import ProtocolPlugin, LoginResult, AuthResult, SessionData


class WinRMPlugin(ProtocolPlugin):
    """WinRM (Windows Remote Management) authentication plugin."""
    
    name = "winrm"
    version = "2.0.0"
    protocols = ["winrm", "wsman"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.transport = config.get("transport", "ntlm") if config else "ntlm"
        self.scheme = config.get("scheme", "http") if config else "http"
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        """
        WinRM authentication.
        """
        import asyncio
        start_time = asyncio.get_event_loop().time()
        
        target = session or self.config.get("target", "localhost:5985")
        host, port = self._parse_target(target)
        
        try:
            from pywinrm import Session
            
            endpoint = f"{self.scheme}://{host}:{port}/wsman"
            
            session = Session(
                endpoint,
                auth=(username, password),
                transport=self.transport,
                server_cert_validation='ignore'
            )
            
            # Test with simple command
            result = session.run_cmd('hostname')
            
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            
            if result.status_code == 0:
                return LoginResult(
                    result=AuthResult.SUCCESS,
                    username=username,
                    password=password,
                    response_time_ms=elapsed,
                    message=f"WinRM connected: {result.std_out.decode().strip()}"
                )
            
            return LoginResult(
                result=AuthResult.FAILURE,
                username=username,
                password=password,
                response_time_ms=elapsed,
                message=f"Command failed: {result.std_err.decode()}"
            )
            
        except Exception as e:
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            error_msg = str(e).lower()
            
            if "unauthorized" in error_msg or \
               "401" in error_msg or \
               "access is denied" in error_msg:
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
                message=str(e)
            )
    
    def _parse_target(self, target: str) -> tuple:
        if ':' in target:
            host, port = target.rsplit(':', 1)
            return host, int(port)
        return target, 5985