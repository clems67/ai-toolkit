from yt_dlp import YoutubeDL
import time_method, os
import json

@time_method.timed_decorator("download_audio")
def download_audio(url: str) -> (str, str):
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

        folder_name = "./data/transcriptions"
        os.makedirs(folder_name, exist_ok=True)
        title = str(filtered_data["title"])
        json_path = f"{folder_name}/{title}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=4)

        audio_path = str(info["requested_downloads"][0]["filepath"])

    return (audio_path, json_path)