"""
Aether MSSQL Plugin
Full implementation with aioodbc.
"""

import asyncio
from typing import Optional, Dict, Any

from ...core.plugin_interface import ProtocolPlugin, LoginResult, AuthResult, SessionData


class MSSQLPlugin(ProtocolPlugin):
    """Microsoft SQL Server authentication plugin."""
    
    name = "mssql"
    version = "2.0.0"
    protocols = ["mssql", "sqlserver"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.database = config.get("database", "master") if config else "master"
        self.driver = config.get("driver", "ODBC Driver 17 for SQL Server") if config else "ODBC Driver 17 for SQL Server"
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        """
        MSSQL authentication via ODBC.
        """
        import asyncio
        start_time = asyncio.get_event_loop().time()
        
        target = session or self.config.get("target", "localhost:1433")
        host, port = self._parse_target(target)
        
        try:
            import aioodbc
            
            dsn = (
                f"DRIVER={{{self.driver}}};"
                f"SERVER={host},{port};"
                f"DATABASE={self.database};"
                f"UID={username};"
                f"PWD={password};"
                f"TrustServerCertificate=yes;"
                f"Encrypt=no;"
            )
            
            conn = await aioodbc.connect(dsn=dsn, timeout=self.timeout)
            
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # Test with simple query
            cursor = await conn.cursor()
            await cursor.execute("SELECT @@VERSION")
            row = await cursor.fetchone()
            version = row[0] if row else "unknown"
            
            await cursor.close()
            await conn.close()
            
            return LoginResult(
                result=AuthResult.SUCCESS,
                username=username,
                password=password,
                response_time_ms=elapsed,
                message=f"MSSQL {version[:50]}"
            )
            
        except Exception as e:
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            error_msg = str(e).lower()
            
            if "login failed" in error_msg or "28000" in error_msg:
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
        return target, 1433