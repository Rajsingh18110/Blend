from blend.ytdl_downloader import normalize_download_quality


def test_normalize_download_quality_handles_audio_aliases():
    assert normalize_download_quality('audio') == 'audio'
    assert normalize_download_quality('bestaudio') == 'audio'
    assert normalize_download_quality('MP3') == 'audio'
    assert normalize_download_quality('best') == 'best'
    assert normalize_download_quality('1080p') == '1080p'
