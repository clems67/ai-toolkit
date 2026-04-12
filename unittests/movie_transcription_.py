import unittest
from src.workflows.movie_transcription import read_str_file_to_json

class TestSubtitleParsing(unittest.TestCase):
    def testSubtitleParsing(self):
        self.expected_output = {
            "segments": [
                {
                    "id": 1392,
                    "start": 8806846,
                    "end": 8811308,
                    "text": "You shall not pass!"
                },
                {
                    "id": 1393,
                    "start": 8838461,
                    "end": 8842339,
                    "text": "BOROMIR: No! No!\n-Gandalf!"
                }
            ]
        }

        result = read_str_file_to_json("unittests/files/str.str")
        self.assertEqual(self.expected_output, result)

if __name__ == '__main__':
    unittest.main()