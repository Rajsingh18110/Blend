import sys
import os

# Filter for modules in our backend
def print_trace():
    print("Runtime Imports:")
    for m in sys.modules.values():
        if hasattr(m, '__file__') and m.__file__ and 'backend' in m.__file__:
            print(f"- {os.path.relpath(m.__file__)}")

import backend.app as app

print_trace()
