Swot Low Rate products
======================

This chapter will present the functionalities specific to the Level 2 and Level
3 SWOT Low Rate products. Although similar, each product follows its own file
name convention and is handled with a dedicated implementation.

.. code-block:: python

    import fcollections.implementations as oct_sio
    # Handlers
    oct_sio.NetcdfFilesDatabaseSwotLRL2
    oct_sio.NetcdfFilesDatabaseSwotLRL3

    # Layouts
    oct_sio.AVISO_L2_LR_SSH_LAYOUT
    oct_sio.AVISO_L3_LR_SSH_LAYOUT

Although the implementations do not share the file name convention, they use the
same reader whose arguments are exposed in the ``query`` interface. We will
illustrate these functionalities by accessing the data from the AVISO FTP server
You will need credentials to authentify (see the
`aviso website <https://www.aviso.altimetry.fr/>`_)


.. raw:: html

    <details>
    <summary><a>Show/Hide code</a></summary>


.. code-block:: python

    from fsspec.implementations.ftp import FTPFileSystem
    fs = FTPFileSystem('ftp-access.aviso.altimetry.fr', 21, username='...', password='...')

.. raw:: html

    </details>
    <br />


Stack for temporal analysis
---------------------------

The most prominent functionality is the ability to stack the half orbits when
the grid is fixed (Basic, Expert, Technical and WindWave subsets). This allows
to work along the ``cycle_number`` dimension and compute temporal analysis
(mean, standard deviation, ...).

There are currently three modes for stacking the half orbits

- ``NOSTACK``: do not stack the half orbits
- ``CYCLES``: concatenate the half orbits of one cycle along the ``num_lines``
  dimension, and stack the cycles along a new ``cycle_number`` dimension
- ``CYCLES_PASSES``: stack the half orbits along the ``cycle_number`` and
  ``pass_number`` dimensions. Useful for regional analysis where the half orbits
  are cropped and we need an additional dimension to reflect the spatial jump


.. code-block:: python

    >>> fc = oct_sio.NetcdfFilesDatabaseSwotLRL3("/swot_products/l3_karin_nadir/l3_lr_ssh", fs=fs, layout=oct_sio.AVISO_L3_LR_SSH_LAYOUT)
    >>>
    >>> ds = fc.query(stack='CYCLES', version='2.0.1', cycle_number=[1, 2, 3], pass_number=10, subset=oct_sio.ProductSubset.Basic)
    >>> ds.sizes
    Frozen({'cycle_number': 2, 'num_lines': 9860, 'num_pixels': 69})
    >>> ds = fc.query(stack='CYCLES_PASSES', version='2.0.1', cycle_number=[1, 2, 3], pass_number=[10, 11], subset=oct_sio.ProductSubset.Basic)
    >>> ds.sizes
    Frozen({'pass_number': 2, 'cycle_number': 2, 'num_lines': 9860, 'num_pixels': 69})

.. note::

    Incomplete cycles are completed with invalids


Filter Level-2 version
----------------------

The Level-2 version is a complex tag composed of a temporality (forward I or
reprocessed G), a baseline (major version A, B, C, D, ...), a minor version
(0, 1, 2, ..) and a product counter (01, 02, ...). The ``L2Version`` class can
handle the tag information and filter out non-desired versions. It can be
partially initialized in order to control the granularity of the filter.

.. code-block:: python

    >>> fc = oct_sio.NetcdfFilesDatabaseSwotLRL2('/swot_products/l2_karin/l2_lr_ssh', fs=fs, layout=oct_sio.AVISO_L2_LR_SSH_LAYOUT)
    >>> version = oct_sio.L2Version(temporality=oct_sio.Timeliness.I)
    'PI??'
    >>> fc.list_files(cycle_number=10, pass_number=10, version=version, subset='Unsmoothed')
    [(cycle_number=10, pass_number=10, version=PIC0_01),]

    >>> version = oct_sio.L2Version(baseline='C')
    'P?C?'
    >>> fc.list_files(cycle_number=10, pass_number=slice(10, 12), version=version, subset='Unsmoothed')
    [(cycle_number=10, pass_number=10, version=PIC0_01), (cycle_number=10, pass_number=111, version=PIC0_01)]


Area selection
--------------

It is possible to select data crossing a specific region by providing ``bbox`` parameter to ``query`` or ``list_files`` method.

