from blend.cli import parse_code_install_args


def test_parse_code_install_args_accepts_all_variants():
    assert parse_code_install_args(['all']).all is True
    assert parse_code_install_args(['--all']).all is True
    assert parse_code_install_args(['-all']).all is True
    assert parse_code_install_args([]).all is True
    assert parse_code_install_args(['clone']).all is False
