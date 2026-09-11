import builtins
import socket

from blend.cli import get_backend_port, get_blend_version, find_available_port


def test_default_backend_port_is_5000(monkeypatch):
    monkeypatch.delenv('BLEND_PORT', raising=False)
    assert get_backend_port() == 5000


def test_backend_port_respects_env_override(monkeypatch):
    monkeypatch.setenv('BLEND_PORT', '8081')
    assert get_backend_port() == 8081


def test_find_available_port_skips_busy_ports():
    used_port = 65534
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', used_port))
    sock.listen(1)
    try:
        port = find_available_port(start_port=used_port, max_attempts=5)
        assert port != used_port
        assert port > used_port
    finally:
        sock.close()


def test_get_blend_version_falls_back_when_package_missing_version(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == 'blend':
            raise ImportError('simulated missing version metadata')
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', fake_import)
    assert get_blend_version() == 'unknown'
