# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Raj Singh / Markanm Team

# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
"""Implementation of a command line for development purposes.  To start a
command, switch to the environment and run library module as a script::

   $ ./manage pyenv.cmd bash --norc --noprofile
   (py3) python -m blend_core.enginelib --help

The following commands can be used for maintenance and introspection
(development) of the engine cache::

   (py3) python -m blend_core.enginelib cache state
   (py3) python -m blend_core.enginelib cache maintenance

"""

import typer

from .. import enginelib

app = typer.Typer()
app.add_typer(enginelib.app, name="cache", help="Commands related to the cache of the engines.")
app()
