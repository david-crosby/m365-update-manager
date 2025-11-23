# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial implementation of M365 update manager with lagged deployment
- Support for 12 Microsoft 365 applications for macOS
- Three-tier deployment model (staged, live, previous)
- Azure Blob Storage integration for package hosting
- Configurable lag period to prevent premature deployments
- Automatic update checking via Microsoft AutoUpdate service
- Manifest-based state management
- Rollback capability for problematic updates
- Dry-run mode for testing
- Comprehensive test suite
- GitHub Actions workflows for CI/CD
- Pre-commit hooks for code quality

## [0.1.0] - TBC

### Added
- First release - draft for peer review
