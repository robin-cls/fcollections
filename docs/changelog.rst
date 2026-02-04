Release notes
=============

1.0.0 (2025-02-04)
------------------

A bit of refactoring has been done in this version to improve the maintainability
and versatility of the code. The following interfaces are impacted:

- ``fcollections.core.FileDiscoverer`` and ``fcollections.core.FileSystemIterable`` have been merged into
  ``fcollections.core.FileSystemMetadataCollector``
- ``fcollections.core.FilesDatabase`` is configured using multiple layouts. Layouts must now declare both folder and filename conventions.
  This effectively makes ``fcollections.core.CompositeLayout`` obsolete (it has been removed)
- A new parameter ``enable_layouts`` has been introduced in ``fcollections.core.FilesDatabase`` to simplify layout feature disabling in
  cast of a mismatch
- A new parameter ``follow_symlinks`` has been introduced in ``fcollections.core.FilesDatabase`` to enable symlinks. (The feature is
  disabled by default)

Details
.......

- fix: keep dataset sorted for bbox selection on unsmoothed dataset `#20 <https://github.com/robin-cls/fcollections/pull/20>`_
- refactor!: Use one or multiple Layouts instead of FileNameConvention in FilesDatabase `#14 <https://github.com/robin-cls/fcollections/pull/14>`_
- feat!: refactor and add layouts for CMEMS implementations `#19 <https://github.com/robin-cls/fcollections/pull/19>`_
- feat!: allow listing with/without layouts `#17 <https://github.com/robin-cls/fcollections/pull/17>`_
- feat!: use INode for FileSystemMetadataCollector `#21 <https://github.com/robin-cls/fcollections/pull/21>`_
- feat: follow symbolic links for posix-compliant local file systems `#18 <https://github.com/robin-cls/fcollections/pull/18>`_
- chore!: remove obsolete code from core API `#16 <https://github.com/robin-cls/fcollections/pull/16>`_
- chore: switch license file name to US spelling `#22 <https://github.com/robin-cls/fcollections/pull/22>`_
- doc: create README and documentation landing page `#15 <https://github.com/robin-cls/fcollections/pull/15>`_

Contributors
............

- Robin Chevrier
- Anne-Sophie Tonneau

0.1.3 (2025-12-15)
------------------

Important
.........

KaRIn geometries URL are now up. Geographical selection should work as intended
for SWOT implementations

Details
.......

- fix: relax area selector longitudes convention `#8 <https://github.com/robin-cls/fcollections/pull/8>`_
- fix: use AVISO Karin Geometries `#4 <https://github.com/robin-cls/fcollections/pull/4>`_
- refactor: redispatch implementations code per product `#6 <https://github.com/robin-cls/fcollections/pull/6>`_
- test: process warnings and enforce full coverage `#11 <https://github.com/robin-cls/fcollections/pull/11>`_
- doc: getting started section conversion to myst_nb `#10 <https://github.com/robin-cls/fcollections/pull/10>`_
- doc: switch implementations documentation to myst_nb `#9 <https://github.com/robin-cls/fcollections/pull/9>`_
- doc: fix signatures and docstrings for sphinx documentation `#7 <https://github.com/robin-cls/fcollections/pull/7>`_
- doc: switch Parameters section to Attributes docstrings in dataclasses `#5 <https://github.com/robin-cls/fcollections/pull/5>`_
- doc: installation procedure and release note `#3 <https://github.com/robin-cls/fcollections/pull/3>`_


0.1.2 (2025-12-09)
------------------

First release. The KaRIn geometries URL are not set up and are expected to break
the geographical selection: avoid using the ``bbox`` argument in the
``query()`` method.
