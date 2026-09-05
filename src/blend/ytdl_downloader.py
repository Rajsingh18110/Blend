# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Raj Singh / Markanm Team

# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
import yt_dlp
import os
import shutil
import sys


def _ffmpeg_available():
    return shutil.which("ffmpeg") is not None


def _quality_height_cap(quality):
    return {
        "4k": 2160,
        "1080p": 1080,
        "720p": 720,
        "360p": 360,
    }.get((quality or "best").lower())


def normalize_download_quality(quality):
    """Normalize frontend/backend aliases to supported yt-dlp quality values."""
    q = (quality or "best").strip().lower().replace(" ", "")
    aliases = {
        "audio": "audio",
        "mp3": "audio",
        "music": "audio",
        "bestaudio": "audio",
        "audioonly": "audio",
        "video": "best",
        "mp4": "best",
        "bestvideo": "best",
    }
    return aliases.get(q, q)


def _build_download_options(quality, output_dir, file_id):
    quality = normalize_download_quality(quality)
    ffmpeg_available = _ffmpeg_available()

    ydl_opts = {
        'outtmpl': os.path.join(output_dir, f'%(title)s_{file_id}.%(ext)s'),
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
    }

    if quality == "audio":
        ydl_opts['format'] = 'bestaudio/best'
        if ffmpeg_available:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '0',
            }]
        return ydl_opts

    if ffmpeg_available:
        if quality == "4k":
            ydl_opts['format'] = 'bestvideo[height<=2160]+bestaudio/best'
            ydl_opts['merge_output_format'] = 'mp4'
        elif quality == "1080p":
            ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best'
            ydl_opts['merge_output_format'] = 'mp4'
        elif quality == "720p":
            ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best'
            ydl_opts['merge_output_format'] = 'mp4'
        elif quality == "360p":
            ydl_opts['format'] = 'best[height<=360]/bestvideo[height<=360]+bestaudio/best'
            ydl_opts['merge_output_format'] = 'mp4'
        else:
            ydl_opts['format'] = 'best/bestvideo+bestaudio'
            ydl_opts['merge_output_format'] = 'mp4'
        return ydl_opts

    # ffmpeg is unavailable, so only select formats that are already muxed
    # (video + audio in a single file). This keeps downloads working instead
    # of failing during the merge/post-processing step.
    height_cap = _quality_height_cap(quality)
    if height_cap:
        ydl_opts['format'] = (
            f'best[height<={height_cap}][vcodec!=none][acodec!=none]'
            f'/best[vcodec!=none][acodec!=none]'
        )
    else:
        ydl_opts['format'] = (
            'best[vcodec!=none][acodec!=none]'
        )
    return ydl_opts


def _resolve_download_path(output_dir, file_id, info, ydl):
    candidates = []

    def add_candidate(path):
        if isinstance(path, str) and path and path not in candidates:
            candidates.append(path)

    add_candidate(info.get('filepath'))
    add_candidate(info.get('_filename'))

    try:
        add_candidate(ydl.prepare_filename(info))
    except Exception:
        pass

    for requested in info.get('requested_downloads') or []:
        if isinstance(requested, dict):
            add_candidate(requested.get('filepath'))
            add_candidate(requested.get('_filename'))
            add_candidate(requested.get('filename'))

    for requested in info.get('requested_formats') or []:
        if isinstance(requested, dict):
            add_candidate(requested.get('filepath'))
            add_candidate(requested.get('_filename'))

    for path in candidates:
        if path and os.path.exists(path) and not path.endswith(('.part', '.ytdl')):
            return path

    if os.path.isdir(output_dir):
        matching_files = []
        for name in os.listdir(output_dir):
            if file_id in name and not name.endswith(('.part', '.ytdl')):
                path = os.path.join(output_dir, name)
                if os.path.isfile(path):
                    matching_files.append(path)

        if matching_files:
            matching_files.sort(key=os.path.getmtime, reverse=True)
            return matching_files[0]

    return None


