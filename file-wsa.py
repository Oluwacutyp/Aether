"""
Aether PostgreSQL Plugin
Full implementation with asyncpg.
"""

import asyncio
from typing import Optional, Dict, Any

from ...core.plugin_interface import ProtocolPlugin, LoginResult, AuthResult, SessionData


class PostgreSQLPlugin(ProtocolPlugin):
    """PostgreSQL authentication plugin."""
    
    name = "postgresql"
    version = "2.0.0"
    protocols = ["postgresql", "postgres"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.ssl = config.get("ssl", False) if config else False
        self.database = config.get("database", "postgres") if config else "postgres"
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        """
        PostgreSQL authentication.
        """
        import asyncio
        start_time = asyncio.get_event_loop().time()
        
        target = session or self.config.get("target", "localhost:5432")
        host, port = self._parse_target(target)
        
        try:
            import asyncpg
            
            conn = await asyncio.wait_for(
                asyncpg.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    database=self.database,
                    ssl=self.ssl
                ),
                timeout=self.timeout
            )
            
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # Get server version
            version = await conn.fetchval("SELECT version()")
            
            await conn.close()
            
            return LoginResult(
                result=AuthResult.SUCCESS,
                username=username,
                password=password,
                response_time_ms=elapsed,
                message=f"PostgreSQL {version[:50]}"
            )
            
        except asyncpg.InvalidPasswordError:
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            return LoginResult(
                result=AuthResult.FAILURE,
                username=username,
                password=password,
                response_time_ms=elapsed
            )
            
        except asyncpg.InvalidAuthorizationSpecificationError:
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            return LoginResult(
                result=AuthResult.FAILURE,
                username=username,
                password=password,
                response_time_ms=elapsed,
                message="User does not exist or database access denied"
            )
            
        except Exception as e:
            return LoginResult(
                result=AuthResult.ERROR,
                username=username,
                password=password,
                message=str(e)
            )
    
    def _parse_target(self, target: str) -> tuple:
        if ':' in target:
            host, port = target.rsplit(':', 1)
            return host, int(port)
        return target, 5432