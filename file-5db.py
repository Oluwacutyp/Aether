"""
Aether Setup
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="aether",
    version="1.0.0",
    author="Security Research",
    description="Universal Credential Attack Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aether-framework/aether",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.12",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "aether=aether.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "aether": ["phishing/templates/*.html", "config/*.yaml"],
    },
)