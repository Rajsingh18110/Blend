"""Blend Search Package"""

try:
	# provide a stable `__version__` attribute expected by the CLI
	from .blend_core import version as _version  # type: ignore
	__version__ = getattr(_version, "VERSION_STRING", "1.0.0")
except Exception:
	__version__ = "1.0.0"
