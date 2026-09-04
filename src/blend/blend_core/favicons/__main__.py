# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""Command line implementation"""

import typer

from . import cache
from . import init

init()
app = typer.Typer()
app.add_typer(cache.app, name="cache", help="commands related to the cache")
app()
