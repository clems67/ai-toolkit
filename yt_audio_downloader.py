from yt_dlp import YoutubeDL
import time_method

def download_audio(url: str) -> str:
    with time_method.timed("download_audio"):
        options = {
            "format": "bestaudio/best",
            "outtmpl": "audios/%(title)s.%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        with YoutubeDL(options) as ydl:
            ydl.download([url])
            info = ydl.extract_info(url, download=True)
            filepath = info["requested_downloads"][0]["filepath"]

    return filepath
