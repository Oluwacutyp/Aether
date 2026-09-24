"""
Aether MongoDB Plugin
Full implementation with SCRAM authentication.
"""

import asyncio
from typing import Optional, Dict, Any

from ...core.plugin_interface import ProtocolPlugin, LoginResult, AuthResult, SessionData


class MongoDBPlugin(ProtocolPlugin):
    """MongoDB authentication plugin."""
    
    name = "mongodb"
    version = "2.0.0"
    protocols = ["mongodb", "mongodb+srv"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.database = config.get("database", "admin") if config else "admin"
        self.auth_source = config.get("auth_source", "admin") if config else "admin"
        
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        """
        MongoDB SCRAM authentication.
        """
        import asyncio
        start_time = asyncio.get_event_loop().time()
        
        target = session or self.config.get("target", "localhost:27017")
        
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            
            # Build connection string
            if "://" in target:
                # Full URI provided
                uri = target.replace("://", f"://{username}:{password}@")
            else:
                # Host:port format
                uri = f"mongodb://{username}:{password}@{target}/{self.database}?authSource={self.auth_source}"
            
            client = AsyncIOMotorClient(
                uri,
                serverSelectionTimeoutMS=self.timeout * 1000
            )
            
            # Test connection
            await client.admin.command('ping')
            
            # Get server info
            build_info = await client.admin.command('buildInfo')
            version = build_info.get("version", "unknown")
            
            client.close()
            
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return LoginResult(
                result=AuthResult.SUCCESS,
                username=username,
                password=password,
                response_time_ms=elapsed,
                message=f"MongoDB {version}"
            )
            
        except Exception as e:
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            error_msg = str(e).lower()
            
            if "authentication failed" in error_msg or \
               "auth failed" in error_msg or \
               "invalid credentials" in error_msg:
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