#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, List, Optional, TypedDict, Union
    from uuid import UUID

    Number = Union[int, float]
    JsonValue = Optional[Union[bool, str, Number]]
    JsonObject = Dict[str, "JSON"]
    JsonArray = List["JSON"]
    JSON = Union[JsonValue, JsonArray, JsonObject]

    AnyUUID = Union[UUID, str]
    AnyRef = Union[str, int, UUID]
    Link = TypedDict("Link", {"href": str, "rel": str, "title": str})

try:
    from importlib_metadata import metadata
except ImportError:
    from importlib import metadata

# all metadata defined in setup.py accessible from package for reuse
package = os.path.basename(os.path.dirname(__file__))
__meta__ = metadata(package)
__title__ = __meta__["Description"].splitlines()[0].replace("# ", "")
