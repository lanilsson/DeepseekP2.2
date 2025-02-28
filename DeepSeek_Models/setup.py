#!/usr/bin/env python3
"""
Setup script for DeepSeek_Models package
"""

from setuptools import setup, find_packages

setup(
    name="DeepSeek_Models",
    version="0.1.0",
    description="DeepSeek-R1-Distill-Qwen-32B Model Launcher",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="DeepSeek AI",
    author_email="info@deepseek.ai",
    url="https://github.com/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    packages=find_packages(),
    install_requires=[
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "accelerate>=0.20.0",
        "sentencepiece>=0.1.99",
        "protobuf>=3.20.0",
        "bitsandbytes>=0.41.0",
        "safetensors>=0.3.1",
        "psutil>=5.9.0"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "deepseek-model=DeepSeek_Models.cli:main",
        ],
    },
)