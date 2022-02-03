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
