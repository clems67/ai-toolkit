import re

def read_str_file_to_json(file_path):
    """
    Reads a .str subtitle file from the given path, parses it using parse_subtitles(),
    and returns the result as JSON.

    Args:
        file_path (str): Path to the .str subtitle file

    Returns:
        dict: Parsed subtitles in JSON format
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            subtitle_str = file.read()
        return parse_subtitles(subtitle_str)
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {file_path} was not found")
    except Exception as e:
        raise Exception(f"An error occurred while reading the file: {str(e)}")

def parse_subtitles(subtitle_str):
    """
    Parses a string containing subtitles in .str format and converts it to a structured JSON format.

    Args:
        subtitle_str (str): A string containing subtitles in .str format.

    Returns:
        dict: A dictionary with the following structure:
            {
                "segments": [
                    {
                        "id": int,
                        "start": int,     # milliseconds
                        "end": int,       # milliseconds
                        "text": str
                    }
                ]
            }
    """
    segments = []
    lines = subtitle_str.strip().split('\n')

    i = 0
    while i < len(lines):
        # Get segment ID (first line)
        if not lines[i].strip():
            i += 1
            continue

        try:
            segment_id = int(lines[i])
        except ValueError:
            i += 1
            continue

        i += 1

        if i >= len(lines):
            break

        time_match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})', lines[i])
        if not time_match:
            i += 1
            continue

        # Parse start and end times
        start_h, start_m, start_s, start_ms = map(int, time_match.groups()[:4])
        end_h, end_m, end_s, end_ms = map(int, time_match.groups()[4:])

        start_ms_total = (start_h * 3600 + start_m * 60 + start_s) * 1000 + start_ms
        end_ms_total = (end_h * 3600 + end_m * 60 + end_s) * 1000 + end_ms

        i += 1

        # Get all text lines until next segment ID or empty line
        text_lines = []
        while i < len(lines):
            if not lines[i].strip() or (lines[i].strip().isdigit() and int(lines[i]) != segment_id):
                break
            text_lines.append(lines[i])
            i += 1

        text = '\n'.join(text_lines)

        segments.append({
            "id": segment_id,
            "start": start_ms_total,
            "end": end_ms_total,
            "text": text.strip()
        })

    return {"segments": segments}
