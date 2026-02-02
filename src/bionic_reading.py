import bionic_writer, os

def write(path: str):
    content = open(path, "r").read()
    bionic_md = bionic_writer.write(content, affix="**", postfix="**")

    file_name_with_extension = os.path.basename(path)
    file_name, _ = os.path.splitext(file_name_with_extension)
    folder_name = "bionic_reading"
    os.makedirs(folder_name, exist_ok=True)
    with open(f"{folder_name}/{file_name}.md", "w", encoding="utf-8") as f:
        f.write(bionic_md)