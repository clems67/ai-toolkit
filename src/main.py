import yt_downloader, speech_to_text, config, time_method, bionic_reading, lm_studio
from colorama import Fore, Style

config = config.load_config()

yt_path = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
language = "en"
prompt = """
Explain me why this text is so much important in today's culture.
Explain briefly in a few sentences (10 maximum).
"""
temperature = 0.7
max_output_tokens = 200

@time_method.timed_decorator("main.py")
def main():
    (audio_path, information_path) = yt_downloader.download_audio(yt_path)

    transcript_path = speech_to_text.transcribe_audio_to_txt(audio_path, information_path, language, delete_audio_file=True)

    bionic_reading.write(transcript_path)

    content = open(transcript_path, "r").readlines()

    chat = f"<ROLE> You are an assistant that analyzes YouTube videos. </ROLE>"
    chat += f"<TASK> {prompt} </TASK>"
    chat += f"<BEGIN_TRANSCRIPT> {content} </END_TRANSCRIPT>"

    res = lm_studio.chat(chat, temperature, max_output_tokens)

    print(Fore.GREEN + "LLM response :")
    print(Style.RESET_ALL)
    print(res)


if __name__ == "__main__":
    main()
