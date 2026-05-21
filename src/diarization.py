import torch, os
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook
from typing import List

def main(wav_path:str) -> List[dict]:
    # Community-1 open-source speaker diarization pipeline
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-community-1",
        token=os.environ['HUGGINGFACE_ACCESS_TOKEN']
    )

    # send pipeline to GPU (when available)
    pipeline.to(torch.device("cuda"))

    # apply pretrained pipeline (with optional progress hook)
    with ProgressHook() as hook:
        output = pipeline(wav_path, hook=hook)  # runs locally

    result: List[dict] = []
    for turn, speaker in output.speaker_diarization:
        if turn.end - turn.start > 1:
            if result and result[-1]["speaker"] == speaker:
                result[-1]["end"] = turn.end
            else:
                result.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker,
                })
    return result