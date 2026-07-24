from faster_whisper import WhisperModel
from typing import List
import python_tools
from speech_to_text import SpeechToText, Transcription


class SpeechToText_Whisper(SpeechToText):
    def __init__(self):
        super().__init__()

    def transcribe_audio(self, audio_path: str) -> List[Transcription]:

        model_size = "large-v3-turbo"

        model = WhisperModel(model_size, compute_type="int8", device="cpu")

        segments, info = model.transcribe(audio_path, beam_size=10)

        print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

        result = []
        for segment in segments:
            transcript_chunk = Transcription(
                start = python_tools.seconds_to_time_str(segment.start),
                end = python_tools.seconds_to_time_str(segment.end),
                text = str(segment.text)
            )
            result.append(transcript_chunk)

        self.transcript = result
        return result