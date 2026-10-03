import os
import sys
from pathlib import Path


def should_use_local_repo():
    try:
        current_file = Path(__file__).resolve()
        repo_root = current_file.parents[2]
        candidate = repo_root / 'src' / 'blend' / '__init__.py'
        return candidate.exists() and candidate.is_file()
    except Exception:
        return False


def main():
    """Compatibility shim for older launchers.

    Blend is source-first and no longer downloads or executes standalone binaries.
    This shim simply routes to the source CLI when running from a checkout and
    otherwise falls back to the installed package entry point.
    """
    if should_use_local_repo():
        repo_root = Path(__file__).resolve().parents[2]
        src_dir = repo_root / 'src'
        env = os.environ.copy()
        env['PYTHONPATH'] = str(src_dir) + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
        os.execvpe(sys.executable, [sys.executable, '-m', 'blend.cli', *sys.argv[1:]], env)

    from blend.cli import main as cli_main
    cli_main()


if __name__ == '__main__':
    main()
