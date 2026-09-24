"""
Aether Redis Plugin
Full implementation with AUTH support.
"""

import asyncio
from typing import Optional, Dict, Any

from ...core.plugin_interface import ProtocolPlugin, LoginResult, AuthResult, SessionData


class RedisPlugin(ProtocolPlugin):
    """Redis authentication plugin."""
    
    name = "redis"
    version = "2.0.0"
    protocols = ["redis", "rediss"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.ssl = config.get("ssl", False) if config else False
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        """
        Redis AUTH authentication.
        Note: Redis 6+ supports username:password, older versions just password.
        """
        import asyncio
        start_time = asyncio.get_event_loop().time()
        
        target = session or self.config.get("target", "localhost:6379")
        host, port = self._parse_target(target)
        
        try:
            import aioredis
            
            # Redis 6+ with username
            if username and username != "default":
                redis_url = f"redis://{username}:{password}@{host}:{port}"
            else:
                redis_url = f"redis://:{password}@{host}:{port}"
            
            if self.ssl:
                redis_url = redis_url.replace("redis://", "rediss://")
            
            client = aioredis.from_url(
                redis_url,
                socket_connect_timeout=self.timeout,
                socket_keepalive=True
            )
            
            # Test connection
            await client.ping()
            
            # Get info
            info = await client.info("server")
            version = info.get("redis_version", "unknown")
            
            await client.close()
            
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return LoginResult(
                result=AuthResult.SUCCESS,
                username=username,
                password=password,
                response_time_ms=elapsed,
                message=f"Redis {version}"
            )
            
        except aioredis.AuthenticationError:
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            return LoginResult(
                result=AuthResult.FAILURE,
                username=username,
                password=password,
                response_time_ms=elapsed
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
        return target, 6379