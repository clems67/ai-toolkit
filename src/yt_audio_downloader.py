from yt_dlp import YoutubeDL
import time_method

@time_method.timed_decorator("download_audio")
def download_audio(url: str) -> str:
    options = {
        "format": "bestaudio/best",
        "outtmpl": "audios/%(title)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav"
            }
        ],
    }

    with YoutubeDL(options) as ydl:
        ydl.download([url])
        info = ydl.extract_info(url, download=True)
        filepath = info["requested_downloads"][0]["filepath"]

    return filepath
