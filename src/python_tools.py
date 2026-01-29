import shutil, os
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