import python_tools
import json, os
from dataclasses import dataclass
from typing import List

@dataclass
class Transcription:
    start: str
    end: str
    text: str

    def to_dict(self):
        return {
            'start': self.start,
            'end': self.end,
            'text': self.text
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            start=data['start'],
            end=data['end'],
            text=data['text']
        )

class SpeechToText:
    def __init__(self):
        super().__init__()
        self.transcript = []

    def save_transcription(self, json_path: str):
        transcription_data = [segment.to_dict() for segment in self.transcript]

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("transcription", transcription_data)

        with open(json_path, 'w', encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        path = f"data/normal_reading"
        os.makedirs(path, exist_ok=True)
        clean_file_name = python_tools.clean_file_name(data["title"])
        file_name = f"{path}/{clean_file_name}.txt"
        with open(file_name, 'w', encoding="utf-8") as f:
            full_text = ' '.join([segment.text for segment in self.transcript])
            f.write(full_text)

    def merge_transcript_timespan(self, minutes: int) -> List[Transcription]:
        window_seconds = minutes * 60
        merged: List[Transcription] = []
        block_start_seconds = 0.0

        for segment in self.transcript:
            segment_start_seconds = python_tools.time_str_to_seconds(segment.start)

            if not merged or segment_start_seconds >= block_start_seconds + window_seconds:
                # Start a new block anchored at this segment's start time
                merged.append(Transcription(start=segment.start, end=segment.end, text=segment.text))
                block_start_seconds = segment_start_seconds
            else:
                # Extend the current block
                current = merged[-1]
                current.end = segment.end
                current.text += segment.text

        self.transcript = merged
        return merged
