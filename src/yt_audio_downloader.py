from yt_dlp import YoutubeDL
import time_method
import json

@time_method.timed_decorator("download_audio")
def download_audio(url: str) -> str:
    options = {
        "format": "bestaudio/best",
        "outtmpl": "./data/audios/%(title)s.%(ext)s",
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
        keys_to_keep = ["title", "fulltitle", "description", "duration", "duration_string", "categories", "tags", "chapters", "channel"]
        filtered_data = {key: info[key] for key in keys_to_keep if key in info}

        audio_path = info["requested_downloads"][0]["filepath"]

    return (audio_path, str(filtered_data))
