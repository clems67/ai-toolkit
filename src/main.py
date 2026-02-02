import yt_audio_downloader, speech_to_text, config, time_method, bionic_reading
import lmstudio as lms

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

        lms.configure_default_client(config["lm_studio"]["server_api_host"])
        response = lms.llm().respond(chat, config={
            "temperature": 0.7,
            "maxTokens": 500,
        })
        print(response)


if __name__ == "__main__":
    main()
