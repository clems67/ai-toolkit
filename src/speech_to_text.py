from transformers import VoxtralForConditionalGeneration, AutoProcessor
from pydub import AudioSegment, silence
import torch, librosa, os, json
import config, time_method, python_tools
from collections import deque
from typing import List
from datetime import timedelta

config = config.load_config()
MAX_CHUNK_LEN_MS = config["speech_to_text"]["max_chunk_length_minutes"] * 60 * 1000

def transcribe_audio_to_txt(audio_path: str, info_path:str, language: str = "fr", delete_audio_file: bool = True) -> str:
    device = "cuda"
    repo_id = "mistralai/Voxtral-Mini-3B-2507"
    TARGET_SAMPLE_RATE = 16000

    audio_chunks_paths = split_audio(audio_path, delete_audio_file)
    audio_chunks_lengths = get_audio_chunks_lengths(audio_chunks_paths)

    processor = AutoProcessor.from_pretrained(repo_id)
    model = VoxtralForConditionalGeneration.from_pretrained(repo_id, torch_dtype=torch.bfloat16, device_map=device)

    final_outputs = []
    with time_method.timed("transcribe_audio_to_txt"):
        for i, audio_chunk_path in enumerate(audio_chunks_paths):
            audio, sampling_rate = librosa.load(audio_chunk_path, sr=TARGET_SAMPLE_RATE)

            inputs = processor.apply_transcription_request(language=language, audio=audio, format=["wav"], sampling_rate=TARGET_SAMPLE_RATE, model_id=repo_id)
            inputs = inputs.to(device, dtype=torch.bfloat16)

            outputs = model.generate(**inputs, max_new_tokens=5000)
            decoded_outputs = processor.batch_decode(outputs[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)
            final_outputs.append(decoded_outputs[0])

            #clear
            del audio, inputs, outputs
            torch.cuda.empty_cache()

            print(f"progress: {i + 1} / {len(audio_chunks_paths)} - {int((i + 1) / len(audio_chunks_paths) * 100)}%")

    save_transcription(info_path, audio_chunks_lengths, final_outputs)
    python_tools.delete_folder(os.path.dirname(audio_chunks_paths[0]))

    return info_path

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
    file_name_with_extension = os.path.basename(original_file_name)
    file_name, _ = os.path.splitext(file_name_with_extension)
    path = f"data_process/audio_chunks/{file_name}"
    os.makedirs(path, exist_ok=True)

    paths_to_return = []
    for i, chunk in enumerate(chunks):
        output_path = f"{path}/chunk_{i}.wav"
        chunk.export(output_path, format="wav")
        paths_to_return.append(output_path)

    return paths_to_return

def get_audio_chunks_lengths(chunks: List[str]) -> List[int]:
    res = []
    for chunk in chunks:
        audio = AudioSegment.from_wav(chunk)
        res.append(len(audio) / 1000.0)
    return res

def print_chunks_info(raw_chunks, text):
    if not config['speech_to_text']['details_log']:
        return

    print(text)
    for chunk in raw_chunks:
        seconds = len(chunk) // 1000
        print(f"Writing chunk of duration {str(timedelta(seconds=seconds))} sec to file")

def save_transcription(json_path: str, audio_chunks_lengths: List[int], str_transcription: List[str]):
    with open(json_path, "r") as f:
        data = json.load(f)
        start_length = 0
        for i, chunk_length in enumerate(audio_chunks_lengths):
            to_insert = {
                "start": str(timedelta(seconds=int(start_length))),
                "end": str(timedelta(seconds=int(start_length + chunk_length))),
                "text": str_transcription[i]
            }
            data.setdefault("transcription", []).append(to_insert)
            start_length += chunk_length

    with open(json_path, 'w') as file:
        json.dump(data, file, indent=4)

    path = f"data/normal_reading"
    os.makedirs(path, exist_ok=True)
    clean_file_name = python_tools.clean_file_name(data["title"])
    file_name = f"{path}/{clean_file_name}.txt"
    with open(file_name, 'w', encoding="utf-8") as f:
        f.write(' '.join(str_transcription))