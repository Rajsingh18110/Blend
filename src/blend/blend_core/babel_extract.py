# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""This module implements the :origin:`markanm_msg <babel.cfg>` extractor to
extract messages from:

- :origin:`blend/markanm.msg`

The ``markanm.msg`` files are selected by Babel_, see Babel's configuration in
:origin:`babel.cfg`::

    markanm_msg = blend_core.babel_extract.extract
    ...
    [markanm_msg: **/markanm.msg]

A ``markanm.msg`` file is a python file that is *executed* by the
:py:obj:`extract` function.  Additional ``markanm.msg`` files can be added by:

1. Adding a ``markanm.msg`` file in one of the Markanm python packages and
2. implement a method in :py:obj:`extract` that yields messages from this file.

.. _Babel: https://babel.pocoo.org/en/latest/index.html

"""

from os import path

MARKANM_MSG_FILE = "markanm.msg"
_MSG_FILES = [path.join(path.dirname(__file__), MARKANM_MSG_FILE)]


def extract(
    # pylint: disable=unused-argument
    fileobj,
    keywords,
    comment_tags,
    options,
):
    """Extract messages from ``markanm.msg`` files by a custom extractor_.

    .. _extractor:
       https://babel.pocoo.org/en/latest/messages.html#writing-extraction-methods
    """
    if fileobj.name not in _MSG_FILES:
        raise RuntimeError("don't know how to extract messages from %s" % fileobj.name)

    namespace = {}
    exec(fileobj.read(), {}, namespace)  # pylint: disable=exec-used

    for obj_name in namespace['__all__']:
        obj = namespace[obj_name]
        if isinstance(obj, list):
            for msg in obj:
                # (lineno, funcname, message, comments)
                yield 0, '_', msg, [f"{obj_name}"]
        elif isinstance(obj, dict):
            for k, msg in obj.items():
                yield 0, '_', msg, [f"{obj_name}['{k}']"]
        else:
            raise ValueError(f"{obj_name} should be list or dict")
