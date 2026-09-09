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

# Only modify sys.path when running from source (not frozen). Rely on
# PyInstaller's import machinery when frozen instead of inserting/appending
# _MEIPASS into sys.path which can hide the PYZ importer and break imports.
if not getattr(sys, 'frozen', False):
    src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
    if src_path and src_path not in sys.path:
        sys.path.insert(0, src_path)

# Debug helper: when frozen and BLEND_DEBUG=1, write environment and extracted files
if getattr(sys, 'frozen', False) and os.environ.get('BLEND_DEBUG') == '1':
    try:
        with open('/tmp/blend_start_debug.txt', 'w') as f:
            f.write(f"frozen={getattr(sys, 'frozen', False)}\n")
            f.write(f"_MEIPASS={getattr(sys, '_MEIPASS', None)}\n")
            f.write(f"_MEIPASS2={getattr(sys, '_MEIPASS2', None)}\n")
            f.write('sys.path:\n')
            for p in sys.path:
                f.write(p + '\n')
            meipass = getattr(sys, '_MEIPASS', None) or getattr(sys, '_MEIPASS2', None)
            if meipass and os.path.isdir(meipass):
                f.write('\nmeipass listing:\n')
                for root, dirs, files in os.walk(meipass):
                    f.write(root + '\n')
                    for d in dirs:
                        f.write('  dir: ' + d + '\n')
                    for fi in files[:50]:
                        f.write('  file: ' + fi + '\n')
    except Exception:
        pass

from blend.cli import main

if __name__ == '__main__':
    main()
