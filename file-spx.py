from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import ProtocolPlugin, LoginResult, AuthResult


class PostgreSQLPlugin(ProtocolPlugin):
    name = "postgresql"
    version = "2.0.0"
    
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        target = session or "localhost:5432"
        host, port = self._parse_target(target)
        
        start = asyncio.get_event_loop().time()
        
        try:
            import asyncpg
            
            conn = await asyncio.wait_for(
                asyncpg.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    database="postgres"
                ),
                timeout=self.timeout
            )
            
            elapsed = (asyncio.get_event_loop().time() - start) * 1000
            
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            
            return LoginResult(
                result=AuthResult.SUCCESS,
                username=username,
                password=password,
                response_time_ms=elapsed,
                message=version
            )
            
        except asyncpg.PostgresError as e:
            elapsed = (asyncio.get_event_loop().time() - start) * 1000
            return LoginResult(
                result=AuthResult.FAILURE,
                username=username,
                password=password,
                response_time_ms=elapsed,
                message=str(e)
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
        return target, 5432