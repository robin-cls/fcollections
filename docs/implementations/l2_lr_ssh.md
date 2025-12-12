# Swot L2_LR_SSH

This chapter will present the functionalities specific to the Level 2 SWOT Low
Rate products.

```python

import fcollections.implementations as fs_impl
# Handlers
fs_impl.NetcdfFilesDatabaseSwotLRL2

# Layouts
fs_impl.AVISO_L2_LR_SSH_LAYOUT
```

Although the implementations do not share the file name convention, they use the
same reader whose arguments are exposed in the ``query`` interface. We will
illustrate these functionalities by accessing the data from the AVISO FTP server
You will need credentials to authentify (see the
[aviso website](https://www.aviso.altimetry.fr/))

```python
from fsspec.implementations.ftp import FTPFileSystem
fs = FTPFileSystem('ftp-access.aviso.altimetry.fr', 21, username='...', password='...')
```

## Stack for temporal analysis

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

```python
fc = oct_sio.NetcdfFilesDatabaseSwotLRL3("/swot_products/l3_karin_nadir/l3_lr_ssh", fs=fs, layout=oct_sio.AVISO_L3_LR_SSH_LAYOUT)
fc.query(stack='CYCLES', version='2.0.1', cycle_number=[1, 2, 3], pass_number=10, subset=oct_sio.ProductSubset.Basic)
```

```python
fc.query(stack='CYCLES_PASSES', version='2.0.1', cycle_number=[1, 2, 3], pass_number=[10, 11], subset=oct_sio.ProductSubset.Basic)
```

```{note}
Incomplete cycles are completed with invalids
```

## Filter Level-2 version

The Level-2 version is a complex tag composed of a temporality (forward I or
reprocessed G), a baseline (major version A, B, C, D, ...), a minor version
(0, 1, 2, ..) and a product counter (01, 02, ...). The ``L2Version`` class can
handle the tag information and filter out non-desired versions. It can be
partially initialized in order to control the granularity of the filter.

```python
fc = oct_sio.NetcdfFilesDatabaseSwotLRL2('/swot_products/l2_karin/l2_lr_ssh', fs=fs, layout=oct_sio.AVISO_L2_LR_SSH_LAYOUT)
version = oct_sio.L2Version(temporality=oct_sio.Timeliness.I)
version
```

```python
fc.list_files(cycle_number=10, pass_number=10, version=version, subset='Unsmoothed')
```

```python
version = oct_sio.L2Version(baseline='C')
```

```python
fc.list_files(cycle_number=10, pass_number=slice(10, 12), version=version, subset='Unsmoothed')
```

## Area selection

It is possible to select data crossing a specific region by providing ``bbox`` parameter to ``query`` or ``list_files`` method.

The bounding box is represented by a tuple of 4 float numbers, such as : (longitude_min, latitude_min, longitude_max, latitude_max).
Its longitude must follow one of the known conventions: [0, 360[ or [-180, 180[.

If bbox's longitude crosses -180/180, data around the crossing and matching the bbox will be selected.
(e.g. for an interval [170, -170] -> both [170, 180[ and [-180, -170] intervals will be used to list/subset data).

To list files corresponding to half orbits crossing the bounding box:

```python
fc = oct_sio.NetcdfFilesDatabaseSwotLRL3("/swot_products/l3_karin_nadir/l3_lr_ssh", fs=fs, layout=oct_sio.AVISO_L3_LR_SSH_LAYOUT)
fc.list_files(
    version='2.0.1',
    subset="Basic",
    cycle_number=[29],
    bbox = (-16, 36, -10, 44))
```

To query a subset of Swot LR L3 data crossing the bounding box:

```{note}
Lines of the swath crossing the bounding box will be entirely selected.
```

```python

fc = oct_sio.NetcdfFilesDatabaseSwotLRL3("/swot_products/l3_karin_nadir/l3_lr_ssh", fs=fs, layout=oct_sio.AVISO_L3_LR_SSH_LAYOUT)
ds = fc.query(
    version='2.0.1',
    subset="Basic",
    cycle_number=[29],
    pass_number=[516],
    bbox = (-16, 36, -10, 44))
```

```{image} query_bbox.png
```

## Swath sides in Level-2 Unsmoothed subset

The L2_LR_SSH Unsmoothed dataset files are using netcdf groups to separate the
swath sides. This means we can open one of the two sides. The following figure
illustrates how the ``left_swath`` and ``right_swath`` parameters can be used to
retrieve one or the other side.

```python
fc = oct_sio.NetcdfFilesDatabaseSwotLRL2('/swot_products/l2_karin/l2_lr_ssh', fs=fs, layout=oct_sio.AVISO_L2_LR_SSH_LAYOUT)
ds_left = fc.query(subset='Unsmoothed', level='L2', cycle_number=525, pass_number=20, left_swath=True, right_swath=False).compute().isel(num_lines=slice(10000, 15000, 3))
ds_left
```

```python
ds_right = fc.query(subset='Unsmoothed', level='L2', cycle_number=525, pass_number=20, left_swath=False, right_swath=True).compute().isel(num_lines=slice(10000, 15000, 3))
ds_right
```

```{image} unsmoothed_sides.png
```

```{note}
Combination of both sides is not yet possible. Moreover, keep in mind that
position coordinates may include invalids which can break geo-plots.
```

## Query detailed information

Detailed information on the filters and reading arguments can be found in the
``query`` methods

{meth}`fcollections.implementations.NetcdfFilesDatabaseSwotLRL2.query`
