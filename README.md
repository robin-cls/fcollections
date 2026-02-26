# Files Collections

[![Linting](https://cnes.github.io/fcollections/actions/workflows/pre-commit.yaml/badge.svg)](https://cnes.github.io/fcollections/actions/workflows/pre-commit.yaml)
[![Tests](https://cnes.github.io/fcollections/actions/workflows/tests.yaml/badge.svg)](https://cnes.github.io/fcollections/actions/workflows/tests.yaml)
[![Documentation](https://cnes.github.io/fcollections/actions/workflows/doc.yaml/badge.svg)](https://cnes.github.io/fcollections/actions/workflows/doc.yaml)
![License](https://img.shields.io/github/license/cnes/fcollections)


Select and read a collection of files

- Information contained in files and folders names are used to create basic
  selection filters
- Both local and remote file systems (FTP, S3, ...) can be explored
- Multiple implementations for handling different products and their specificities
- Easy building of an implementation for a new product


## Installation

```bash
conda install files_collections -c conda-forge
```

## Use

```python
from fcollections.implementations import NetcdfFilesDatabaseSwotLRL3

fc = NetcdfFilesDatabaseSwotLRL3("data_dir")
ds = fc.query(subset='Basic', cycle_number=1, pass_number=1)

print(ds.sizes)
```

Output:

```text
Frozen({'num_lines': 9860, 'num_pixels': 69})
```

```python
print(list(ds.data_vars))
```

Output:

```text
['mdt', 'ssha_filtered', 'ssha_unfiltered', 'cycle_number', 'pass_number']
```

## Documentation

📘 **Full documentation:**
https://cnes.github.io/fcollections/index.html

Key pages:
- [Getting started](https://cnes.github.io/fcollections/getting_started.html)
- [Installation](https://cnes.github.io/fcollections/install.html)
- [Catalog](https://cnes.github.io/fcollections/implementations/catalog.html)
- [Changelog](https://cnes.github.io/fcollections/changelog.html)

## Project status

⚠️ This project is still subject to breaking changes. Versioning will reflects
the breaking changes using SemVer convention

## License

Apache 2.0 — see [LICENSE](LICENSE)
