---
kernelspec:
  language: python
  name: python3
jupytext:
  text_representation:
    extension: .md
    format_name: myst
---
# Building an implementation

This chapter aims at giving details about the concepts supporting the generic
model ``FilesDatabase``. The ultimate purpose is to build a custom
implementation supporting any file set.


## File name convention

The central piece of the model is the definition of a file name convention.
Usually, file names contain a great deal of information that can be used for
selection. It may display periods for time series, geographical extent for tiles
and so on.

A file name convention has a dual purpose: interpreting a file name to deduce a
record of information, and conversely using a record of information to generate
a filename. Interpretation relies on a regex whereas generation uses an
f-string. Both functionalities also need ``FileNameField`` definitions to
specify the type of the data extracted from the file name, how to encode and
decode it, and which filters can be used onto it.

Let's take the SWOT altimery mission Low Rate product as an example:
``SWOT_L2_LR_SSH_Expert_001_010_20240101T000000_20240101T030000_PGC0_01.nc``

This file name contains the following information
    - ``L2_LR_SSH`` is the product (Level 2 Low Rate Sea Surface Height)
    - ``Expert`` is the products' subset (other subset are Basic, WindWave and Unsmoothed)
    - ``001`` is the cycle number
    - ``010`` is the pass number
    - ``20240101T000000`` is the timestamp for the first measurement
    - ``20240101T030000`` is the timestamp for the last measurement
    - ``PGC0_01`` is the version of the product

To represent this convention, we define a regex with explicit regex groups for
representing the fields. The groups names are important as they will be used to
automatically build an API (see the following sections).

```{code-cell}
import re
pattern = re.compile(
    r'SWOT_(?P<level>.*)_LR_SSH_(?P<subset>.*)_(?P<cycle_number>\d{3})_(?P<pass_number>\d{3})_'
    r'(?P<time>\d{8}T\d{6}_\d{8}T\d{6})_(?P<version>P[I|G][A-Z]\d{1}_\d{2}).nc'
)
```

