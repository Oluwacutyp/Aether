"""
Aether LDAP Plugin
Full implementation with BIND authentication.
"""

import asyncio
from typing import Optional, Dict, Any

from ...core.plugin_interface import ProtocolPlugin, LoginResult, AuthResult, SessionData


class LDAPPlugin(ProtocolPlugin):
    """LDAP/LDAPS authentication plugin."""
    
    name = "ldap"
    version = "2.0.0"
    protocols = ["ldap", "ldaps"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_dn = config.get("base_dn", "") if config else ""
        self.use_ssl = config.get("ssl", False) if config else False
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        """
        LDAP BIND authentication.
        """
        import asyncio
        start_time = asyncio.get_event_loop().time()
        
        target = session or self.config.get("target", "localhost:389")
        host, port = self._parse_target(target)
        
        try:
            from ldap3 import Server, Connection, ALL, AUTO_BIND_NO_TLS
            
            # Build user DN if not provided
            if "=" in username:
                user_dn = username
            else:
                user_dn = f"uid={username},{self.base_dn}" if self.base_dn else username
            
            server = Server(host, port=port, get_info=ALL)
            
            conn = Connection(
                server,
                user=user_dn,
                password=password,
                auto_bind=AUTO_BIND_NO_TLS,
                read_only=True
            )
            
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # If we get here, bind was successful
            server_info = conn.server.info
            version = str(server_info)[:100] if server_info else "unknown"
            
            conn.unbind()
            
            return LoginResult(
                result=AuthResult.SUCCESS,
                username=username,
                password=password,
                response_time_ms=elapsed,
                message=f"LDAP BIND successful: {version}"
            )
            
        except Exception as e:
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            error_msg = str(e).lower()
            
            if "invalidcredentials" in error_msg or \
               "invalid credentials" in error_msg or \
               "49" in error_msg:
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
        if '://' in target:
            # ldap://host:port format
            target = target.split('://', 1)[1]
        if ':' in target:
            host, port = target.rsplit(':', 1)
            return host, int(port)
        return target, 636 if self.use_ssl else 389