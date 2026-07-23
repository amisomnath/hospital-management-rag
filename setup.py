"""Editable-install metadata for the educational project."""

from setuptools import find_packages, setup

setup(
    name="hospital-rag-fastapi",
    version="1.0.0",
    description="Hospital management API with a medical-only RAG chatbot",
    packages=find_packages(),
    python_requires=">=3.11",
)
