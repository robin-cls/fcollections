Files Collections
=================

Select and read a collection of files

.. code-block:: python

    from fcollections.implementations import NetcdfFilesDatabaseSwotLRL3

    fc = NetcdfFilesDatabaseSwotLRL3("data")
    fc.query(cycle_number=1, pass_number=1)


- Information contained in files and folders names are used to create basic
  selection filters
- Both local and :ref:`remote file systems <remote>` (FTP, S3, ...) can be explored
- Multiple implementations for handling different products and their specificities (see the :doc:`catalog <implementations/catalog>`)
- Easy :doc:`building of an implementation <custom>` for a new product


.. toctree::
    :caption: Files Collection

    install
    getting_started
    custom

.. toctree::
    :caption: Implementations

    implementations/catalog
    implementations/l2_lr_ssh
    implementations/l3_lr_ssh

.. toctree::
    :caption: Utilities

    auxiliary

.. toctree::
    :caption: Reference
    :maxdepth: 1

    api
    changelog
