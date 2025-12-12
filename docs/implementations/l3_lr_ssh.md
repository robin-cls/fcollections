---
file_format: mystnb
kernelspec:
  name: python3
---
# Swot L3_LR_SSH

This chapter will present the functionalities specific to the Level 3 SWOT Low
Rate products.

```{code-cell}

import fcollections.implementations as fc_impl
# Handlers
fc_impl.NetcdfFilesDatabaseSwotLRL3

# Layouts
fc_impl.AVISO_L3_LR_SSH_LAYOUT
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
the grid is fixed (Basic, Expert and Technical subsets). This allows
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

fc = oct_sio.NetcdfFilesDatabaseSwotLRL3(
    "/swot_products/l3_karin_nadir/l3_lr_ssh",
    fs=fs,
    layout=oct_sio.AVISO_L3_LR_SSH_LAYOUT)

ds = fc.query(
    version='2.0.1',
    subset="Basic",
    cycle_number=[29],
    pass_number=[516],
    bbox = (-16, 36, -10, 44))
```

```{image} query_bbox.png
```

## Handling nadir clipped data in Level-3 Basic and Expert subsets

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

```python
fc = oct_sio.NetcdfFilesDatabaseSwotLRL3("/swot_products/l3_karin_nadir/l3_lr_ssh", fs=fs, layout=oct_sio.AVISO_L3_LR_SSH_LAYOUT)
fc.query(version='2.0.1', subset="Basic", cycle_number=550, pass_number=13, nadir=False)
```

```python
fc.query(version='2.0.1', subset="Basic", cycle_number=550, pass_number=13, nadir=True, swath=False)
```

## Query detailed information

Detailed information on the filters and reading arguments can be found in the
``query`` methods

{meth}`fcollections.implementations.NetcdfFilesDatabaseSwotLRL3.query`
