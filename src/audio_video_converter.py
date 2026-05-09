from pathlib import Path
import subprocess

def webm_to_mp3(input_path):
    input_path = Path(input_path)
    output_path = input_path.with_suffix(".mp3")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-vn",
            "-acodec", "libmp3lame",
            "-ab", "192k",
            str(output_path)
        ],
        check=True
    )

    return output_path


def video_to_wav(input_path, output_suffix=".wav"):
    input_path = Path(input_path)
    output_path = input_path.with_suffix(output_suffix)

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-vn",
            "-acodec", "pcm_s16le",
            str(output_path)
        ],
        check=True,
    )

    return output_path