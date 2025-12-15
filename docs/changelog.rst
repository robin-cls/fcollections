Release notes
=============

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
