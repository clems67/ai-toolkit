from transformers import VoxtralForConditionalGeneration, AutoProcessor
from pydub import AudioSegment, silence
import torch, librosa, os
import config, time_method, python_tools
from collections import deque
from typing import List

config = config.load_config()
MAX_CHUNK_LEN_MS = config["speech_to_text"]["max_chunk_length_minutes"] * 60 * 1000

def transcribe_audio_to_txt(audio_path: str, language: str = "fr", delete_audio_file: bool = True) -> str:
    device = "cuda"
    repo_id = "mistralai/Voxtral-Mini-3B-2507"
    TARGET_SAMPLE_RATE = 16000

    audio_chunks_paths = split_audio(audio_path, delete_audio_file)

    processor = AutoProcessor.from_pretrained(repo_id)
    model = VoxtralForConditionalGeneration.from_pretrained(repo_id, torch_dtype=torch.bfloat16, device_map=device)

    with time_method.timed("transcribe_audio_to_txt"):
        for audio_chunk_path in audio_chunks_paths:
            audio, sampling_rate = librosa.load(audio_chunk_path, sr=TARGET_SAMPLE_RATE)

            inputs = processor.apply_transcription_request(language=language, audio=audio, format=["wav"], sampling_rate=TARGET_SAMPLE_RATE, model_id=repo_id)
            inputs = inputs.to(device, dtype=torch.bfloat16)

            outputs = model.generate(**inputs, max_new_tokens=5000)
            decoded_outputs = processor.batch_decode(outputs[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)

            output_path = save_transcription(audio_path, decoded_outputs)

            #clear
            del audio, inputs, outputs
            torch.cuda.empty_cache()

    python_tools.delete_folder(os.path.dirname(audio_chunks_paths[0]))

    return output_path

@time_method.timed_decorator("split_audio")
def split_audio(audio_path: str, delete_audio_file: bool) -> List[str]:
    MIN_SILENCE_LEN = 700  # ms
    SILENCE_THRESH = -40  # dBFS
    KEEP_SILENCE = 800  # ms

    OUTPUT_DIR = "./data/audio_chunks"
    audio = AudioSegment.from_file(audio_path)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    path = f"./data/audio_chunks/{file_name}"
    os.makedirs(path, exist_ok=True)

    paths_to_return = []
    for i, chunk in enumerate(chunks):
        output_path = f"{path}/chunk_{i}.wav"
        chunk.export(output_path, format="wav")
        paths_to_return.append(output_path)

    return paths_to_return

def print_chunks_info(raw_chunks, text):
    if not config['speech_to_text']['details_log']:
        return

    print(text)
    for chunk in raw_chunks:
        seconds = len(chunk) // 1000  # Convert milliseconds to seconds
        minutes = seconds // 60  # Get the minutes
        remaining_seconds = seconds % 60  # Get the remaining seconds
        print(f"Writing chunk of length {minutes} min {remaining_seconds} sec to file")

def save_transcription(audio_path, decoded_outputs) -> str:
    transcriptions_path = "./data/transcriptions"
    os.makedirs(transcriptions_path, exist_ok=True)

    audio_filename = os.path.splitext(os.path.basename(audio_path))[0]
    output_path = os.path.join(transcriptions_path, f"{audio_filename}.txt")

    with open(output_path, "a", encoding="utf-8") as f:
        for decoded_output in decoded_outputs:
            f.write(decoded_output.strip())
    return output_path