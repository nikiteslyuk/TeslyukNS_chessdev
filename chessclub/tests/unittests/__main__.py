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

    def test_table_creation_and_usage(self):
        """Table корректно хранит состояние игроков, зрителей и активных игроков."""
        t = Table(42)

        self.assertEqual(t.id, 42)
        self.assertIsNone(t.white)
        self.assertIsNone(t.black)
        self.assertEqual(t.spectators, [])
        self.assertEqual(t.active_players, set())

        t.white, t.black = "vasya", "petya"
        self.assertEqual((t.white, t.black), ("vasya", "petya"))

        t.spectators.append("spec1")
        self.assertIn("spec1", t.spectators)

        t.active_players.update({"vasya", "petya"})
        self.assertSetEqual(t.active_players, {"vasya", "petya"})