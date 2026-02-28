import bionic_writer, os, json
from colorama import Fore, Style

def write(path: str):
    content = open(path, "r").read()
    json_data = json.loads(content)
    merged_text = " ".join(item["text"] for item in json_data["transcription"])
    bionic_md = bionic_writer.write(merged_text, affix="**", postfix="**")

    file_name_with_extension = os.path.basename(path)
    file_name, _ = os.path.splitext(file_name_with_extension)
    folder_name = "data/bionic_reading"
    os.makedirs(folder_name, exist_ok=True)
    file_destination_path = f"{folder_name}/{file_name}.md"
    with open(file_destination_path, "w", encoding="utf-8") as f:
        f.write(bionic_md)
    
    print(Fore.BLUE + f"Transcript in bionic reading style has been saved here : " + Style.RESET_ALL + file_destination_path)