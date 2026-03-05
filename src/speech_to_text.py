from transformers import VoxtralForConditionalGeneration, AutoProcessor
from pydub import AudioSegment
import torch, librosa, os, json
import time_method, python_tools, split_audio
from typing import List
from datetime import timedelta
from colorama import Fore, Style

def transcribe_audio(audio_path: str, info_path:str, language: str = "fr", delete_audio_file: bool = True) -> str:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print(Fore.YELLOW + "WARNING, running on cpu")
        print(Style.RESET_ALL)
    repo_id = "mistralai/Voxtral-Mini-3B-2507"
    TARGET_SAMPLE_RATE = 16000

    audio_chunks_paths = split_audio.split_audio(audio_path, delete_audio_file)
    audio_chunks_lengths = get_audio_chunks_lengths(audio_chunks_paths)

    processor = AutoProcessor.from_pretrained(repo_id)
    model = VoxtralForConditionalGeneration.from_pretrained(repo_id, torch_dtype=torch.bfloat16, device_map="auto").to(device)

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

def get_audio_chunks_lengths(chunks: List[str]) -> List[int]:
    res = []
    for chunk in chunks:
        audio = AudioSegment.from_wav(chunk)
        res.append(len(audio) / 1000.0)
    return res

def save_transcription(json_path: str, audio_chunks_lengths: List[int], str_transcription: List[str]):
    with open(json_path, "r", encoding="utf-8") as f:
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

    with open(json_path, 'w', encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    path = f"data/normal_reading"
    os.makedirs(path, exist_ok=True)
    clean_file_name = python_tools.clean_file_name(data["title"])
    file_name = f"{path}/{clean_file_name}.txt"
    with open(file_name, 'w', encoding="utf-8") as f:
        f.write(' '.join(str_transcription))