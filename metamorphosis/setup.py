from setuptools import setup, find_packages

setup(
    name="openenv-customer-support",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=1.10",
        "fastapi>=0.100",
        "uvicorn>=0.23",
        "openai>=1.3",
    ],
)
