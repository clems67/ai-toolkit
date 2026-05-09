from faster_whisper import WhisperModel
import yt_downloader

def main(audio_path: str):

    model_size = "large-v3-turbo"

    model = WhisperModel(model_size, compute_type="float16")

    segments, info = model.transcribe(audio_path, beam_size=10)

    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

    for segment in segments:
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))