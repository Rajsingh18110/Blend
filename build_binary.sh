#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
PY_BIN="${PYTHON_BIN:-/usr/bin/python3}"
BUILD_VENV="${BUILD_VENV_DIR:-.build-venv}"

if [[ ! -x "$PY_BIN" ]]; then
  echo "❌ Shared-library Python is required for PyInstaller."
  echo "   Expected: $PY_BIN"
  echo "   Install a Python built with --enable-shared or use the distro Python."
  exit 1
fi

python_check="$($PY_BIN - <<'PY'
import sysconfig
shared = sysconfig.get_config_var('Py_ENABLE_SHARED')
print('1' if shared else '0')
PY
)"

if [[ "$python_check" != "1" ]]; then
  echo "❌ The selected Python is static-only and PyInstaller cannot build a binary with it."
  echo "   Use a shared-library build, usually the distro Python at /usr/bin/python3."
  exit 2
fi

if [[ ! -d "$BUILD_VENV" ]]; then
  "$PY_BIN" -m venv "$BUILD_VENV"
fi

. "$BUILD_VENV/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install .
python -m pip install pyinstaller

python -m PyInstaller \
  --name blend-linux \
  --onefile \
  --clean \
  --add-data "src/blend/templates:blend/templates" \
  --add-data "src/blend/static:blend/static" \
  --add-data "src/blend/blend_core/assets:blend/blend_core/assets" \
  --add-data "src/blend/blend_core/views:blend/blend_core/views" \
  --add-data "src/blend/blend_core/translations:blend/blend_core/translations" \
  --add-data "src/blend/blend_core/data:blend/blend_core/data" \
  --add-data "src/blend/blend_core/blend_config.yml:blend/blend_core" \
  --add-data "src/blend/blend_core/limiter.toml:blend/blend_core" \
  --add-data "src/blend/blend_core/sources:blend/blend_core/sources" \
  --add-data "src/blend/blend_core/favicons:blend/blend_core/favicons" \
  --collect-all lxml \
  --collect-all blend.blend_core.extensions \
  --collect-all blend.blend_core.sources \
  --hidden-import "cloudscraper" \
  --hidden-import "lxml.etree" \
  --hidden-import "lxml._elementpath" \
  --hidden-import "lxml.html" \
  --hidden-import "flask" \
  --hidden-import "gunicorn.glogging" \
  --hidden-import "gunicorn.workers.sync" \
  --hidden-import "httpx_socks" \
  --hidden-import "valkey" \
  run_blend.py

echo
printf '\n✅ Binary build finished. Artifact: %s\n' "$(pwd)/dist/blend-linux"
