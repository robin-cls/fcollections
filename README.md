# Files Collections

[![Linting](https://github.com/robin-cls/fcollections/actions/workflows/pre-commit.yaml/badge.svg)](https://github.com/robin-cls/fcollections/actions/workflows/pre-commit.yaml)
[![Tests](https://github.com/robin-cls/fcollections/actions/workflows/tests.yaml/badge.svg)](https://github.com/robin-cls/fcollections/actions/workflows/tests.yaml)
[![Documentation](https://github.com/robin-cls/fcollections/actions/workflows/doc.yaml/badge.svg)](https://github.com/robin-cls/fcollections/actions/workflows/doc.yaml)
![License](https://img.shields.io/github/license/robin-cls/fcollections)


Select and read a collection of files

- Information contained in files and folders names are used to create basic
  selection filters
- Both local and remote file systems (FTP, S3, ...) can be explored
- Multiple implementations for handling different products and their specificities
- Easy building of an implementation for a new product


## Quick start

```bash
conda install files_collections
```

```python
from fcollections.implementations import NetcdfFilesDatabaseSwotLRL3
fc = NetcdfFilesDatabaseSwotLRL3("data")
fc.query(cycle_number=1, pass_number=1)
```

## Documentation

📘 **Full documentation:**
https://robin-cls.github.io/fcollections/index.html#

Key pages:
- [Getting started](https://robin-cls.github.io/fcollections/getting_started.html)
- [Installation](https://robin-cls.github.io/fcollections/install.html)
- [Catalog](https://robin-cls.github.io/fcollections/implementations/catalog.html)
- [Changelog](https://robin-cls.github.io/fcollections/changelog.html)

## Project status

⚠️ This project is still subject to breaking changes. Versioning will reflects
the breaking changes using SemVer convention

## License

Apache 2.0 — see [LICENSE](LICENSE)
