# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Improved conflict detection algorithm to correctly identify overlapping changes
- Fixed auto_merge function to properly handle non-conflicting changes and relationships
- Enhanced conflict file resolution with better validation and error handling
- Added version comparison and hash methods to Version class
- Improved Document class versioning methods for better consistency
- Fixed create_version method to respect update_document parameter
- Added compare_versions method to Document class for comparing arbitrary versions

## [0.2.0] - 2024-03-02

### Added
- Support for collection ID types including URI, UUID, CID, and string
- Enhanced relationship support with better validation
- Added document versioning features
- Improved conflict resolution system

### Changed
- Refactored Document class for better user experience
- MDPFile.write_mdp now returns an MDPFile object instead of a Path

### Fixed
- Various bug fixes and improvements to IPFS integration
- Fixed relationship metadata handling

## [0.1.0] - 2024-01-15

### Added
- Initial release with core functionality
- Basic document structure and metadata
- Simple relationship model
- CLI interface

### Added
- IPFS integration for document relationships
- Support for IPFS CIDs in metadata
- IPFS URI validation and parsing
- 'relationships' property to Document class for easier access
- Support for 'id' parameter in relationship functions as an alternative to 'reference'/'target'

### Fixed
- Validation for IPFS URIs in relationship fields
- Improved error handling for relationship creation 