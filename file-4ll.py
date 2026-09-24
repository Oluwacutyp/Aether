from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import ProtocolPlugin, LoginResult, AuthResult


class MySQLPlugin(ProtocolPlugin):
    name = "mysql"
    version = "2.0.0"
    
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        target = session or "localhost:3306"
        host, port = self._parse_target(target)
        
        start = asyncio.get_event_loop().time()
        
        try:
            import aiomysql
            
            conn = await asyncio.wait_for(
                aiomysql.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password
                ),
                timeout=self.timeout
            )
            
            elapsed = (asyncio.get_event_loop().time() - start) * 1000
            
            async with conn.cursor() as cur:
                await cur.execute("SELECT VERSION()")
                version = await cur.fetchone()
            
            conn.close()
            
            return LoginResult(
                result=AuthResult.SUCCESS,
                username=username,
                password=password,
                response_time_ms=elapsed,
                message=f"MySQL {version[0] if version else 'unknown'}"
            )
            
        except aiomysql.OperationalError as e:
            elapsed = (asyncio.get_event_loop().time() - start) * 1000
            if "Access denied" in str(e):
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
        return target, 3306