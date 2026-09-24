import hashlib
import asyncio
from typing import Optional, Dict, Any, List


class HashCracker:
    ALGORITHMS = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256,
        'sha512': hashlib.sha512,
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.wordlist = config.get("wordlist", "wordlist.txt")
        
    async def crack(self, hash_value: str, algorithm: str) -> Optional[str]:
        if algorithm not in self.ALGORITHMS:
            return None
        
        hash_func = self.ALGORITHMS[algorithm]
        
        try:
            with open(self.wordlist, 'r', encoding='utf-8', errors='ignore') as f:
                for word in f:
                    word = word.strip()
                    if hash_func(word.encode()).hexdigest() == hash_value.lower():
                        return word
        except FileNotFoundError:
            pass
        
        return None
    
    async def crack_file(self, hash_file: str, algorithm: str) -> Dict[str, Optional[str]]:
        results = {}
        
        with open(hash_file) as f:
            hashes = [l.strip() for l in f if l.strip()]
        
        for h in hashes:
            results[h] = await self.crack(h, algorithm)
            if results[h]:
                print(f"[+] CRACKED: {h} = {results[h]}")
        
        return results