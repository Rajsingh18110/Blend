# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
# SPDX-License-Identifier: Apache-2.0
"""The *answerers* give instant answers related to the search query, they
usually provide answers of type :py:obj:`Answer <blend_core.result_types.Answer>`.

Here is an example of a very simple answerer that adds a "Hello" into the answer
area:

.. code::

   from flask_babel import gettext as _
   from blend.blend_core.answerers import Answerer
   from blend.blend_core.result_types import Answer

   class MyAnswerer(Answerer):

       keywords = [ "hello", "hello world" ]

       def info(self):
           return AnswererInfo(name=_("Hello"), description=_("lorem .."), keywords=self.keywords)

       def answer(self, request, search):
           return [ Answer(answer="Hello") ]

----

.. autoclass:: Answerer
   :members:

.. autoclass:: AnswererInfo
   :members:

.. autoclass:: AnswerStorage
   :members:

.. autoclass:: blend_core.answerers._core.ModuleAnswerer
   :members:
   :show-inheritance:

"""


__all__ = ["AnswererInfo", "Answerer", "AnswerStorage"]


from ._core import AnswererInfo, Answerer, AnswerStorage

STORAGE: AnswerStorage = AnswerStorage()
STORAGE.load_builtins()
