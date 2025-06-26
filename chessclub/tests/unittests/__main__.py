"""Юнит тестирование."""

import unittest
from unittest.mock import MagicMock, patch

from chessclub.server.__main__ import Player, Table
from chessclub.client.__main__ import (
    get_table_info,
    _,
    ChessCmd,
)

