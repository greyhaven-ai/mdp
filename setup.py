"""
Setup script for the mdp package.
"""

from setuptools import setup, find_packages
import os

# Read the long description from README.md
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

# Get version from a VERSION file, or hardcode it if not available
if os.path.exists('VERSION'):
    with open('VERSION') as f:
        version = f.read().strip()
else:
    version = '0.1.0'  # Default version

# Define extra dependencies
extras_require = {
    # Development tools
    'dev': [
        'pytest>=7.0.0',
        'black>=22.0.0',
        'flake8>=5.0.0',
        'mypy>=1.0.0',
        'sphinx>=5.0.0',
    ],
    # LSP server dependencies
    'lsp': [
        'pygls>=1.0.0',
    ],
}

setup(
    name="mdp",
    version=version,
    author="MDP",
    author_email="contact@markdowndatapack.org",
    description="Markdown Data Package (MDP): A global standard file specification for document management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/greyhaven-ai/mdp",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pyyaml>=6.0",
        "markdown>=3.4.0",
        "python-frontmatter>=1.0.0",
        "python-dateutil>=2.8.2",
        "pytz>=2023.3",
        "requests>=2.28.0",
        "uuid>=1.30",
        "mcp>=1.3.0",  # Model Context Protocol SDK
    ],
    extras_require=extras_require,
    entry_points={
        'console_scripts': [
            'mdp=mdp.cli:main',
            'mdp-language-server=mdp:lsp_server',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Documentation",
        "Topic :: Software Development :: Documentation",
        "Topic :: Text Processing :: Markup :: Markdown",
    ],
    python_requires=">=3.8",
) 