---
title: "Contributing to MDP"
version: "1.0.0"
author: "MDP Team"
published_date: "2024-10-18"
status: "Active"
uuid: "7a9e5f2b-3c10-4e51-a567-0e02b2c3d480"
---

# Contributing to MDP

Thank you for your interest in contributing to the MDP (Markdown Data Pack) project! This guide will help you understand how to contribute effectively to both the specification and the implementation.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please read it before contributing:

- Be respectful and inclusive
- Focus on constructive feedback
- Maintain a collaborative environment
- Report unacceptable behavior to the project maintainers

## Ways to Contribute

There are many ways you can contribute to the MDP project:

1. **Specification Development**: Help refine the MDP specification
2. **Implementation Code**: Contribute to the reference implementations
3. **Documentation**: Improve guides, examples, and API references
4. **Testing**: Create test cases and report bugs
5. **Examples**: Add example use cases and implementations
6. **Tools Integration**: Build tools that work with MDP files
7. **Promotion**: Help spread the word about the MDP standard

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- A GitHub account

### Setting Up Your Development Environment

1. **Fork the repository**:
   - Visit [https://github.com/greyhaven-ai/mdp](https://github.com/greyhaven-ai/mdp)
   - Click the "Fork" button in the top-right corner

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/mdp.git
   cd mdp
   ```

3. **Set up the development environment**:
   ```bash
   # Create a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -e ".[dev]"
   
   # Install pre-commit hooks
   pre-commit install
   ```

## Development Workflow

### Branches

- `main`: Production-ready code
- `dev`: Development branch for upcoming releases
- Feature branches: Create from `dev` for new features

### Creating a Branch

```bash
git checkout dev
git pull origin dev
git checkout -b feature/your-feature-name
```

### Making Changes

1. Make your changes following our coding standards
2. Add tests for new functionality
3. Update documentation as needed
4. Run tests locally to verify your changes

```bash
# Run tests
pytest

# Run type checking
mypy mdp

# Run linting
flake8 mdp
```

### Committing Changes

Follow conventional commits for your commit messages:

```
type(scope): brief description

[optional body]

[optional footer]
```

Types include:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting changes
- `refactor`: Code restructuring
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

Example:
```
feat(parser): add support for custom collection types

Adds ability to define custom collection types in the metadata section.
Includes unit tests and documentation updates.

Resolves #123
```

### Creating a Pull Request

1. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Go to the [original repository](https://github.com/greyhaven-ai/mdp) and create a pull request
3. Fill out the pull request template with details about your changes
4. Link any relevant issues
5. Wait for the maintainers to review your PR

## Contributing to the Specification

When contributing to the MDP specification:

1. Clearly identify which part of the specification you're addressing
2. Provide rationale for proposed changes
3. Consider backward compatibility
4. Include examples showing the benefit of your proposal
5. Update any relevant schema files (JSON Schema, OpenAPI)

## Documentation Guidelines

- Use MDP format for all documentation files
- Include proper metadata in the YAML frontmatter
- Follow markdown best practices
- Include examples when explaining features
- Update the mkdocs.yml file if adding new pages

## Testing

- All new features should include tests
- Bug fixes should include tests that verify the fix
- Run the full test suite before submitting PRs
- Include both unit tests and integration tests when appropriate

## Release Process

1. Versioning follows [Semantic Versioning](https://semver.org/)
2. Changelog entries are required for all significant changes
3. Release notes are generated from the changelog
4. Documentation is updated with each release

## Getting Help

If you need help with contributing:

- Join our [GitHub Discussions](https://github.com/greyhaven-ai/mdp/discussions)
- Check existing issues and documentation
- Reach out to maintainers for guidance

## Acknowledgment

Contributors will be acknowledged in:

- The project's README
- Release notes
- Project documentation

Thank you for helping make MDP better! 