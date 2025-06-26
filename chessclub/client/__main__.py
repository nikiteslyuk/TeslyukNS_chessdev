"""Client for chess."""
import socket
import pickle
import cmd
import shlex
import sys
import time
import pygame
import os
import chess
import gettext
import locale as loc
import readline

if 'libedit' in readline.__doc__:
    readline.parse_and_bind("bind ^I rl_complete")
else:
    readline.parse_and_bind("tab: complete")

SERVER = "127.0.0.1"
PORT = 5555

locales_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")
LOCALES = {
    "ru_RU.UTF-8": gettext.translation("CHESS", locales_dir, languages=["ru_RU.UTF-8"]),
    "en_US.UTF-8": gettext.NullTranslations(),
}