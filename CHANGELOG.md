# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

## [0.2.0]

### Changed

- Updated to flattened `qcio v0.3.0` data models.
- Changed order of args to `compute()` to allow for the same pattern to `compute_args`.

## [0.1.0]

### Added

- Core compute capabilities exposed in top-level `compute()` function, including `QCEngine` fallback for programs without a `qcop` adapter.
- Created adapter for TeraChem.
- Exposed general purpose computing for any subprocess with `FileAdaptor`

[unreleased]: https://github.com/coltonbh/qcop/compare/0.2.0...HEAD
[0.2.0]: https://github.com/coltonbh/qcop/releases/tag/0.2.0
[0.1.0]: https://github.com/coltonbh/qcop/releases/tag/0.1.0