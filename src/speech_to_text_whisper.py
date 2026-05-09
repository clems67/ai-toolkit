from faster_whisper import WhisperModel
from typing import List
import python_tools
from speech_to_text_voxtral import save_transcription as save_transcription_voxtral

def transcribe_audio(audio_path: str) -> List[dict]:

    model_size = "large-v3-turbo"

    model = WhisperModel(model_size, compute_type="float16")

    segments, info = model.transcribe(audio_path, beam_size=10)

    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

    result = []
    for segment in segments:
        result.append({
            "start": python_tools.seconds_to_time_str(segment.start),
            "end": python_tools.seconds_to_time_str(segment.end),
            "text": str(segment.text)
        })
        
    return result

def save_transcription(json_path: str, transcript: List[dict]):
    save_transcription_voxtral(json_path, transcript)