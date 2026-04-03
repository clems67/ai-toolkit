import shutil, os, re
from colorama import Fore, Style

def delete_folder(folder_path):
    """
    Deletes a folder and all its contents.

    :param folder_path: Path to the folder to be deleted.
    """
    if os.path.exists(folder_path):
        try:
            shutil.rmtree(folder_path)
        except Exception as e:
            print(f"An error occurred while deleting the folder: {e}")
    else:
        print(Fore.RED + f"Folder '{folder_path}' does not exist.")
        print(Style.RESET_ALL)

def clean_file_name(file_name: str) -> str:
    # Replace invalid characters with "-"
    name = re.sub(r'[<>:"/\\|?*]', '-', file_name)

    # Collapse multiple dashes
    name = re.sub(r'-+', '-', name)

    # Trim spaces and dots (Windows restriction)
    name = name.strip(' .')

    # Avoid reserved Windows names
    reserved = {
        "CON","PRN","AUX","NUL",
        *(f"COM{i}" for i in range(1,10)),
        *(f"LPT{i}" for i in range(1,10)),
    }
    if name.upper() in reserved:
        name = f"_{name}"

    # Limit length (safe margin)
    return name[:100] or "file"