#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, List, Optional, Union

    Number = Union[int, float]
    JsonValue = Optional[Union[bool, str, Number]]
    JsonObject = Dict[str, "JSON"]
    JsonArray = List["JSON"]
    JSON = Union[JsonValue, JsonArray, JsonObject]
