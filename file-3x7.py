"""
Aether Plugin Interface
Defines the contract all target plugins must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, List, Any, AsyncIterator, Callable
from datetime import datetime


class AuthResult(Enum):
    SUCCESS = auto()
    FAILURE = auto()
    LOCKOUT = auto()
    CAPTCHA = auto()
    MFA_REQUIRED = auto()
    RATE_LIMITED = auto()
    PROXY_BLOCKED = auto()
    CHALLENGE = auto()
    ERROR = auto()
    UNKNOWN = auto()


@dataclass
class SessionData:
    cookies: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    tokens: Dict[str, str] = field(default_factory=dict)
    user_agent: Optional[str] = None
    proxy_used: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cookies": self.cookies,
            "headers": self.headers,
            "tokens": self.tokens,
            "user_agent": self.user_agent,
            "proxy_used": self.proxy_used,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class LoginResult:
    result: AuthResult
    username: str
    password: str
    message: Optional[str] = None
    session: Optional[SessionData] = None
    response_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def is_success(self) -> bool:
        return self.result == AuthResult.SUCCESS
    
    def is_failure(self) -> bool:
        return self.result == AuthResult.FAILURE
    
    def is_blocked(self) -> bool:
        return self.result in (AuthResult.LOCKOUT, AuthResult.RATE_LIMITED, 
                               AuthResult.PROXY_BLOCKED, AuthResult.CHALLENGE)


@dataclass
class EnumerateResult:
    username: str
    exists: Optional[bool] = None
    confidence: float = 0.0
    indicators: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BasePlugin(ABC):
    name: str = "base"
    version: str = "1.0.0"
    protocols: List[str] = []
    attack_modes: List[str] = ["credential_stuffing", "brute_force", 
                               "password_spray", "enumeration"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._session_factory: Optional[Callable] = None
        self._proxy_manager: Optional[Any] = None
        
    def inject_dependencies(self, session_factory: Callable, 
                           proxy_manager: Optional[Any] = None):
        self._session_factory = session_factory
        self._proxy_manager = proxy_manager
    
    @abstractmethod
    async def login(self, username: str, password: str, 
                   session: Optional[Any] = None,
                   proxy: Optional[str] = None) -> LoginResult:
        pass
    
    async def enumerate(self, username: str,
                       session: Optional[Any] = None,
                       proxy: Optional[str] = None) -> EnumerateResult:
        return EnumerateResult(username=username, exists=None, confidence=0.0)
    
    def supports_enumeration(self) -> bool:
        return "enumeration" in self.attack_modes


class WebPlugin(BasePlugin):
    protocols = ["http", "https"]
    use_browser: bool = False
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url: Optional[str] = None


class ProtocolPlugin(BasePlugin):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.timeout: int = config.get("timeout", 30) if config else 30