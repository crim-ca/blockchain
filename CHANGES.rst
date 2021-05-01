.. explicit references must be used in this file
.. :changelog:

Changes
*******

`Unreleased <https://www.crim.ca/stash/projects/PATR/repos/MODL-EvalBlockChain>`_ (latest)
------------------------------------------------------------------------------------

* First structured release.

Features / Changes
~~~~~~~~~~~~~~~~~~~~~
* Employ reference implementation `dvf/blockchain <https://github.com/dvf/blockchain>`_ to define ``Blockchain``.
* Extend types with ``Block`` and other utilities to facilitate their parameter definition.
* Extend with ``Database`` file system test implementation to persist ``Blocks`` and reload on startup.
* Add ``setup.py``, package metadata and LICENSES definitions.
* Add typing to some existing and new classes.
