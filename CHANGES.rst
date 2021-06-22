.. explicit references must be used in this file
.. :changelog:

Changes
*******

`Unreleased <https://www.crim.ca/stash/projects/PATR/repos/MODL-EvalBlockChain>`_ (latest)
---------------------------------------------------------------------------------------------------------------

* Nothing yet.

`0.5.0 <https://www.crim.ca/stash/projects/PATR/repos/MODL-EvalBlockChain?at=refs/tags/0.5.0>`_ (2021-06-21)
---------------------------------------------------------------------------------------------------------------

* Add ``Consent`` updates, reporting and resolution against new blocks added to the blockchain.
* Add schema validation error ``messages`` to returned response for contextual details of the cause of failing request.
* Fix issue when resolving remote node IDs using ``detail`` query parameter.
* Fix blockchain creation during the initial resolution to avoid different genesis blocks, resulting in following
  blocks to compute different previous-hash, in turn resulting into diverging blockchains.
* Fix block instantiation using predefined ``created`` value to avoid regeneration with current datetime.
* Fix issue related to incorrect inheritance of fields when resolving JSON representation of ``AttributeDict``.

`0.4.0 <https://www.crim.ca/stash/projects/PATR/repos/MODL-EvalBlockChain?at=refs/tags/0.4.0>`_ (2021-06-18)
---------------------------------------------------------------------------------------------------------------

* Add consents implementation embedded in the blocks of the blockchains.
* Add change tracking, history and resolution of latest consents from blockchain.
* Add Mako templates and UI endpoints to display blockchains and their contents.

`0.3.0 <https://www.crim.ca/stash/projects/PATR/repos/MODL-EvalBlockChain?at=refs/tags/0.3.0>`_ (2021-06-04)
---------------------------------------------------------------------------------------------------------------

Features / Changes
~~~~~~~~~~~~~~~~~~~~~
* Restructure API into separate blueprints sections for the main blockchain functionalities and registered nodes
  for consensus resolution.
* Add provision of JSON/YAML OpenAPI schema and rendering of Swagger UI with it.
* Employ auto schema validator and parameters in functions to retrieved parsed queries.
* Update the API and database implementation to support multiple parallel blockchains.
* Improve resolution mechanism to allow initial consensus to generate the chain when it doesn't exist on current node
  using another node reference.
* Partial implementation of ``Consent`` related objects, but not yet applied to the blockchain.

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
