---
kernelspec:
  language: python
  name: python3
jupytext:
  text_representation:
    extension: .md
    format_name: myst
---
# Getting started

``fcollections`` is a library that aims at reading a collections of files. Its
primary goal is to combine the selection, reading and concatenation of files
within a common model: ``FilesDatabase``.

Let's set up a minimal case with stub data for the SWOT altimetry mission.

```{code-cell}

import tempfile
import numpy as np
import xarray as xr
import fsspec.implementations.local as fs_loc

# Create stub data
path = tempfile.mkdtemp()
ds = xr.Dataset(data_vars={
    "ssha": (('num_lines', 'num_pixels'), np.random.random((9860, 69))),
    "swh": (('num_lines', 'num_pixels'), np.random.random((9860, 69))),})
ds.to_netcdf(f'{path}/SWOT_L2_LR_SSH_Expert_001_011_20240101T000000_20240101T030000_PGC0_01.nc')
ds.to_netcdf(f'{path}/SWOT_L2_LR_SSH_Expert_001_012_20240101T030000_20240101T060000_PGC0_01.nc')
```

## Implementations

The generic ``FilesDatabase`` model must be subclassed in order to properly
define the file listing and reading functionalities. A subclass handling a given
type of files is called an implementation.

When confronted to a files collection, the first step is to try and find if
an implementation matching the data already exists. Such implementation may be
found in the [catalog](implementations/catalog)

From the catalog, we can see that {class}`fcollections.implementations.NetcdfFilesDatabaseSwotLRL2`
matches our file names. In case no implementation is available, the user can
build its own following [creation procedure](custom).

## Listing files

An implementation can be used by simply giving the path to the data. An
important endpoint for the implementation is the ability to list files matching
given criterias

```{code-cell}
from fcollections.implementations import NetcdfFilesDatabaseSwotLRL2
fc = NetcdfFilesDatabaseSwotLRL2(path)
fc.list_files(cycle_number=1)
```

Listing files using filters is the first step toward subsetting the files set.


## Query data

Another important endpoint is the ability to read the file contents using the
``query`` method.


```{code-cell}
fc.query()
```

The method returns a {class}`xarray.Dataset` containing the combined data for
all files matching the regex specified by the implementation.

It is possible to load only a subset of the data by applying filters in the
query. For example, giving the ``cycle_number`` and ``pass_number`` argument
will select one half orbit of our altimetry mission.

```{code-cell}
fc.query(cycle_number=1, pass_number=11)
```

Variable selection is also available to return only part of the data

```{code-cell}
ds = fc.query(selected_variables=['ssha'])
list(ds.variables)
```

Each implementation has its own filters that can be displayed with the ``query``
method help or in the {doc}`../api` documentation of the implementation.

```{code-cell}
:tags: [hide-output]
fc.query?
```

## Access metadata

The database can display information about the variables and attributes
contained in the files' collection using the ``variables_info`` method

```{code-cell}
fc.variables_info(subset='Expert')
```

It will offer a simple collapsible tree view with multiple levels of nesting
depending on the data you manipulate

In order to return consistent metadata, the method ensures that only one
homogeneous subset is selected. In case you handle unmixable data (for example
Expert and Unsmoothed datasets), you must give proper filters on the subset
partitioning keys ``fc.unmixer.partition_keys``. If these filters are missing,
an error with the possible choices will be raised.

```{code-cell}
:tags: [raises-exception]
# Create Unsmoothed file, this will mix Expert and Unsmoothed dataset
ds.to_netcdf(f'{path}/SWOT_L2_LR_SSH_Unsmoothed_001_012_20240101T030000_20240101T060000_PGC0_01.nc')

# This will not work because we don't know if we need to display Expert or
# Unsmoothed metadata
fc.variables_info()
```

```{code-cell}
# Use the enumeration name for filtering
fc.variables_info(subset='Expert')
```

