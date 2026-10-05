# Releasing the Python package

The Python package in this repository is published to PyPI as:

`ahmad-yar-gpt-tools`

Publishing uses PyPI Trusted Publishing through GitHub Actions. No long-lived PyPI API token should be stored in this repository.

## Trusted Publisher identity

The PyPI Trusted Publisher must match these values exactly:

| Setting | Value |
| --- | --- |
| Owner | `ahamdjin` |
| Repository | `ahmad-yar-automation-lab` |
| Workflow filename | `publish-pypi.yml` |
| Environment | `pypi` |

The publishing workflow is:

`.github/workflows/publish-pypi.yml`

## Release process

1. Update the version in both:
   - `pyproject.toml`
   - `python/gpt_tools/__init__.py`
2. Update documentation/tests when behavior changes.
3. Open a pull request and wait for the normal repository validation workflow to pass.
4. Merge the release change into `main`.
5. Create a GitHub Release from the exact `main` commit.
6. Use a tag matching the package version with a leading `v`. Example:
   - package version: `0.3.0`
   - release tag: `v0.3.0`
7. Publish the GitHub Release.

Publishing the GitHub Release triggers the PyPI workflow.

## What the release workflow verifies

Before PyPI receives anything, GitHub Actions:

- confirms the release tag matches `pyproject.toml`;
- confirms `gpt_tools.__version__` matches the project version;
- compiles the Python source;
- runs the complete Python test suite;
- builds both a wheel and source distribution;
- runs `twine check` on the built artifacts;
- installs the wheel into a clean virtual environment;
- smoke-tests installed CLI entry points.

Only after those checks pass does the publish job request a short-lived OIDC credential and upload the distributions to PyPI.

## GitHub environment

The publish job uses the GitHub environment named `pypi`.

For a public package, adding required-reviewer protection to that environment is a useful extra release safeguard when the repository/account supports it.

## Versioning rule

PyPI release files are immutable in normal release workflows. Treat every published version as permanent: fix mistakes by publishing a new version rather than trying to overwrite an existing one.

## Project links

The package metadata deliberately exposes:

- Homepage → https://www.ahmadyar.co/
- Source → GitHub repository
- Issues → GitHub issues
- Documentation → the Python toolkit documentation
- Changelog → GitHub Releases

This keeps the portfolio attribution useful and contextual for people who actually discover the package through PyPI.
