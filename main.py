import converter, yt_audio_downloader, speech_to_text, config

config = config.load_config()

def main():
    yt_path = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    filepath = yt_audio_downloader.download_audio(yt_path)
    speech_to_text.transcribe_audio_to_txt(filepath, "en")

if __name__ == "__main__":
    main()
