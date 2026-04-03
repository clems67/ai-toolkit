from pydub import AudioSegment, silence
import os
import config, time_method, python_tools
from collections import deque
from typing import List
from datetime import timedelta
from pathlib import Path
from python_tools import clean_file_name

config = config.load_config()
MAX_CHUNK_LEN_MS = config["speech_to_text"]["max_chunk_length_minutes"] * 60 * 1000

@time_method.timed_decorator("split_audio")
def split_audio(audio_path: str, delete_audio_file: bool) -> List[str]:
    MIN_SILENCE_LEN = 700  # ms
    SILENCE_THRESH = -40  # dBFS
    KEEP_SILENCE = 800  # ms

    audio = AudioSegment.from_file(audio_path)

    initial_chunks = silence.split_on_silence(
        audio,
        min_silence_len=MIN_SILENCE_LEN,
        silence_thresh=SILENCE_THRESH,
        keep_silence=KEEP_SILENCE,
    )
    print_chunks_info(initial_chunks, f"Silence detection has split audio into {len(initial_chunks)} chunks")

    split_chunks = split_too_big_chunks(initial_chunks)
    print_chunks_info(split_chunks, f"Splitting too big chunks, now there is : {len(split_chunks)} chunks")

    merged_chunks = merge_too_small_chunks(split_chunks)
    print_chunks_info(merged_chunks, f"Merging too small chunks, now there is : {len(merged_chunks)} chunks")

    if delete_audio_file:
        os.remove(audio_path)

    return save_chunks_as_wav(merged_chunks, audio_path)

def split_too_big_chunks(initial_chunks):
    to_process = deque(initial_chunks)  # BIG queue that will shrink
    result = deque()  # EMPTY queue that will grow

    while to_process:
        chunk = to_process.popleft()

        if len(chunk) > MAX_CHUNK_LEN_MS:
            nb_divide = len(chunk) // MAX_CHUNK_LEN_MS + 1
            sub_length = len(chunk) // nb_divide
            for i in range(0, len(chunk), sub_length):
                sub = chunk[i: i + sub_length]
                to_process.append(sub)
        else:
            result.append(chunk)
    return result

def merge_too_small_chunks(result):
    final_result = deque()
    buffer = AudioSegment.empty()

    while result:
        chunk = result.popleft()

        if len(buffer) + len(chunk) < MAX_CHUNK_LEN_MS:
            buffer += chunk
        else:
            if len(buffer) > 0:
                final_result.append(buffer)
            buffer = chunk

    final_result.append(buffer)
    return final_result

def save_chunks_as_wav(chunks, original_file_name:str) -> List[str]:
    file_name = Path(original_file_name).stem
    file_name = clean_file_name(file_name)
    path = Path("data_process") / "audio_chunks" / file_name
    os.makedirs(path, exist_ok=True)

    paths_to_return = []
    for i, chunk in enumerate(chunks):
        output_path = Path(path) / f"chunk_{i}.wav"
        chunk.export(output_path, format="wav")
        paths_to_return.append(output_path)

    return paths_to_return

def print_chunks_info(raw_chunks, text):
    if config['speech_to_text']['details_log']:
        print(text)
        for chunk in raw_chunks:
            seconds = len(chunk) // 1000
            print(f"Writing chunk of duration {str(timedelta(seconds=seconds))} sec to file")