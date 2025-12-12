Getting started
===============

``fcollections`` is a library that aims at reading a collections of files. Its
primary goal is to combine the selection, reading and concatenation of files
within a common model: ``FilesDatabase``.

Let's set up a minimal case with stub data for the SWOT altimetry mission.

.. raw:: html

    <details>
    <summary><a>Show/Hide code</a></summary>

.. code-block:: python

    import os
    import numpy as np
    import xarray as xr
    import fsspec.implementations.local as fs_loc

    # Create stub data
    os.makedirs('fc', exist_ok=True)
    ds = xr.Dataset(data_vars={
        "ssha": (('num_lines', 'num_pixels'), np.random.random((9860, 69))),
        "swh": (('num_lines', 'num_pixels'), np.random.random((9860, 69))),})
    ds.to_netcdf('fc/SWOT_L2_LR_SSH_Expert_001_011_20240101T000000_20240101T030000_PGC0_01.nc')
    ds.to_netcdf('fc/SWOT_L2_LR_SSH_Expert_001_012_20240101T030000_20240101T060000_PGC0_01.nc')

.. raw:: html

    </details>
    <br />

Implementations
---------------

The generic ``FilesDatabase`` model must be subclassed in order to properly
define the file listing and reading functionalities. A subclass handling a given
type of files is called an implementation.

When confronted to a files collection, the first step is to try and find if
an implementation matching the data already exists. Such implementation may be
found in the following table

.. csv-table:: Implementations
   :file: implementations/implementations.csv
   :header-rows: 1

Here, we can see that :class:`fcollections.implementations.NetcdfFilesDatabaseSwotLRL2`
matches our file names. In case no implementation is available, the user can
build its own following :doc:`custom`.


Listing files
-------------

An implementation can be used by simply giving the path to the data. An
important endpoint for the implementation is the ability to list files matching
given criterias

.. code-block:: python

    >>> import fcollections.implementations as oct_sio
    >>> db = oct_sio.NetcdfFilesDatabaseSwotLRL2('fc')
    >>> ds = db.list_files(cycle_number=1)
    fc/SWOT_L2_LR_SSH_Expert_001_011_20240101T000000_20240101T030000_PGC0_01.nc
    fc/SWOT_L2_LR_SSH_Expert_001_012_20240101T030000_20240101T060000_PGC0_01.nc
    fc/SWOT_L2_LR_SSH_Expert_001_012_20240101T030000_20240101T060000_PGC0_02.nc

Listing files using filters is the first step toward subsetting the files set.


Query data
----------

Another important endpoint is the ability to read the file contents using the
``query`` method.


.. code-block:: python

    >>> import fcollections.implementations as oct_sio
    >>> db = oct_sio.NetcdfFilesDatabaseSwotLRL2('fc')
    >>> ds = db.query()
    >>> ds.dims
    Frozen({'num_lines': 19720, 'num_pixels': 69})

The method returns a :class:`xarray.Dataset` containing the combined data for
all files matching the regex specified by the implementation.

It is possible to load only a subset of the data by applying filters in the
query. For example, giving the ``cycle_number`` and ``pass_number`` argument
will select one half orbit of our altimetry mission.

.. code-block:: python

    >>> db = oct_sio.NetcdfFilesDatabaseSwotLRL2('fc')
    >>> ds = db.query(cycle_number=1, pass_number=11)
    >>> ds.dims
    Frozen({'num_lines': 9860, 'num_pixels': 69})

Variable selection is also available to return only part of the data

.. code-block:: python

    >>> db = oct_sio.NetcdfFilesDatabaseSwotLRL2('fc')
    >>> ds = db.query(selected_variables=['ssha'])
    >>> list(ds.variables)
    ['ssha']

Each implementation has its own filters that can be displayed with the ``query``
method help or in the :doc:`../api` documentation of the implementation.

