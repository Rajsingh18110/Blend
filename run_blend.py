import sys
import os

# PyInstaller creates a temporary folder and stores path in _MEIPASS.
# We must ensure that Flask finds the correct base path.
if getattr(sys, 'frozen', False):
    os.environ['BLEND_FROZEN'] = '1'

from blend.cli import main

if __name__ == '__main__':
    main()
