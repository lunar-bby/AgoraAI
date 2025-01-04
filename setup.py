from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agoraai",
    version="0.1.0",
    author="AgoraAI Team",
    author_email="contact@agoraai.org",
    description="A framework for creating decentralized AI agent marketplaces",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AgoraAI/agoraai",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "cryptography>=3.4.7",
        "pyjwt>=2.1.0",
        "pyyaml>=5.4.1",
        "aiohttp>=3.8.0",
        "dataclasses-json>=0.5.7",
        "typing-extensions>=4.0.0",
        "pydantic>=1.8.2",
        "websockets>=10.0"
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.5",
            "pytest-asyncio>=0.16.0",
            "pytest-cov>=2.12.1",
            "black>=21.9b0",
            "isort>=5.9.3",
            "mypy>=0.910",
            "flake8>=3.9.2",
        ],
        "docs": [
            "sphinx>=4.2.0",
            "sphinx-rtd-theme>=1.0.0",
            "sphinx-autodoc-typehints>=1.12.0",
        ],
    }
)