## Remote file systems

It is possible to access a file set from a remote location. Fcollections is based on
the powerful ``fsspec`` abstraction. As a consequence, files collections might
accept any file system, provided that the underlying reader supports it.

```{warning}
In case the reader does not support a specific file system, an error will be
triggered. The solution is to implement its own reader following
{doc}`custom`
```

The following code shows how to access data directly from the AVISO public FTP
server using both FTP and SFTP protocols. You will need credentials to
authentify (see the [aviso website](https://www.aviso.altimetry.fr/))

::::{tab-set}
:::{tab-item} FTP
```python
from fsspec.implementations.ftp import FTPFileSystem
fs = FTPFileSystem('ftp-access.aviso.altimetry.fr', 21, username='...', password='...')
db = NetcdfFilesDatabaseSwotLRL2('/swot_products/l2_karin/l2_lr_ssh/PIC2/Expert/cycle_031', fs=fs)
ds = db.list_files(pass_number=1)
```
:::
:::{tab-item} SFTP
```python
from fsspec.implementations.sftp import SFTPFileSystem
fs = SFTPFileSystem(host='ftp-access.aviso.altimetry.fr', port=2221, username='...', password='...')
db = NetcdfFilesDatabaseSwotLRL2('/swot_products/l2_karin/l2_lr_ssh/PIC2/Expert/cycle_031', fs=fs)
ds = db.list_files(pass_number=1)
```
```{note}
[paramiko](https://www.paramiko.org/) must be installed to use the SFTP
implementation of ``fsspec``
:::
::::

(layout_intro)=

## Partial file listing

A files collection is usually stored on a file system storage at a root path,
with nested folders for organizing the data. By default, all subfolders are
scanned to build the files metadata table. However, in case filters for listing
or querying the database are defined, only a subset of the subfolders are
relevant: a global scan is then inefficient.

In order to finely select the subfolders to explore, a
{class}`fcollections.core.Layout` object can be given to the
{class}`fcollections.core.FilesDatabase`. This object gives information about how
the file collection is organized and speeds up the requests.

```{note}
Pre-configured layouts are associated to the implementations. They can be found
in the {doc}`summary table <implementations/catalog>`
```

Below is an example of how a layout shall be configured. The given query filters
match the ``<version>/<subset>/<cycle_number>`` structure declared in the layout

```python
from fsspec.implementations.ftp import FTPFileSystem
from fcollections.implementations import AVISO_L2_LR_SSH_LAYOUT
fs = FTPFileSystem('ftp-access.aviso.altimetry.fr', 21, username='...', password='...')

# Use the layout parameter to give the file system tree information
db = NetcdfFilesDatabaseSwotLRL2('/swot_products/l2_karin/l2_lr_ssh', fs=fs,
                                 layout=AVISO_L2_LR_SSH_LAYOUT)

# Queries will now be faster
db.list_files(cycle_number=31, subset='Expert', pass_number=1)
```

In case the layout object mismatches the actual structure of the file
collection, the requests will return empty results and a warning will be emitted

```{code-cell}
# Display warning as a message log in stdout. Can be skipped
import sys;import logging; logging.basicConfig(stream=sys.stdout)
logging.captureWarnings(True)

# Recreate a invalid tree structure
import os
path = tempfile.mkdtemp()
os.mkdir(os.path.join(path, 'cycle_001'))

# Querying with a badly matched layout will return empty results
from fcollections.implementations import AVISO_L2_LR_SSH_LAYOUT
db = NetcdfFilesDatabaseSwotLRL2(path, layout=AVISO_L2_LR_SSH_LAYOUT)
ds = db.query(cycle_number=31, subset='Expert', pass_number=1)

ds is None
```

The user has two options to solve this issue:

- Remove the layout from it database instance, though the requests will fall
  back to a default a global scan
- Create the layout object matching the file collection structure, see
  {ref}`layout` for how to build a layout
