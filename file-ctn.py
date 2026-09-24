from typing import Optional, Dict, Any
import asyncio

from ...core.plugin_interface import ProtocolPlugin, LoginResult, AuthResult


class SSHPlugin(ProtocolPlugin):
    name = "ssh"
    version = "2.0.0"
    
    async def login(self, username: str, password: str,
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        import asyncssh
        import asyncio
        
        target = session or "localhost:22"
        host, port = self._parse_target(target)
        
        start = asyncio.get_event_loop().time()
        
        try:
            conn = await asyncio.wait_for(
                asyncssh.connect(
                    host,
                    port,
                    username=username,
                    password=password,
                    known_hosts=None
                ),
                timeout=self.timeout
            )
            
            elapsed = (asyncio.get_event_loop().time() - start) * 1000
            
            # Verify shell access
            result = await conn.run('echo success', check=True)
            verified = result.stdout.strip() == 'success'
            
            await conn.close()
            
            return LoginResult(
                result=AuthResult.SUCCESS,
                username=username,
                password=password,
                response_time_ms=elapsed,
                message=f"SSH access verified: {verified}"
            )
            
        except asyncssh.PermissionDenied:
            elapsed = (asyncio.get_event_loop().time() - start) * 1000
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
    
    def _parse_target(self, target: str):
        if ':' in target:
            host, port = target.rsplit(':', 1)
            return host, int(port)
        return target, 22