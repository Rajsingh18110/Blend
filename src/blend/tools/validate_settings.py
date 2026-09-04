#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Raj Singh / Markanm Team

# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
import sys
import yaml
from pathlib import Path


def validate_settings(path: Path) -> int:
    print(f"Validating: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    except Exception as e:
        print("YAML parse error:", e)
        return 2

    engines = data.get('engines')
    if engines is None:
        print("No 'engines' key found.")
        return 1
    if not isinstance(engines, list):
        print("'engines' is not a list (type=", type(engines), ")")
        return 2

    names = set()
    errors = 0
    for i, e in enumerate(engines, start=1):
        if not isinstance(e, dict):
            print(f"Entry #{i} is not a mapping: {type(e)} -> {e}")
            errors += 1
            continue
        for k in list(e.keys()):
            if not isinstance(k, str):
                print(f"Entry #{i} has non-string key: {k} (type {type(k)})")
                errors += 1
        name = e.get('name')
        if not name:
            print(f"Entry #{i} missing 'name': {e}")
            errors += 1
        else:
            if not isinstance(name, str):
                print(f"Entry #{i} 'name' is not a string: {name} ({type(name)})")
                errors += 1
            else:
                if name in names:
                    print(f"Duplicate engine name: {name} (first seen earlier)")
                    errors += 1
                names.add(name)

        about = e.get('about')
        if about is not None and not isinstance(about, dict):
            print(f"Entry #{i} 'about' is not a mapping: {about} ({type(about)})")
            errors += 1

    if errors:
        print(f"Validation finished: {errors} errors found.")
        return 3
    print(f"Validation finished: OK ({len(engines)} engines).")
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: validate_settings.py <blend_config.yml>")
        raise SystemExit(1)
    path = Path(sys.argv[1])
    if not path.exists():
        print("File does not exist:", path)
        raise SystemExit(2)
    raise SystemExit(validate_settings(path))
