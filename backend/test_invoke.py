import urllib.parse
from flask import Flask, request, jsonify
from blend.webapp import app

@app.route("/api/test_invoke")
def test_invoke():
    # Simulate adding format=json to the request args
    from blend_server import search
    
    # We must patch the request context args temporarily? No, request.args is immutable.
    # Flask allows modifying request.args by modifying request.environ['QUERY_STRING']? No.
    return "ok"