[Online tools](https://regex101.com/) are useful to help building the regex for
non-critical use. In addition, inspiration can be found in the many existing
[implementations](implementations/catalog).

Once the regex is identified, the groups must be associated to fields by
subclassing ``FileNameField``. File name fields are used to declare which type
of data can be extracted from a file name, and how to decode and encode them.
The following example shows a field matching the ``cycle_number`` group declared
in the file name convention's regex

```{code-cell}
from fcollections.core import FileNameFieldInteger
field = FileNameFieldInteger('cycle_number')
field.type
```

```{code-cell}
field.decode('10')
```

```{code-cell}
field.encode(10)
```

In addition, file name fields provide a testing method that can compare two
objects strictly or loosely related to the field's type. The tested object must
be an instance of the type declared in the field, whereas the reference object
is dependent on the field implementation and can be more loosely related to the
field's type. For example, the integer field checks if an integer is in a list,
a range or equal to another integer.


```{code-cell}
field.test(10, 10)
```

```{code-cell}
field.test(10, 9)
```

```{code-cell}
field.test([9, 10, 11], 10)
```

```{code-cell}
field.test(slice(9, 11), 10)
```

The resulting convention is the composition of the regex, the fields and
optionally the generation f-string (not shown in this example).

```{code-cell}
from fcollections.core import FileNameConvention, FileNameFieldPeriod, FileNameFieldString
convention = FileNameConvention(
    regex=pattern,
    fields=[
        FileNameFieldInteger('cycle_number'),
        FileNameFieldInteger('pass_number'),
        FileNameFieldPeriod('time', '%Y%m%dT%H%M%S', '_',),
        FileNameFieldString('level'),
        FileNameFieldString('subset'),
        FileNameFieldString('version')])
```

## File listing and automatic filters

Once a file name convention is established, we can build a series of records
from a file set. Records contain decoded information from each file name and is
converted to a pandas DataFrame whose columns are named after the regex groups.

```{code-cell}
import fsspec.implementations.memory as fs_mem
from fcollections.core import FileDiscoverer, FileSystemIterable

fs = fs_mem.MemoryFileSystem()
fs.touch('/SWOT_L2_LR_SSH_Expert_001_010_20240101T000000_20240101T030000_PGC0_01.nc')
fs.touch('/SWOT_L2_LR_SSH_Expert_001_012_20240101T030000_20240101T030000_PGC0_01.nc')
fs.touch('/SWOT_L2_LR_SSH_Expert_002_010_20240102T000000_20240102T030000_PGC0_01.nc')

discoverer = FileDiscoverer(convention, iterable=FileSystemIterable(fs))
df = discoverer.list('/')
```

The discoverer looks for files in the given path, parses the file names and
returns the records. It is possible to set filters on the records to get a
subset of the files. The filters are automatically configured from the
convention's fields and are passed as keywords arguments. For example, we can
set filters to retrieve only one half orbit from our altimetry dataset.

```{code-cell}
df = discoverer.list('/', cycle_number=1, subset='Expert', pass_number=12)
```

In addition, the discoverer can add from the filesystem. The list of the desired
information can be passed to the ``stat_fields`` argument. Each value will be
shown as a column in the returned dataframe.

```{code-cell}
df = discoverer.list('/', stat_fields=['size', 'created'])
```

```{note}
Using ``fs.ls(..., detail=True)`` will give the available values for the
``stat_fields`` arguments
```

## Reading files

Reading files is the last element needed before building a functional API. Once
the desired files are listed, we can read and combine them using the ``Reader``
interface. A basic wrapper around ``xarray.open_mfdataset`` can be instanciated
in order to freeze the reading arguments. In most case, giving the engine and
the data combination method is sufficient.

In the following example, we show how to generate a simple reader to concatenate
stub data along the ``num_lines`` dimension.

```{code-cell}
import tempfile
import numpy as np
import xarray as xr
import fsspec.implementations.local as fs_loc
from fcollections.core import OpenMfDataset

# Create stub data
path = tempfile.mkdtemp()
ds = xr.DataArray(np.random.random((9860, 69)), dims=('num_lines', 'num_pixels')).to_dataset(name='ssha')
ds.to_netcdf(f'{path}/SWOT_L2_LR_SSH_Expert_001_011_20240101T000000_20240101T030000_PGC0_01.nc')
ds.to_netcdf(f'{path}/SWOT_L2_LR_SSH_Expert_001_012_20240101T030000_20240101T060000_PGC0_01.nc')
```

```{code-cell}
reader = OpenMfDataset({'engine': 'h5netcdf',
                               'concat_dim' :'num_lines',
                               'combine': 'nested'})

reader.read([
    f'{path}/SWOT_L2_LR_SSH_Expert_001_011_20240101T000000_20240101T030000_PGC0_01.nc',
    f'{path}/SWOT_L2_LR_SSH_Expert_001_012_20240101T030000_20240101T060000_PGC0_01.nc'])
```

## Query API

Combining all elements is done by subclassing ``FilesDatabase``. The subclass
must define class arguments for the file name convention and the reader. The
file listing method from the ``FileDiscoverer`` is integrated in the interface
and can be called from the new object to get the records.

```{code-cell}
from fcollections.core import FilesDatabase
class MyDatabase(FilesDatabase):
    parser = convention
    reader = reader

fc = MyDatabase(path)
fc.list_files()
```

Apart from listing files, the ``FilesDatabase`` exposes the ``query`` method.
This method mixes the previously introduced concepts of files' listing,
selection, reading and combination to produce a dataset. Like for the
``FileDiscoverer``, filters are automatically built from the file name
convention.

```{code-cell}
fc.query(pass_number=11)
```

The documentation for the available filters can be displayed with the ``query``
method help.

```{code-cell}
:tags: [hide-output]
fc.query?
```

## Handling duplicates and unmixable subsets

File sets often piles up multiple versions or subsets of the same data. In
addition, some duplicates may be found even within the same subsets. In this
particular case, filtering the files before reading them becomes a necessity
rather than a possibility.

To get a consistent dataset from the ``query`` method, a ``FilesDatabase``
subclass can define the following

* ``SubsetsUnmixer``: this class interprets the records of the files' metadata
  table to detect subset mixing. The ``partition_keys`` attribute serves as the
  subset definition. Using this partition keys, the unmixer can split the
  records table into multiple sub-tables containing homogeneous data. The
  ``auto_pick_last`` attribute is a list of keys that will help sorting and
  picking the subset. If the auto pick does not include all of the partition
  keys, it can prove insufficient so we expect manual filtering from the user.
  In case the manual inputs are missing when needed, an error will be raised to
  help the user properly configure the filters
* ``Deduplicator``: this class interprets the records of a files' metadata
  table to detect duplicates. The ``unique`` attribute serves as the unicity
  definition. The ``auto_pick_last`` attribute is a list of keys that will be
  sorted and deduplicated

The subset unmixing and picking is ran just after listing the files. The user is
encouraged to pick one subset with some filters applied to file listing. For
example, in the SWOT Low Rate products, the subset field should be set to either
``Basic``, ``Expert``, ``WindWave`` or ``Unsmoothed``. After one subset is
selected, the deduplication process is ran to remove files containing the same
data. In our case, multiple versions may pile up so the auto pick property will
choose the latest. Once the files' list is properly processed, it can be read to
form an homogeneous dataset for the user.

To illustrate how to use the ``SubsetsUnmixer`` and ``Deduplicator``, we can
modify our previous custom implementation

```{code-cell}
from fcollections.core import Deduplicator, SubsetsUnmixer

deduplicator = Deduplicator(
    # Altimetry granules are defined using cycle and pass numbers
    unique=('cycle_number', 'pass_number'),
    # Auto pick will automatically keep the latest version
    auto_pick_last=('version',))

subset_unmixer = SubsetsUnmixer(
    # We should not mix data part of a different subset Basic/Expert/
    # Unsmoothed/WindWave
    partition_keys=['subset'])

class MyDatabase(FilesDatabase):
    parser = convention
    reader = reader
    deduplicator = deduplicator
    unmixer = subset_unmixer

fc = MyDatabase(path)
```

```{code-cell}
# Create a duplicate
ds.to_netcdf(f'{path}/SWOT_L2_LR_SSH_Expert_001_011_20240101T000000_20240101T030000_PIC0_01.nc')
fc.list_files(deduplicate=False)
```

```{code-cell}
fc.list_files(deduplicate=True)
```

```{code-cell}
:tags: [raises-exception]
# In case there is also Unsmoothed products, 'subset' argument will become
# mandatory to filter out other subsets
ds.to_netcdf(f'{path}/SWOT_L2_LR_SSH_Unsmoothed_001_011_20240101T000000_20240101T030000_PIC0_01.nc')

# An error is expected if we enforce one subset only
fc.list_files(unmix=True)
```

```{code-cell}
fc.list_files(subset='Expert', unmix=True)
```

```{note}
In our example, we explicitely allowed versions mixing by setting the
``version`` field in the deduplicator. We could have chosen otherwise and
set this field in the subset unmixer instead, enforcing one version per
subset
```

## Mixins

A custom ``FilesDatabase`` may need additional functionalities apart from
listing and reading files. These functionalities are usually specific to the use
case or the data contained in the files. This lack of genericity justifies using
a multiple inheritance mecanism to inject them in the generic model. Because the
classes adding the functionalities are abstract, they should be mixed with other
classes to get a complete implementation: these abstract classes are then called
``mixins``.

Two mixins are currently available: ``PeriodMixin`` and ``DownloadMixin``. The
``PeriodMixin`` works with time series and can analyze the data to get the time
coverage or detect holes. The ``DownloadMixin`` appends a download endpoint to
a remote database.

To add a mixin in a custom implementation, the subclass should declare both the
mixin and the ``FilesDatabase`` generic class

```{code-cell}
from fcollections.core import PeriodMixin

class MyDatabase(FilesDatabase, PeriodMixin):
    parser = convention
    reader = reader

fc = MyDatabase(path)
fc.time_coverage()
```

(layout)=

## Layout

As stated in {ref}`layout_intro`, the {class}`fcollections.core.Layout` object
speeds up file listing. You might want to build a layout reflecting the file
collection structure to complement the custom implementation.

A layout is a list of {class}`fcollections.core.FileNameConvention` that
reflects the expected organization of subfolders. Let us consider the following
layout related to our running example

```
collection_root/
├── PIC2/
│   ├── Basic/
│   │   ├── cycle_001/
│   │   ├── cycle_002/
│   │   └── cycle_003/
│   └── Expert/
│       ├── cycle_001/
│       └── cycle_002/
└── PID0/
    ├── Basic/
    │   ├── cycle_001/
    │   └── cycle_002/
    └── Expert/
        ├── cycle_001/
        └── cycle_002/
```

When defining a layout, we often have a redundancy between the file name
information and the folder information. To avoid redefining the same fields, a
utility function can extract a field from the file name convention.

In our case, we define the following layout for matching the file collection
structure

```{code-cell}
from fcollections.core import Layout
layout = Layout([FileNameConvention(re.compile(r'(?P<version>P[I|G][A-Z]\d{1}_\d{2})'), [convention.get_field('version')]),
                    FileNameConvention(re.compile(r'(?P<subset>.*)'), [convention.get_field('subset')]),
                    FileNameConvention(re.compile(r'cycle_(?P<cycle_number>\d{3})'), [convention.get_field('cycle_number')])])
```

This layout must be given at class instanciation, because even if a dataset is
present on multiple platforms, there is no guarantee that the files'
organization is the same. An integrated default layout would be prone to
breaking, so we instead define independant default layouts (see
the [catalog](implementations/catalog)) and ask the user to properly inject them in the
databases.

```{code-cell}
fc = MyDatabase(path, layout=layout)
```
