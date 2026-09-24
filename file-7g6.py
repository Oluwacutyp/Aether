import random
from typing import Optional, List, Dict, Any


class ProxyRotator:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.proxies: List[str] = []
        self.current_index = 0
        
        proxy_file = config.get("proxy_file") if config else None
        if proxy_file:
            with open(proxy_file) as f:
                self.proxies = [l.strip() for l in f if l.strip()]
    
    def get_proxy(self) -> Optional[str]:
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    def get_random(self) -> Optional[str]:
        if not self.proxies:
            return None
        return random.choice(self.proxies)