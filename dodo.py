from pathlib import Path
from zipfile import ZipFile
from doit.tools import create_folder
from shutil import rmtree

PODEST = "chessclub/locales"
DOIT_CONFIG = {"default_tasks": ["docs"]}

def task_pot():
    """Re-create .pot ."""
    return {
        "actions": [f"pybabel extract -o CHESS.pot chessclub"],
        "file_dep": [*Path(".").glob("*.py")],
        "targets": ["CHESS.pot"],
    }
