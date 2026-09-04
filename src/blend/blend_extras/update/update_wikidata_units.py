#!/usr/bin/env python
# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""Fetch units from :origin:`blend_core/sources/wikidata.py` engine.

Output file: :origin:`blend/data/wikidata_units.json` (:origin:`CI Update data
...  <.github/workflows/data-update.yml>`).

"""

import json

from blend.blend_core.sources import wikidata, set_loggers
from blend.blend_core.data import data_dir
from blend.blend_core.wikidata_units import fetch_units

DATA_FILE = data_dir / 'wikidata_units.json'
set_loggers(wikidata, 'wikidata')


if __name__ == '__main__':
    with DATA_FILE.open('w', encoding="utf8") as f:
        json.dump(fetch_units(), f, indent=4, sort_keys=True, ensure_ascii=False)