.. code-block::

    help(fc.query)
    >> Help on method query in module fcollections.core._filesdb:
    >>
    >> query(...) method of __main__.MyDatabase instance
    >> Query a dataset by reading selected files in file system.
    >>
    >>
    >> Parameters
    >> ----------
    >> selected_variables
    >>     list of variables to select in dataset. Set to None (default) to
    >>     disable the selection
    >> cycle_number : int
    >>      As a Integer field, it can be filtered by using a reference value.
    >>     The reference value can either be a list, a slice or an integer. The
    >>     tested value from the file name will be filtered out if it is outside
    >>     the given list/slice or not equal to the integer value.
    >> pass_number : int
    >>      As a Integer field, it can be filtered by using a reference value.
    >>     The reference value can either be a list, a slice or an integer. The
    >>     tested value from the file name will be filtered out if it is outside
    >>     the given list/slice or not equal to the integer value.
    >> bbox : tuple[float, float, float, float]
    >>     the bounding box (lon_min, lat_min, lon_max, lat_max) used to subset data
    >>     Longitude coordinates can be provided in [-180, 180[ or [0, 360[ convention.
    >>     If bbox's longitude crosses the -180/180 of longitude, data around the crossing and matching the bbox will be selected.
    >>     (e.g. longitude interval: [170, -170] -> data in [170, 180[ and [-180, -170] will be retrieved)
    >> time : Period
    >>     As a Period field, it can be filtered by giving a reference Period or
    >>     datetime. The tested value from the file name will be filtered out if
    >>     it does not intersect the reference Period or contain  the reference
    >>     datetime. The reference value can be given as a string or tuple of
    >>     string following the %Y%m%dT%H%M%S formatting
    >> level : str
    >>      As a String field, it can filtered by giving a reference string. The
    >>     tested value from the file name will be filtered out if it is not
        equal to the reference value.
    >> subset : str
    >>      As a String field, it can filtered by giving a reference string. The
    >>     tested value from the file name will be filtered out if it is not
    >>     equal to the reference value.
    >> version : str
    >>      As a String field, it can filtered by giving a reference string. The
    >>     tested value from the file name will be filtered out if it is not
    >>     equal to the reference value.


Access metadata
---------------

The database can display information about the variables and attributes
contained in the files' collection using the ``variables_info`` method

.. code-block:: python

    db = oct_sio.NetcdfFilesDatabaseSwotLRL2('fc')
    ds = db.variables_info(subset='Expert')

It will offer a simple collapsible tree view with multiple levels of nesting
depending on the data you manipulate

.. raw:: html
    :file: variables_info.html

In order to return consistent metadata, the method ensures that only one
homogeneous subset is selected. In case you handle unmixable data (for example
Expert and Unsmoothed datasets), you must give proper filters on the subset
partitioning keys ``db.unmixer.partition_keys``. If these filters are missing,
an error with the possible choices will be raised.

.. code-block:: python

    >>> # Create Unsmoothed file, this will mix Expert and Unsmoothed dataset
    >>> ds.to_netcdf('fc/SWOT_L2_LR_SSH_Unsmoothed_001_012_20240101T030000_20240101T060000_PGC0_01.nc')
    >>> db = oct_sio.NetcdfFilesDatabaseSwotLRL2('fc')
    >>> # This will not work because we don't know if we need to display Expert or
    >>> # Unsmoothed metadata
    >>> db.variables_info()
    ValueError: Subsets could not be unmixed, the following keys are duplicated and should be fixed manually: {'subset': [<ProductSubset.Expert: 2>, <ProductSubset.Unsmoothed: 4>]}
    # Use the enumeration name for filtering
    >>> db.variables_info(subset='Expert')
    Metadata properly displayed


Remote file systems
-------------------

It is possible to access a file set from a remote location. Fcollections is based on
the powerful ``fsspec`` abstraction. As a consequence, files collections might
accept any file system, provided that the underlying reader supports it.

.. warning::

    In case the reader does not support a specific file system, an error will be
    triggered. The solution is to implement its own reader following
    :doc:`custom`

The following code shows how to access data directly from the AVISO public FTP.
You will need credentials to authentify (see the
`aviso website <https://www.aviso.altimetry.fr/>`_)

.. code-block:: python

    >>> from fsspec.implementations.ftp import FTPFileSystem
    >>> fs = FTPFileSystem('ftp-access.aviso.altimetry.fr', 21, username='...', password='...')
    >>> db = oct_sio.NetcdfFilesDatabaseSwotLRL2('/swot_products/l2_karin/l2_lr_ssh/PIC2/Expert/cycle_031', fs=fs)
    >>> ds = db.query(pass_number=1)
    >>> ds.sizes
    Frozen({'num_lines': 9860, 'num_pixels': 69})

.. _layout_intro:

Partial file listing
--------------------

A files collection is usually stored on a file system storage at a root path,
with nested folders for organizing the data. By default, all subfolders are
scanned to build the files metadata table. However, in case filters for listing
or querying the database are defined, only a subset of the subfolders are
relevant: a global scan is then inefficient.

In order to finely select the subfolders to explore, a
:class:`fcollections.core.Layout` object can be given to the
:class:`fcollections.core.FilesDatabase`. This object gives information about how
the file collection is organized and speeds up the requests.

.. note::

    Pre-configured layouts are associated to the implementations. They can be
    found in the :doc:`summary table <implementations/catalog>`

Below is an example of how a layout shall be configured. The given query filters
match the ``<version>/<subset>/<cycle_number>`` structure declared in the layout

.. code-block:: python

    >>> from fsspec.implementations.ftp import FTPFileSystem
    >>> fs = FTPFileSystem('ftp-access.aviso.altimetry.fr', 21, username='...', password='...')
    >>> db = oct_sio.NetcdfFilesDatabaseSwotLRL3('/swot_products/l3_karin_nadir/l3_lr_ssh', fs=fs, layout=oct_sio.AVISO_L3_LR_SSH_LAYOUT)
    >>> ds = db.query(version='2.0.1', cycle_number=31, subset='Expert', pass_number=1)
    >>> ds.sizes
    Frozen({'num_lines': 9860, 'num_pixels': 69})

In case the layout object mismatches the actual structure of the file
collection, the requests will return empty results. A warning will also be
raised and the user has two options to solve this issue:

- Remove the layout from it database instance, though the requests will fall
  back to a default a global scan
- Create the layout object matching the file collection structure, see
  :ref:`layout` for how to build a layout


.. code-block:: python

    >>> from fsspec.implementations.ftp import FTPFileSystem
    >>> import logging; logging.basicConfig() # Set up to display warnings
    >>>
    >>> fs = FTPFileSystem('ftp-access.aviso.altimetry.fr', 21, username='...', password='...')
    >>> # Here, the root of the file collection is misplaced, causing a mismatch between the file collection and the layout
    >>> db = oct_sio.NetcdfFilesDatabaseSwotLRL3('/swot_products/l3_karin_nadir/l3_lr_ssh/v2_0_1/Expert', fs=fs, layout=oct_sio.AVISO_L3_LR_SSH_LAYOUT)
    >>> ds = db.query(version='2.0.1', cycle_number=31, subset='Expert', pass_number=1)
    WARNING:py.warnings:<...>/_listing.py:161: UserWarning: Actual node cycle_513 did not match the expected convention re.compile('v(?P<version>.*)'). This is probably due to a mismatch between the layout and the actual tree structure
    warnings.warn(msg)
    ...
    >>> ds is None
    True