The bounding box is represented by a tuple of 4 float numbers, such as : (longitude_min, latitude_min, longitude_max, latitude_max).
Its longitude must follow one of the known conventions: [0, 360[ or [-180, 180[.

If bbox's longitude crosses -180/180, data around the crossing and matching the bbox will be selected.
(e.g. for an interval [170, -170] -> both [170, 180[ and [-180, -170] intervals will be used to list/subset data).

To list files corresponding to half orbits crossing the bounding box:

.. code-block:: python

    >>> fc = oct_sio.NetcdfFilesDatabaseSwotLRL3("/swot_products/l3_karin_nadir/l3_lr_ssh", fs=fs, layout=oct_sio.AVISO_L3_LR_SSH_LAYOUT)
    >>>
    >>> ds = fc.list_files(
    >>>     version='2.0.1',
    >>>     subset="Basic",
    >>>     cycle_number=[29],
    >>>     bbox = (-16, 36, -10, 44))
    [(cycle_number=29, pass_number=3), (cycle_number=29, pass_number=154), (cycle_number=29, pass_number=182), ...]



To query a subset of Swot LR L3 data crossing the bounding box:

.. note::

    Lines of the swath crossing the bounding box will be entirely selected.

.. code-block:: python

    >>> fc = oct_sio.NetcdfFilesDatabaseSwotLRL3("/swot_products/l3_karin_nadir/l3_lr_ssh", fs=fs, layout=oct_sio.AVISO_L3_LR_SSH_LAYOUT)
    >>>
    >>> ds = fc.query(
    >>>     version='2.0.1',
    >>>     subset="Basic",
    >>>     cycle_number=[29],
    >>>     pass_number=[516],
    >>>     bbox = (-16, 36, -10, 44))
    Frozen({'num_lines': 468, 'num_pixels': 69})

.. image:: query_bbox.png


Swath sides in Level-2 Unsmoothed subset
----------------------------------------

The L2_LR_SSH Unsmoothed dataset files are using netcdf groups to separate the
swath sides. This means we can open one of the two sides. The following figure
illustrates how the ``left_swath`` and ``right_swath`` parameters can be used to
retrieve one or the other side.

.. code-block:: python

    fc = oct_sio.NetcdfFilesDatabaseSwotLRL2('/swot_products/l2_karin/l2_lr_ssh', fs=fs, layout=oct_sio.AVISO_L2_LR_SSH_LAYOUT)
    ds_left = fc.query(subset='Unsmoothed', level='L2', cycle_number=525, pass_number=20, left_swath=True, right_swath=False).compute().isel(num_lines=slice(10000, 15000, 3))
    ds_right = fc.query(subset='Unsmoothed', level='L2', cycle_number=525, pass_number=20, left_swath=False, right_swath=True).compute().isel(num_lines=slice(10000, 15000, 3))


.. image:: unsmoothed_sides.png

.. note::

    Combination of both sides is not yet possible. Moreover, keep in mind that
    position coordinates may include invalids which can break geo-plots.


Handling nadir clipped data in Level-3 Basic and Expert subsets
---------------------------------------------------------------

The L3_LR_SSH Basic and Expert subsets have the Nadir instrument data clipped in
the Sea Level Anomaly fields. The indexes where the nadir data has been
introduced are stored along ``num_nadir`` dimension. The SWOT implementation
offers various choices for handling this clipped data:

- ``nadir=False`` and ``swath=True``: remove the nadir data clipped. This is the
  default behavior
- ``nadir=True`` and ``swath=True``: do nothing and keep both the KaRIn and
  Nadir instruments data
- ``nadir=True`` and ``swath=False``: extract the Nadir instrument data only.
  This will give a dataset indexed along the ``num_nadir`` dimension. Because
  it returns the nadir data only, we lose the possibility of stacking multiple
  half orbits

.. code-block:: python

    >>> fc = oct_sio.NetcdfFilesDatabaseSwotLRL3("/swot_products/l3_karin_nadir/l3_lr_ssh", fs=fs, layout=oct_sio.AVISO_L3_LR_SSH_LAYOUT)
    >>> ds = fc.query(version='2.0.1', subset="Basic", cycle_number=550, pass_number=13, nadir=False)
    Frozen({'num_lines': 9860, 'num_pixels': 69})
    >>> ds_nadir = fc.query(version='2.0.1', subset="Basic", cycle_number=550, pass_number=13, nadir=True, swath=False)
    Frozen({'num_nadir': 1748})


Query detailed information
--------------------------

Detailed information on the filters and reading arguments can be found in the
``query`` methods

:meth:`fcollections.implementations.NetcdfFilesDatabaseSwotLRL2.query`

:meth:`fcollections.implementations.NetcdfFilesDatabaseSwotLRL3.query`