def get_stream_info(url):
    """
    Extract real playable stream URLs from a YouTube video (or any yt-dlp supported URL).
    Returns metadata + multiple format streams for direct HTML5 <video> playback.
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'skip_download': True,
        'listformats': False,
        'geo_bypass': True,
        'nocheckcertificate': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Build streams list
        streams = []
        best_audio_url = None
        best_audio_tbr = -1

        all_formats = info.get('formats', [])

        for f in all_formats:
            furl = f.get('url', '')
            if not furl:
                continue
            ext = f.get('ext', '').lower()
            height = f.get('height') or 0
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            has_video = vcodec != 'none'
            has_audio = acodec != 'none'
            mime = (f.get('mime_type') or f.get('mime') or '').lower()

            stream_entry = {
                'url': furl,
                'ext': ext,
                'height': height,
                'label': f'{height}p' if height else 'auto',
                'type': 'combined' if has_video and has_audio else 'audio' if has_audio and not has_video else 'video',
                'filesize': f.get('filesize'),
                'tbr': f.get('tbr'),
                'mime': mime,
            }

            # Prefer real combined streams for video playback.
            if has_video and has_audio and ext in ('mp4', 'webm'):
                streams.append(stream_entry)

            # Track the strongest audio-only stream for music playback/downloads.
            if has_audio and not has_video and ext in ('m4a', 'mp4', 'webm', 'opus'):
                tbr = f.get('tbr') or 0
                if tbr > best_audio_tbr or (tbr == best_audio_tbr and best_audio_url is None):
                    best_audio_url = furl
                    best_audio_tbr = tbr

        # Sort streams by quality descending
        streams.sort(key=lambda x: x.get('height', 0), reverse=True)

        # If no combined streams, try the 'url' field directly (some formats give single URL)
        if not streams:
            direct_url = info.get('url')
            if direct_url:
                vcodec = info.get('vcodec', 'none')
                acodec = info.get('acodec', 'none')
                has_video = vcodec != 'none'
                has_audio = acodec != 'none'
                direct_type = 'combined' if has_video and has_audio else 'audio' if has_audio and not has_video else 'video'
                streams.append({
                    'url': direct_url,
                    'ext': info.get('ext', 'mp4'),
                    'height': info.get('height', 0),
                    'label': 'best',
                    'type': direct_type,
                    'mime': (info.get('mime_type') or info.get('mime') or '').lower(),
                })

        # If we have an audio-only stream and no video stream, make it available as the best stream.
        if not streams and best_audio_url:
            streams.append({
                'url': best_audio_url,
                'ext': 'm4a',
                'height': 0,
                'label': 'audio',
                'type': 'audio',
                'mime': 'audio/mp4',
            })

        # Format duration
        dur_sec = info.get('duration') or 0
        mins, secs = divmod(int(dur_sec), 60)
        hrs, mins = divmod(mins, 60)
        if hrs:
            duration_str = f'{hrs}:{mins:02d}:{secs:02d}'
        else:
            duration_str = f'{mins}:{secs:02d}'

        # Format views
        views = info.get('view_count') or 0
        if views >= 1_000_000:
            views_str = f'{round(views/1_000_000, 1)}M'
        elif views >= 1000:
            views_str = f'{round(views/1000, 1)}K'
        else:
            views_str = str(views)

        # Upload date
        upload_raw = info.get('upload_date') or ''
        if len(upload_raw) == 8:
            upload_date = f"{upload_raw[6:8]}/{upload_raw[4:6]}/{upload_raw[:4]}"
        else:
            upload_date = upload_raw

        # Determine whether available streams contain any video track
        has_video_stream = False
        for s in streams:
            if s.get('type') in ('combined', 'video', 'direct'):
                has_video_stream = True
                break

        has_any_video_track = any((f.get('vcodec', 'none') or 'none') != 'none' for f in all_formats)
        needs_muxing = has_any_video_track and not has_video_stream
        is_audio_only = not has_any_video_track

        # Best combined stream (video+audio) if available
        best_combined = None
        for s in streams:
            if s.get('type') == 'combined' and s.get('url'):
                best_combined = s.get('url')
                break

        best_stream_mime = None
        if streams:
            best_stream_mime = streams[0].get('mime') or streams[0].get('mime_type')
        else:
            best_stream_mime = (info.get('mime_type') or info.get('mime') or '').lower()

        return {
            'success': True,
            'title': info.get('title', ''),
            'thumbnail': info.get('thumbnail', ''),
            'duration': duration_str,
            'duration_sec': dur_sec,
            'views': views_str,
            'channel': info.get('channel') or info.get('uploader', ''),
            'channel_url': info.get('channel_url') or info.get('uploader_url', ''),
            'upload_date': upload_date,
            'description': (info.get('description') or '')[:300],
            'streams': streams,
            'audio_url': best_audio_url,
            'best_stream': streams[0]['url'] if streams else None,
            'best_combined_stream': best_combined,
            'best_stream_mime': best_stream_mime,
            'is_audio_only': bool(is_audio_only),
            'needs_muxing': needs_muxing,
            'video_id': info.get('id', ''),
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def download_video(url, quality="best"):
    import tempfile
    import uuid
    output_dir = os.path.join(tempfile.gettempdir(), "blend_downloads")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_id = str(uuid.uuid4())[:8]
    ydl_opts = _build_download_options(quality, output_dir, file_id)
    # Normalize requested quality and build a fallback chain so we don't
    # abort immediately when a specific format isn't available for a video.
    q_norm = normalize_download_quality(quality)

    # Build fallback order: prefer requested quality, then more permissive options.
    fallbacks = []
    if q_norm in ("4k", "1080p", "720p", "360p"):
        fallbacks = [q_norm, "best", "720p", "360p", "best"]
    elif q_norm == "audio":
        fallbacks = ["audio", "best"]
    else:
        fallbacks = [q_norm, "best"]

    last_exc = None
    attempted = []
    for attempt_q in fallbacks:
        if attempt_q in attempted:
            continue
        attempted.append(attempt_q)
        ydl_opts = _build_download_options(attempt_q, output_dir, file_id)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = _resolve_download_path(output_dir, file_id, info, ydl)
                if not file_path:
                    # No output file; try next fallback
                    print(f"yt-dlp finished but no output file found for quality='{attempt_q}'")
                    last_exc = RuntimeError(
                        f"yt-dlp finished but no output file was found for quality='{attempt_q}'.")
                    continue
                return file_path
        except Exception as e:
            # Common yt-dlp message when a format is missing includes
            # 'Requested format is not available' — we should retry with
            # looser format selection instead of failing hard.
            print(f"Download attempt failed (quality={attempt_q}): {e}")
            last_exc = e
            # Continue to next fallback
            continue

    # If we reach here, all fallbacks failed — raise a helpful error.
    msg = (
        f"Download failed: tried qualities {attempted}. "
        "If this persists, run yt-dlp with --list-formats to inspect available formats, "
        "or try a different quality (e.g., '720p' or 'best')."
    )
    if last_exc:
        msg = msg + f" Last error: {str(last_exc)}"
    raise RuntimeError(msg)


def search_youtube(query, max_results=15):
    """
    Search YouTube using yt-dlp and return structured metadata.
    """
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
    }

    results = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch{max_results}:{query}"
            info = ydl.extract_info(search_query, download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    if not entry:
                        continue
                    duration_sec = entry.get('duration') or 0
                    mins, secs = divmod(duration_sec, 60)
                    duration_str = f"{int(mins)}:{int(secs):02d}" if duration_sec > 0 else ""

                    views = entry.get('view_count') or 0
                    if views > 1_000_000:
                        views_str = f"{round(views/1_000_000, 1)}M"
                    elif views > 1000:
                        views_str = f"{round(views/1000, 1)}K"
                    else:
                        views_str = str(views)

                    vid_id = entry.get('id', '')
                    results.append({
                        'title': entry.get('title'),
                        'url': f"https://www.youtube.com/watch?v={vid_id}" if vid_id else entry.get('url'),
                        'thumbnail': entry.get('thumbnail') or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                        'author': entry.get('uploader') or entry.get('channel', ''),
                        'duration': duration_str,
                        'views': views_str,
                        'id': vid_id,
                    })
    except Exception as e:
        print(f"YouTube search error: {e}")

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 ytdl_downloader.py <URL> [quality]")
        sys.exit(1)
    url = sys.argv[1]
    quality = sys.argv[2] if len(sys.argv) > 2 else "best"
    try:
        print(download_video(url, quality))
    except Exception as exc:
        print(f"Download failed: {exc}")
        sys.exit(1)
