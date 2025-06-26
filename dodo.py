from pathlib import Path
from zipfile import ZipFile
from doit.tools import create_folder
from shutil import rmtree

PODEST = "chessclub/locales"
DOIT_CONFIG = {"default_tasks": ["docs"]}