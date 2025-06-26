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


# разкомментировать в случае экстренной инициализации перевода
def task_po():
    """Init translations."""
    return {
        "actions": [f"pybabel init -D CHESS -d {PODEST} -l ru_RU.UTF-8 -i CHESS.pot"],
        "file_dep": ["CHESS.pot"],
        "targets": [f"CHESS.po"],
    }


# def task_po():
#     """Update translations."""
#     return {
#         "actions": [f"pybabel update -D CHESS -d {PODEST} -l ru_RU.UTF-8 -i CHESS.pot"],
#         "file_dep": ["CHESS.pot"],
#         "targets": [f"CHESS.po"],
#     }