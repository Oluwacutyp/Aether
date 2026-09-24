from setuptools import setup, find_packages

setup(
    name="aether",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "httpx[http2]>=0.25.0",
        "aiohttp>=3.9.0",
        "asyncssh>=2.14.0",
        "aiomysql>=0.2.0",
        "aiosqlite>=0.19.0",
        "pyyaml>=6.0.1",
        "beautifulsoup4>=4.12.0",
        "rich>=13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "aether=aether.cli:main",
        ],
    },
)