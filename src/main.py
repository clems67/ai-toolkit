import yt_audio_downloader, speech_to_text, config, time_method, bionic_reading, lm_studio

config = config.load_config()

@time_method.timed_decorator("main.py")
def main():
    yt_path = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    filepath = yt_audio_downloader.download_audio(yt_path)
    transcript_path = speech_to_text.transcribe_audio_to_txt(filepath, "en")
    bionic_reading.write(transcript_path)

    with time_method.timed("LLM question"):
        content = open(transcript_path, "r")
        chat = f"Explain me why this text is so much important in today's culture. Explain briefly in a few sentences (10 maximum)."
        chat += f"text: {content}"

        res =lm_studio.chat(chat)
        print(res)

if __name__ == "__main__":
    main()
