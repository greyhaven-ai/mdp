# Installing and Setting Up MDP

This guide covers installing the MDP Python package and getting started with basic usage.

## Prerequisites

Before installing MDP, ensure you have:

- Python 3.8 or newer
- pip (Python package installer)

## Installation Methods

### Standard Installation

The simplest way to install MDP is via pip:

```bash
pip install mdp
```

### Development Installation

For development or to contribute to the MDP project, clone the repository and install in development mode:

```bash
git clone https://github.com/greyhaven-ai/mdp.git
cd mdp
pip install -e .
```

### Optional Dependencies

MDP has several optional dependencies for extended functionality:

```bash
# For HTML conversion
pip install mdp[html]

# For PDF conversion
pip install mdp[pdf]

# For IPFS integration
pip install mdp[ipfs]

# Install all optional dependencies
pip install mdp[all]
```

## Verifying Installation

To verify that MDP is installed correctly, run the following command:

```bash
python -c "import mdp; print(mdp.__version__)"
```

You should see the current version number of the MDP package.

## Setting Up Your Environment

### Environment Variables

MDP supports configuration through environment variables:

- `MDP_CONFIG_PATH`: Path to the configuration file
- `MDP_COLLECTIONS_PATH`: Default path for searching collections
- `MDP_IPFS_API_URL`: IPFS API endpoint for IPFS integration
- `MDP_IPFS_GATEWAY_URL`: IPFS gateway URL for web access

### Configuration File

Create a configuration file at `~/.mdp/config.yaml` to set global options:

```yaml
collections:
  path: ~/Documents/mdp/collections
  
ipfs:
  api_url: http://localhost:5001/api/v0
  gateway_url: https://ipfs.io/ipfs/
  
converters:
  html:
    default_template: ~/Templates/mdp.html
  pdf:
    engine: wkhtmltopdf
```

## Command Line Interface

MDP includes a command-line interface for working with MDP files. After installation, the `mdp` command will be available:

```bash
# Show help
mdp --help

# Create a new MDP document
mdp create "My Document"

# Convert an MDP document to HTML
mdp convert document.mdp --format html

# Validate an MDP document
mdp validate document.mdp

# List documents in a collection
mdp collection list my-collection
```

## Next Steps

After installation, you may want to:

1. [Create your first MDP document](../examples/getting_started.md)
2. [Learn about the Python API](./python_api.md)
3. [Explore document relationships](../examples/relationships.md)
4. [Work with collections](../examples/collections.md)

## Troubleshooting

### Common Issues

- **ImportError**: Ensure you have installed the correct optional dependencies
- **Permission Error**: Use `pip install --user mdp` if you don't have admin permissions
- **Version Conflict**: Try `pip install --upgrade mdp` to get the latest version

### Getting Help

If you encounter issues:

- Check the [GitHub issues](https://github.com/greyhaven-ai/mdp/issues)
- Join the [discussion forum](https://github.com/greyhaven-ai/mdp/discussions)
- Read the [full documentation](https://greyhaven-ai.github.io/mdp/) 