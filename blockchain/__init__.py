#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from typing import Dict, List, Optional, Union
from pydantic import UUID4
from importlib_metadata import metadata

# all metadata defined in setup.py accessible from package for reuse
package = os.path.basename(os.path.dirname(__file__))
__meta__ = metadata(package)
__title__ = __meta__["Description"].splitlines()[0].replace("# ", "")

# types

Number = Union[int, float]
JsonValue = Optional[Union[bool, str, Number]]
JsonObject = Dict[str, "JSON"]
JsonArray = List["JSON"]
JSON = Union[JsonValue, JsonArray, JsonObject]

AnyUUID = Union[UUID4, str]
AnyRef = Union[str, int, UUID4]
