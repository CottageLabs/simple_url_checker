import setuptools
from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()


setup(
    name="simple-url-checker",
    version="0.0.1",
    author="philipwho",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(exclude=[]),
    scripts=[
        'simple_url_checker/url_checker.py',
    ],
    install_requires=[
        'selenium~=4.7.0',
        'selenium-wire~=5.1.0',
        'requests',
    ],
)
