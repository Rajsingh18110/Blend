# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""Command line implementation"""

import typer

from .core import get_cache

app = typer.Typer()


@app.command()
def state():
    """show state of the cache"""
    cache = get_cache()
    for table in cache.table_names:
        for row in cache.DB.execute(f"SELECT count(*) FROM {table}"):
            print(f"cache table {table} holds {row[0]} key/value pairs")


app()
