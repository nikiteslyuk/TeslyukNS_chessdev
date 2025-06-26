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

def _(text, locale):
    """Return translated text."""
    return LOCALES[locale].gettext(text)


def send_recv(sock, data):
    """Sends pickle payload to receive response from server."""
    payload = pickle.dumps(data)
    sock.sendall(len(payload).to_bytes(4, "big") + payload)
    resp_len_bytes = sock.recv(4)
    if not resp_len_bytes:
        raise ConnectionError("Server disconnected")
    resp_len = int.from_bytes(resp_len_bytes, "big")
    resp_data = b""
    while len(resp_data) < resp_len:
        chunk = sock.recv(resp_len - len(resp_data))
        if not chunk:
            raise ConnectionError("Server disconnected")
        resp_data += chunk
    return pickle.loads(resp_data)


def get_table_info(sock, table_id):
    """Get table list and print info."""
    resp = send_recv(sock, {"action": "list_tables"})
    for t in resp["data"]:
        if t["id"] == table_id:
            return t
    return None
