import os
from logging import getLogger

log = getLogger(__name__)


def is_file_exists(folder_path: str, file_name: str) -> bool:
    file_path = os.path.join(folder_path, file_name)
    return os.path.isfile(file_path)


def is_dir_exists(folder_path: str) -> bool:
    return os.path.isdir(folder_path)


def create_directory_if_doesnt_exists(output_folder: str):
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder, exist_ok=True)
        log.info(f"Directory {output_folder} created successfully.")


def get_absolute_path_from_current_dir(path: str = None) -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if path:
        return os.path.join(current_dir, path)
    else:
        return current_dir
