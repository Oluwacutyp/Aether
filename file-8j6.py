"""
Aether SMB Plugin
Full implementation with NTLM authentication.
"""

import asyncio
from typing import Optional, Dict, Any

from ...core.plugin_interface import ProtocolPlugin, LoginResult, AuthResult, SessionData


class SMBPlugin(ProtocolPlugin):
    """SMB/CIFS authentication plugin."""
    
    name = "smb"
    version = "2.0.0"
    protocols = ["smb", "cifs", "smb2", "smb3"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.share = config.get("share", "IPC$") if config else "IPC$"
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        """
        SMB authentication.
        """
        import asyncio
        start_time = asyncio.get_event_loop().time()
        
        target = session or self.config.get("target", "localhost:445")
        host, port = self._parse_target(target)
        
        try:
            from smbprotocol.connection import Connection
            from smbprotocol.session import Session
            
            # Create connection
            conn = Connection(uuid.uuid4(), host, port)
            await asyncio.get_event_loop().run_in_executor(None, conn.connect)
            
            # Create session
            smb_session = Session(conn, username, password)
            await asyncio.get_event_loop().run_in_executor(None, smb_session.connect)
            
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # Disconnect
            await asyncio.get_event_loop().run_in_executor(None, conn.disconnect)
            
            return LoginResult(
                result=AuthResult.SUCCESS,
                username=username,
                password=password,
                response_time_ms=elapsed,
                message="SMB authentication successful"
            )
            
        except Exception as e:
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            error_msg = str(e).lower()
            
            if "logon failure" in error_msg or \
               "bad username" in error_msg or \
               "bad password" in error_msg:
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
        return target, 445