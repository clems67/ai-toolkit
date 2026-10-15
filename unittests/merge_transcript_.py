import unittest

from speech_to_text import Transcription, SpeechToText


class TestMergeTranscriptTimespan(unittest.TestCase):

    def test_merges_segments_within_timespan(self):
        transcript = [
            Transcription(start="00:00:00", end="00:01:30", text="hello "),
            Transcription(start="00:01:30", end="00:02:30", text="world "),
            Transcription(start="00:02:30", end="00:05:00", text="!"),
            Transcription(start="00:05:00", end="00:05:30", text="!"),
        ]

        result = SpeechToText.merge_transcript_timespan(transcript, minutes=2)

        expected = [
            Transcription(start="00:00:00", end="00:02:30", text="hello world "),
            Transcription(start="00:02:30", end="00:05:00", text="!"),
            Transcription(start="00:05:00", end="00:05:30", text="!"),
        ]
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()