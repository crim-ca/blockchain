from pydantic import UUID4
from typing import Dict, List, Optional, Union

AnyUUID = Union[UUID4, str]
AnyRef = Union[str, int, UUID4]
Number = Union[int, float]
JsonValue = Optional[Union[bool, str, Number]]
JsonObject = Dict[str, "JSON"]
JsonArray = List["JSON"]
JSON = Union[JsonValue, JsonArray, JsonObject]

# JSON limited to single level (not nested)
Mapping = Dict[str, Union[JsonValue, List[JsonValue]]]
