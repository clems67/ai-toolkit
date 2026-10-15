from faster_whisper import WhisperModel
from typing import List
import python_tools
from speech_to_text import SpeechToText, Transcription


class SpeechToText_Whisper(SpeechToText):
    def __init__(self):
        super().__init__()

    def transcribe_audio(self, audio_path: str, quantization_int8=False) -> List[Transcription]:
        model_size = "large-v3-turbo"
        quantization = "int8" if quantization_int8 else "float16"

        model = WhisperModel(model_size, compute_type=quantization, device="auto")

        segments, info = model.transcribe(audio_path, beam_size=10)

        print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

        result = []
        for i, segment in enumerate(segments):
            transcript_chunk = Transcription(
                start=python_tools.seconds_to_time_str(segment.start),
                end=python_tools.seconds_to_time_str(segment.end),
                text=str(segment.text)
            )
            result.append(transcript_chunk)
            print(f"{python_tools.seconds_to_time_str(segment.end)} de l'audio été traité")

        self.transcript = result
        return result
