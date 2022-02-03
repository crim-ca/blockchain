.. explicit references must be used in this file
.. :changelog:

Changes
*******

`Unreleased <https://github.com/crim-ca/blockchain/tree/master>`_ (latest)
---------------------------------------------------------------------------------------------------------------

* Add ``subsystems`` definitions to blocks stored in the blockchains to detail referenced data for which the
  consents are being applied.
* Add more extensive documentation about content metadata when ``subsystems`` are involved.
* Add more CSS definitions for different field types allowing better interpretation of consents metadata at a glance.
* Improve application log message format and align ``uvicorn`` logging details with it.
* Fix import error when computing block hash.
* Fix default modification ``ContentType`` from ``CREATED`` to new ``UNDEFINED``.
  This better explains why the creation time of a dynamically generated consent during *latest consents* listing
  always changes upon each API or UI call.
* Fix potential incomplete save of blockchain following corrupted data in block.
* Fix block creation from direct dictionary instead of keyword arguments.
* Fix resolution of class implementations to enforce parsing and validation of properties when available.
* Fix format of ``created`` and ``expire`` fields in API and for saving data using consistent ISO formatted datetimes.

`1.1.0 <https://github.com/crim-ca/blockchain/tree/1.1.0>`_ (2022-01-26)
---------------------------------------------------------------------------------------------------------------

* Add generation of OpenAPI schema per version to documentation directory.
* Remove the need to supply the ``--secret`` argument when creating the genesis block using ``--new`` argument.
* Fix application imports causing circular references between schemas and blockchain class implementations.

`1.0.0 <https://github.com/crim-ca/blockchain/tree/1.0.0>`_ (2022-01-25)
---------------------------------------------------------------------------------------------------------------

* Refactor code using ``FastAPI`` framework for better schema validation and generation in OpenAPI documentation.
* Add required ``--secret`` option that sets the Blockchain node secret for hashing blocks.
* Fix warning about potential *Length Extension Attacks* related to applied hashing method
  (relates to `HL101 warning <https://pycharm-security.readthedocs.io/en/latest/checks/HL101.html>`_,
  `Length Extension Attacks <https://blog.skullsecurity.org/2012/everything-you-need-to-know-about-hash-length-extension-attacks>`_).
* Fix startup of application as direct Python due to arguments not retrieved from ``sys.argv``.
* Fix docker image build.

`0.11.2 <https://github.com/crim-ca/blockchain/tree/0.11.2>`_ (2021-08-16)
---------------------------------------------------------------------------------------------------------------

* Fix missing ``detail=true`` parameter for retrieval of remote node blocks during blockchain consensus resolution.

`0.11.1 <https://github.com/crim-ca/blockchain/tree/0.11.1>`_ (2021-08-16)
---------------------------------------------------------------------------------------------------------------

* Update invalid requirements reference to extended ``addict`` package with JSON converter.

`0.11.0 <https://github.com/crim-ca/blockchain/tree/0.11.0>`_ (2021-08-16)
---------------------------------------------------------------------------------------------------------------

* Add current API ``version`` field in frontpage endpoint.
* Add API ``version`` label to every UI page using shared inherited Mako definition.

`0.10.0 <https://github.com/crim-ca/blockchain/tree/0.10.0>`_ (2021-08-12)
---------------------------------------------------------------------------------------------------------------

* Add UI endpoint and links that allow display of complete list of blocks details and their stored consents.
* Add typing definitions for ``blockchain.app:run`` command to help understand expected inputs for ``gunicorn`` call.
* Add metadata rendering about the currently viewed blockchain for both new blocks and previous consents UI pages.
* Replace ``APP.node`` with only ``UUID`` of current node by full ``Node`` class that contains both the URL and UUID.
* Fix override of local node ``host`` value to allow referring to public IP.

`0.9.0 <https://github.com/crim-ca/blockchain/tree/0.9.0>`_ (2021-08-12)
---------------------------------------------------------------------------------------------------------------

