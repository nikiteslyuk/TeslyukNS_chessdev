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

    def test_get_table_info(self):
        """get_table_info возвращает нужную запись стола или None."""
        fake_sock = MagicMock()

        with patch("chessclub.client.__main__.send_recv") as mock_send_recv:
            mock_send_recv.return_value = {
                "data": [
                    {"id": 1, "white": "a", "black": "b"},
                    {"id": 2, "white": None, "black": "c"},
                ]
            }

            self.assertEqual(get_table_info(fake_sock, 1)["id"], 1)
            self.assertIsNone(get_table_info(fake_sock, 99))

    def test_complete_createtable_space_then_tab(self):
        """После 'createtable ' (с пробелом) автодополнение предлагает 'as'."""
        with patch("chessclub.client.__main__.send_recv") as mock_send_recv:
            mock_send_recv.return_value = {"status": "ok", "msg": "ok"}

            cmd = ChessCmd("petya", sock=MagicMock())

            options = cmd.complete_createtable("", "createtable ", 12, 13)

            self.assertEqual(options, ["as"])

    def test_on_leave_resets_state_and_sends_leave(self):
        """on_leave очищает current_table/current_color и шлёт action 'leave'."""
        with patch("chessclub.client.__main__.send_recv") as mock_send_recv:
            mock_send_recv.return_value = {"status": "ok", "msg": "ok"}
            sock_mock = MagicMock()

            cmd = ChessCmd("masha", sock=sock_mock)
            cmd.current_table, cmd.current_color = 7, "white"

            cmd.on_leave()
            self.assertIsNone(cmd.current_table)
            self.assertIsNone(cmd.current_color)

            mock_send_recv.assert_called_with(
                sock_mock,
                {
                    "action": "leave",
                    "table_id": 7,
                    "color": "white",
                    "user": "masha",
                },
            )


if __name__ == "__main__":
    unittest.main()
