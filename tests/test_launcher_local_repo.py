from pathlib import Path

from blend.launcher import should_use_local_repo


def test_should_use_local_repo_when_checkout_is_present(monkeypatch, tmp_path):
    repo_root = tmp_path / 'Blend'
    (repo_root / 'src' / 'blend').mkdir(parents=True)
    (repo_root / 'src' / 'blend' / '__init__.py').write_text('')

    monkeypatch.setattr('blend.launcher.__file__', str(repo_root / 'src' / 'blend' / 'launcher.py'))
    assert should_use_local_repo() is True


def test_should_use_local_repo_when_not_in_checkout(monkeypatch, tmp_path):
    repo_root = tmp_path / 'other'
    (repo_root / 'src' / 'blend').mkdir(parents=True)
    (repo_root / 'src' / 'blend' / '__init__.py').write_text('')

    monkeypatch.setattr('blend.launcher.__file__', str(tmp_path / 'standalone' / 'launcher.py'))
    assert should_use_local_repo() is False
