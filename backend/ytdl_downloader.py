# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Raj Singh / Markanm Team

# -----------------------------------------------
# Blend Engine — by Markanm Team
# https://markanm.com
# -----------------------------------------------
import yt_dlp
import os
import sys


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
        'extractor_args': {'youtube': ['player_client=android']},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Build streams list
        streams = []
        best_video_url = None
        best_audio_url = None

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

            # Collect combined streams (has both video + audio)
            if has_video and has_audio and ext in ('mp4', 'webm'):
                streams.append({
                    'url': furl,
                    'ext': ext,
                    'height': height,
                    'label': f'{height}p' if height else 'auto',
                    'type': 'combined',
                    'filesize': f.get('filesize'),
                    'tbr': f.get('tbr'),
                })
            # Track best audio-only
            if has_audio and not has_video and ext in ('m4a', 'mp4', 'webm', 'opus'):
                if best_audio_url is None:
                    best_audio_url = furl

        # Sort streams by quality descending
        streams.sort(key=lambda x: x.get('height', 0), reverse=True)

        # If no combined streams, try the 'url' field directly (some formats give single URL)
        if not streams:
            direct_url = info.get('url')
            if direct_url:
                streams.append({
                    'url': direct_url,
                    'ext': info.get('ext', 'mp4'),
                    'height': info.get('height', 0),
                    'label': 'best',
                    'type': 'direct',
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
            'video_id': info.get('id', ''),
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def download_video(url, quality="best", output_dir="downloads"):
    """
    Smart Downloader using yt-dlp.
    Allows downloading in best quality, 1080p, 720p, or Audio only.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'quiet': True,
    }

    if quality == "audio":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif quality == "4k":
        ydl_opts['format'] = 'bestvideo[height<=2160]+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'
    elif quality == "1440p":
        ydl_opts['format'] = 'bestvideo[height<=1440]+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'
    elif quality == "1080p":
        ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'
    elif quality == "720p":
        ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'
    elif quality == "360p":
        ydl_opts['format'] = 'bestvideo[height<=360]+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"Download error: {e}")
        return False


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
        'extractor_args': {'youtube': ['player_client=android']},
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
    download_video(url, quality)
