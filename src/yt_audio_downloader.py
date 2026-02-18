from yt_dlp import YoutubeDL
import time_method, os, python_tools
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
        keys_to_keep = ["title", "fulltitle", "description", "duration_string", "categories", "tags", "chapters", "channel"]
        filtered_data = {key: info[key] for key in keys_to_keep if key in info}
        cleaned_data = {k: v for k, v in filtered_data.items() if v is not None}

        folder_name = "./data/transcriptions"
        os.makedirs(folder_name, exist_ok=True)

        title = str(cleaned_data["title"])
        clean_file_name = python_tools.clean_file_name(title)
        json_path = f"{folder_name}/{clean_file_name}.json"
        
        with open(json_path, 'w') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=4)

        audio_path = str(info["requested_downloads"][0]["filepath"])

    return (audio_path, json_path)