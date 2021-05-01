#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

try:
    # typing only available builtin starting with Python3
    # cannot employ it during setup, but will be installed afterwards with backport
    from typing import TYPE_CHECKING  # noqa
    if TYPE_CHECKING:
        # pylint: disable=W0611,unused-import
        from typing import Iterable, Set, Tuple, Union  # noqa: F401
except ImportError:
    pass

PACKAGE_NAME = "blockchain"

LOGGER = logging.getLogger("{}.setup".format(PACKAGE_NAME))
if logging.StreamHandler not in LOGGER.handlers:
    LOGGER.addHandler(logging.StreamHandler(sys.stdout))  # type: ignore # noqa
LOGGER.setLevel(logging.INFO)
LOGGER.info("starting setup")

DESCRIPTION = ""
with open("README.md") as readme_file:
    README = readme_file.read()
    lines = [line.strip() for line in README.splitlines() if not line.startswith("#")]
    found = False
    start = None
    for i in range(len(lines)):
        if lines[i] == "":
            if found:
                break
            continue
        if start is None:
            start = i
        found = True
    DESCRIPTION = " ".join(lines[start:i])

LICENSE = ""
LICENSE_NAME = ""
if os.path.exists("LICENSE"):
    with open("LICENSE") as license_file:
        LICENSE = license_file.read()
        LICENSE_NAME = [line.strip() for line in LICENSE.splitlines() if line.strip()][0]

CHANGES = ""
if os.path.isfile("CHANGES.rst"):
    with open("CHANGES.rst") as changes_file:
        CHANGES = changes_file.read().replace(".. :changelog:", "")


LOGGER.info("reading requirements")
REQUIREMENTS = {}
for req in ["", "dev", "docs", "test"]:
    req_name = "requirements{}.txt".format(req)
    REQUIREMENTS[req] = []
    if os.path.isfile(req_name):
        with open(req_name) as req_file:
            requires = {req.strip() for req in req_file.readlines()}
            REQUIREMENTS[req] = list(set(r for r in requires if r and not r.startswith("#")))
    LOGGER.info("%s%srequirements: %s", req, " " if req else "", REQUIREMENTS[req])

setup(
    # -- meta information --------------------------------------------------
    name=PACKAGE_NAME,
    version="0.0.0",
    description=DESCRIPTION,
    long_description=README + "\n\n" + CHANGES,
    author="CRIM",
    maintainer="Francis Charette-Migneault",
    maintainer_email="francis.charette-migneault@crim.ca",
    contact="CRIM Info",
    contact_email="info@crim.ca",
    url="https://www.crim.ca/stash/projects/PATR/repos/MODL-EvalBlockChain",
    platforms=["linux_x86_64"],
    license=LICENSE_NAME,
    keywords="Blockchain, Security, Data Integrity, Consensus",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: {}".format(LICENSE_NAME) if LICENSE_NAME else "",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.6.*, <4",

    # -- Package structure -------------------------------------------------
    packages=[PACKAGE_NAME],
    package_dir={PACKAGE_NAME: PACKAGE_NAME},
    include_package_data=True,
    install_requires=REQUIREMENTS[""],
    extras_require={req: REQUIREMENTS[req] for req in REQUIREMENTS if req},
    zip_safe=False,

    # -- self - tests --------------------------------------------------------
    test_suite="tests",
    tests_require=REQUIREMENTS["test"],

    # -- script entry points -----------------------------------------------
    entry_points={
        "paste.app_factory": [
            "main = {}.app:main".format(PACKAGE_NAME)
        ],
        "console_scripts": [
            "app = {}.app:main".format(PACKAGE_NAME),
        ],
    }
)
LOGGER.info("setup complete")
