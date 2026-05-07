from transformers import VoxtralForConditionalGeneration, AutoProcessor
from pydub import AudioSegment
import torch, librosa, os, json, time
import time_method, python_tools, split_audio
from typing import List
from datetime import timedelta
from colorama import Fore, Style
from enums import Language

def transcribe_audio(audio_path: str, language: Language, delete_audio_file: bool = True, max_chunk_length_min: int = 0) -> List[dict]:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print(Fore.YELLOW + "WARNING, running on cpu")
        print(Style.RESET_ALL)
    repo_id = "mistralai/Voxtral-Mini-3B-2507"
    TARGET_SAMPLE_RATE = 16000

    audio_chunks_paths = split_audio.split_audio(audio_path, delete_audio_file, max_chunk_length_min)

    processor = AutoProcessor.from_pretrained(repo_id)
    model = VoxtralForConditionalGeneration.from_pretrained(repo_id, torch_dtype=torch.bfloat16, device_map="auto").to(device)

    transcription = []

    start_time = 0
    with time_method.timed("transcribe_audio_to_txt"):
        for i, audio_chunk_path in enumerate(audio_chunks_paths):
            audio, sampling_rate = librosa.load(audio_chunk_path, sr=TARGET_SAMPLE_RATE)

            inputs = processor.apply_transcription_request(language=language.value, audio=audio, format=["wav"], sampling_rate=TARGET_SAMPLE_RATE, model_id=repo_id)
            inputs = inputs.to(device, dtype=torch.bfloat16)

            outputs = model.generate(**inputs, max_new_tokens=5000)
            decoded_outputs = processor.batch_decode(outputs[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)

            #clear
            del audio, inputs, outputs
            torch.cuda.empty_cache()

            audio = AudioSegment.from_wav(audio_chunks_paths[i])
            end_time = len(audio) / 1000.0
            transcription.append({
                "start": str(timedelta(seconds=int(start_time))),
                "end": str(timedelta(seconds=int(end_time))),
                "text": decoded_outputs[0]
            })
            start_time = end_time

            print(f"{time.strftime('%H:%M:%S')}: progress: {i + 1} / {len(audio_chunks_paths)} - {int((i + 1) / len(audio_chunks_paths) * 100)}%")

    python_tools.delete_folder(os.path.dirname(audio_chunks_paths[0]))

    return transcription

def save_transcription(json_path: str, transcript: List[dict]):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        data.setdefault("transcription", transcript)

    with open(json_path, 'w', encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    path = f"data/normal_reading"
    os.makedirs(path, exist_ok=True)
    clean_file_name = python_tools.clean_file_name(data["title"])
    file_name = f"{path}/{clean_file_name}.txt"
    with open(file_name, 'w', encoding="utf-8") as f:
        full_text = ' '.join([segment['text'] for segment in transcript])
        f.write(full_text)