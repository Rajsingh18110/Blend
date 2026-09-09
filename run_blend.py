import sys
import os

# PyInstaller creates a temporary folder and stores path in _MEIPASS.
# We must ensure that Flask finds the correct base path.
if getattr(sys, 'frozen', False):
    os.environ['BLEND_FROZEN'] = '1'
    try:
        import blend.blend_core.extensions.ahmia_filter
        import blend.blend_core.extensions.calculator
        import blend.blend_core.extensions.hash_plugin
        import blend.blend_core.extensions.hostnames
        import blend.blend_core.extensions.infinite_scroll
        import blend.blend_core.extensions.oa_doi_rewrite
        import blend.blend_core.extensions.self_info
        import blend.blend_core.extensions.time_zone
        import blend.blend_core.extensions.tor_check
        import blend.blend_core.extensions.tracker_url_remover
        import blend.blend_core.extensions.unit_converter
    except ImportError:
        pass

from blend.cli import main

if __name__ == '__main__':
    main()
