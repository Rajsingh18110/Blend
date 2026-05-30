# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Raj Singh / Markanm Team

# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
"""Local API key configuration for Blend Search."""

from __future__ import annotations

import os


def get_active_api_config() -> dict | None:
    """Get the full config dictionary of the currently active API."""
    import json
    from pathlib import Path
    config_path = Path(__file__).resolve().parent / "admin_config.json"
    
    try:
        if config_path.exists():
            config = json.loads(config_path.read_text())
            for api in config.get("apis", []):
                if api.get("active"):
                    return api
    except Exception as e:
        print(f"Error reading admin_config.json: {e}")
    return None

def get_navar_api_key() -> str:
    """Read the active Navar API key from admin config, fallback to environment."""
    cfg = get_active_api_config()
    if cfg and cfg.get("api_key"):
        return cfg.get("api_key", "").strip()
    return os.environ.get("NAVAR_API_KEY", "").strip()

def get_global_config() -> dict:
    """Return the entire admin_config.json as a dict."""
    import json
    from pathlib import Path
    config_path = Path(__file__).resolve().parent / "admin_config.json"
    try:
        if config_path.exists():
            return json.loads(config_path.read_text())
    except Exception:
        pass
    return {}
