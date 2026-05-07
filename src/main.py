import yt_downloader, speech_to_text, config, time_method, bionic_reading, lm_studio
from enums import Language
from colorama import Fore, Style

config = config.load_config()

yt_path = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
language = Language.ENGLISH
prompt = """
Explain me why this text is so much important in today's culture.
Explain briefly in a few sentences (10 maximum).
"""
temperature = 0.7
max_output_tokens = 200

@time_method.timed_decorator("main.py")
def main():
    (audio_path, result_path) = yt_downloader.download_audio(yt_path)

    transcript = speech_to_text.transcribe_audio(audio_path, language, delete_audio_file=True)
    speech_to_text.save_transcription(result_path, transcript)

    bionic_reading.write(result_path)

    content = open(result_path, "r").readlines()

    chat = f"<ROLE> You are an assistant that analyzes YouTube videos. </ROLE>"
    chat += f"<TASK> {prompt} </TASK>"
    chat += f"<BEGIN_TRANSCRIPT> {content} </END_TRANSCRIPT>"

    res = lm_studio.chat(chat, structured_response=None, temperature = temperature, max_tokens= max_output_tokens)

    print(Fore.GREEN + "LLM response :")
    print(Style.RESET_ALL)
    print(res)


if __name__ == "__main__":
    main()
