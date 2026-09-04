# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Raj Singh / Markanm Team

# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
"""Blend webapp entrypoint that wraps the underlying search runtime."""

from blend.blend_core.webapp import app, init, run


@app.after_request
def add_cors_headers(response):
    response.headers.setdefault("Access-Control-Allow-Origin", "*")
    response.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE")
    response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Admin-Token")
    return response


@app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def blend_options_handler(path=""):
    return "", 204

__all__ = ["app", "init", "run"]


if __name__ == "__main__":
    run()
