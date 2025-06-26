"""Юнит тестирование."""

import unittest
from unittest.mock import MagicMock, patch

from chessclub.server.__main__ import Player, Table
from chessclub.client.__main__ import (
    get_table_info,
    _,
    ChessCmd,
)


class TestChessProject(unittest.TestCase):
    """Набор юнит тестов."""

    def test_player_creation(self):
        """Player хранит имя, переданное в конструкторе."""
        p = Player("Vasya")
        self.assertEqual(p.name, "Vasya")