* Add sample execution call to start an application node using multiple ``gunicorn`` workers.
* Add ``gunicorn`` to requirements.
* Fix breaking changes in ``flask`` and ``apispec`` major versions not pinned by ``flask-apispec``.

`0.8.0 <https://github.com/crim-ca/blockchain/tree/0.8.0>`_ (2021-08-09)
---------------------------------------------------------------------------------------------------------------

* Change ``GET /chains/{CHAIN_ID}/blocks`` endpoint to return by default a list of Block IDs instead of their expanded
  definition. Query parameter ``detail=true`` can be provided to return the expanded definitions of the blocks.
* Add ``resolve=true|false`` (default ``false``) query parameter to ``GET /chains`` to allow initial creation of
  all missing Blockchain definitions on a server node using retrieved definitions from remote nodes in the network.
  This is equivalent to calling initial consensus resolution (blockchain generated) for all missing ID of other
  nodes ``GET /chains/{CHAIN_ID}/resolve`` responses.
* Add performance test for evaluation purpose (CLI with repeated request calls and timing summary statistics).
* Add ``app.run`` function to allow execution of the Web Application through WSGI runner such as ``gunicorn``.
* Change parsing of command line arguments to support both direct Web Application call and through WSGI runner.

`0.7.0 <https://github.com/crim-ca/blockchain/tree/0.7.0>`_ (2021-07-16)
---------------------------------------------------------------------------------------------------------------

* Add listing of known remote network nodes in UI summary page.
* Add ``http`` scheme to current node URL location returned in responses.
* Add ``ui`` URL link in node entrypoint response.
* Add URL links clickable to relevant locations in UI pages.
* Add CSS for ``UUID`` fields in UI pages.
* Apply sorting of ``Content`` by ``ContentAction`` rather than created date for easier readability in UI page.

`0.6.0 <https://github.com/crim-ca/blockchain/tree/0.6.0>`_ (2021-07-09)
---------------------------------------------------------------------------------------------------------------

* Add body top-menu table to render current node ID on each UI page.
* Fix incorrect rendering of UI shortcut link titles.

`0.5.0 <https://github.com/crim-ca/blockchain/tree/0.5.0>`_ (2021-06-21)
---------------------------------------------------------------------------------------------------------------

* Add ``Consent`` updates, reporting and resolution against new blocks added to the blockchain.
* Add schema validation error ``messages`` to returned response for contextual details of the cause of failing request.
* Fix issue when resolving remote node IDs using ``detail`` query parameter.
* Fix blockchain creation during the initial resolution to avoid different genesis blocks, resulting in following
  blocks to compute different previous-hash, in turn resulting into diverging blockchains.
* Fix block instantiation using predefined ``created`` value to avoid regeneration with current datetime.
* Fix issue related to incorrect inheritance of fields when resolving JSON representation of ``AttributeDict``.

`0.4.0 <https://github.com/crim-ca/blockchain/tree/0.4.0>`_ (2021-06-18)
---------------------------------------------------------------------------------------------------------------

* Add consents implementation embedded in the blocks of the blockchains.
* Add change tracking, history and resolution of latest consents from blockchain.
* Add Mako templates and UI endpoints to display blockchains and their contents.

`0.3.0 <https://github.com/crim-ca/blockchain/tree/0.3.0>`_ (2021-06-04)
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

`0.2.0 <https://github.com/crim-ca/blockchain/tree/0.2.0>`_ (2021-05-07)
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

`0.1.0 <https://github.com/crim-ca/blockchain/tree/0.1.0>`_ (2021-05-01)
---------------------------------------------------------------------------------------------------------------

* First structured release.

Features / Changes
~~~~~~~~~~~~~~~~~~~~~
* Employ reference implementation `dvf/blockchain <https://github.com/dvf/blockchain>`_ to define ``Blockchain``.
* Extend types with ``Block`` and other utilities to facilitate their parameter definition.
* Extend with ``Database`` file system test implementation to persist ``Blocks`` and reload on startup.
* Add ``setup.py``, package metadata and LICENSES definitions.
* Add typing to some existing and new classes.
