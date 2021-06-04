.. explicit references must be used in this file
.. :changelog:

Changes
*******

`Unreleased <https://www.crim.ca/stash/projects/PATR/repos/MODL-EvalBlockChain>`_ (latest)
---------------------------------------------------------------------------------------------------------------

Features / Changes
~~~~~~~~~~~~~~~~~~~~~
* Restructure API into separate blueprints sections for the main blockchain functionalities and registered nodes
  for consensus resolution.
* Add provision of JSON/YAML OpenAPI schema and rendering of Swagger UI with it.
* Employ auto schema validator and parameters in functions to retrieved parsed queries.
* Update the API and database implementation to support multiple parallel blockchains.

Bug Fixes
~~~~~~~~~~~~~~~~~~~~~
* Fix resolution if LICENSE metadata.

`0.2.0 <https://www.crim.ca/stash/projects/PATR/repos/MODL-EvalBlockChain?at=refs/tags/0.2.0>`_ (2021-05-07)
---------------------------------------------------------------------------------------------------------------

Features / Changes
~~~~~~~~~~~~~~~~~~~~~
* Update linting of strings to uniformize the code.
* Add automatic generation of OpenAPI and JSON schemas.
* Add automatic resolution of package metadata from setup, which itself resolves fields the
  multiple root repository files (``CHANGES``, ``README``, ``LICENSE``, ``requirements.txt``, etc.).

Bug Fixes
~~~~~~~~~~~~~~~~~~~~~
* Fix resolution and loading of ``FileSystemDatabase`` blockchain contents from existing data files.

`0.1.0 <https://www.crim.ca/stash/projects/PATR/repos/MODL-EvalBlockChain?at=refs/tags/0.1.0>`_ (2021-05-01)
---------------------------------------------------------------------------------------------------------------

* First structured release.

Features / Changes
~~~~~~~~~~~~~~~~~~~~~
* Employ reference implementation `dvf/blockchain <https://github.com/dvf/blockchain>`_ to define ``Blockchain``.
* Extend types with ``Block`` and other utilities to facilitate their parameter definition.
* Extend with ``Database`` file system test implementation to persist ``Blocks`` and reload on startup.
* Add ``setup.py``, package metadata and LICENSES definitions.
* Add typing to some existing and new classes.
