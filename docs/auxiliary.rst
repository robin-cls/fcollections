Fetch auxiliary data
====================

Separating code from data is generally recognized as a good practice. This is
done in order to reduce the binaries' size and allowing different lifecycles for
the software and the data. As a consequence, libraries may relies on data that
are remotely available but not shipped with their package. We can cite
``cartopy`` - often used in earth data science - as an example.

If multiple pieces of software need to fetch the same data, it can introduce
duplicate code and an additional maintenance burden. This present module
proposes a solution to handling auxiliary data by making an inventory of useful
data and providing a simple way to fetch them. Software consumers can then get
their data transparently without caring about the fetching part.

Use from Python
---------------

Accessing auxiliary data from Python is done using a class matching the data of
interest. Because this module has been built for satellite altimetry, it can
retrieve shore lines, river lines and altimeters' footprints. The exhaustive
list and descriptions of the available classes can be found in the
:doc:`API documentation <fcollections.sad>`.

The class hosts a set of keys that act as identifiers for each downloadable
asset (generally one file). Its meaning is heavily dependent on the class so the
API documentation can help identify your key. Once the key has been chosen, the
associated asset can be retrieved using the subscription notation ``aux[key]``.

If the file is not available on your local file system, it will be automatically
downloaded using the pre-coded fetching request (http or ftp depending on the
data). The following example shows an example where the download is
automatically triggered

.. code-block:: python

    import logging
    import xarray as xr
    import fcollections.sad

    # Setup logging to monitor if a download is triggered
    logging.basicConfig()
    logging.getLogger('fcollections').setLevel('INFO')

    aux = fcollections.sad.GSHHG()

    print(aux.keys)
    >> {'border_i', 'river_c', 'GSHHS_h', 'GSHHS_f', 'border_h', 'border_c', 'GSHHS_i', 'border_f', 'GSHHS_l', 'GSHHS_c', 'river_i', 'river_f', 'river_l', 'river_h', 'border_l'}

    file = aux['GSHHS_c']
    >> INFO:fcollections.sad._gshhg:Downloading gshhg/gshhg-gmt-2.3.7.tar.gz...
    >> INFO:fcollections.sad._gshhg:Downloading gshhg/gshhg-gmt-2.3.7.tar.gz... Done
    >> /home/myuser/.config/sad/binned_GSHHS_c.nc

    # Continue working with your auxiliary data file
    ds = xr.open_dataset(file)
    ...


.. note::

    In case your are behind a proxy, you need to setup the ``http_proxy``,
    ``https_proxy`` and ``ftp_proxy`` environment variables


Available data
--------------

Apart from the API description, a command line tool is available. The
``summary`` command prints a brief for all data types and shows which one are
available locally

.. code-block:: bash

    [myuser@mymachine]$ sad summary
    ┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Type             ┃ Available ┃ Keys                                                                                           ┃ Lookup Folders               ┃
    ┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │ gshhg            │ 0/15      │ GSHHS_c,GSHHS_f,GSHHS_h,GSHHS_i,GSHHS_l,border_c,border_f,border_h,border_i,border_l,river_c,r │ /home/myuser/.config/sad     │
    │                  │           │ iver_f,river_h,river_i,river_l                                                                 │                              │
    │ karin_footprints │ 0/2       │ calval,science                                                                                 │ /home/myuser/.config/sad     │
    └──────────────────┴───────────┴────────────────────────────────────────────────────────────────────────────────────────────────┴──────────────────────────────┘

Handling scattered data
-----------------------

Given that we use a mix of classic and more specialized data, it is probable
that part of the files we need are already somewhere on the file system. For
each type of data, the module will look into:

- A generic folder set by the ``SAD_DATA`` environment variable
- A specific folder set by the ``SAD_DATA_<placeholder>`` environment variable,
  where ``<placeholder>`` is the data type identifier
- The user folder (defaulting to ``~/.config/sad``)

The multiplication of environment variables can be confusing. The ``env``
command is here to summarize which folders are set from the environment
variables, giving hints about where the program will look for the data.

.. code-block:: bash

    [myuser@mymachine]$ sad env
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Name                      ┃ Value                                                    ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │ SAD_DATA                  │ INVALID -> ''                                            │
    │ SAD_DATA_GSHHG            │ UNSET                                                    │
    │ SAD_DATA_KARIN_FOOTPRINTS │ /path/to/swot/data/KaRIn_geometries/                     │
    └───────────────────────────┴──────────────────────────────────────────────────────────┘


Setup auxiliary data for everyone
---------------------------------

The default behavior for downloading a missing asset is to download it in the
user folder. This ensures proper writing permission but is prone to duplicate
data between users.

The alternative is to download all the auxiliary data in a shared folder. This
can be done using the ``download`` command.

.. code-block:: bash

    [myuser@mymachine]$ export SAD_DATA='/path/to/shared/sad/data'
    [myuser@mymachine]$ sad download $SAD_DATA
    Processing sources...       ━━━━━━━━━━━━━━━━━━━━╺━━━━━━━━━━━━━━━━━━━  50% -:--:--
    Processing keys in gshhg... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00

Once the data is downloaded, users can set the ``SAD_DATA`` environment
variable in the sourced file of their choice.

Alternatively, if you manage a shared conda environment, you can bypass this by
setting the environment variable at activation ``conda env config vars -h``.
Lastly, if you manage a shared Jupyter kernel, you can also set up the variable
at the kernel creation ``python ipykernel install --help``
