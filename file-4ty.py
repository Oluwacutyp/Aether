import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class ProxyConfig:
    enabled: bool = False
    provider: str = "rotating"
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    rotation_interval: int = 300
    sticky_sessions: bool = True


@dataclass
class AttackConfig:
    mode: str = "credential_stuffing"
    threads: int = 10
    delay_min: float = 0.5
    delay_max: float = 2.0
    jitter: float = 0.3


@dataclass
class AetherConfig:
    version: str = "1.0.0"
    debug: bool = False
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    attack: AttackConfig = field(default_factory=AttackConfig)
    
    @classmethod
    def from_yaml(cls, path: str) -> "AetherConfig":
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})