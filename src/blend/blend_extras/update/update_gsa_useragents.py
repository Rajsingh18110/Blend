#!/usr/bin/env python
# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""This script fetches user agents suitable for blend.

Output file: :origin:`blend/data/gsa_useragents.txt` (:origin:`CI Update data
...  <.github/workflows/data-update.yml>`).

.. Source for user agents: https://github.com/intoli/user-agents/

"""

from gzip import decompress
from json import loads

from blend.blend_core.data import data_dir
from blend.blend_core.network import get as http_get
from blend.blend_core.utils import markanm_useragent

DATA_FILE = data_dir / "gsa_useragents.txt"
URL = "https://raw.githubusercontent.com/intoli/user-agents/main/src/user-agents.json.gz"


def fetch_gsa_useragents() -> list[str]:
    response = http_get(URL, timeout=3.0, headers={"User-Agent": markanm_useragent()})
    response.raise_for_status()

    suas: set[str] = set()
    for ua in loads(decompress(response.content)):
        if "Android" in ua["userAgent"] and "Chrome" in ua["userAgent"] and "Samsung" not in ua["userAgent"]:
            suas.add(ua["userAgent"])

    luas = list(suas)
    luas.sort()

    return luas


if __name__ == "__main__":
    useragents = fetch_gsa_useragents()
    with DATA_FILE.open("w", encoding="utf-8") as f:
        f.write("\n".join(useragents))
