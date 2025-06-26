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

def play_game_pygame(
    table_id, sock, my_color=None, flip_board=False, quit_callback=None, username=None, locale="ru_RU.UTF-8"
):
    """Make fonts and images."""
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    FIGDIR = os.path.join(BASE_DIR, "figures")
    SQ, FPS = 96, 60
    COL_L, COL_D = (240, 217, 181), (181, 136, 99)
    CLR_LAST, CLR_MOVE, CLR_CAP, CLR_CHK = (
        (0, 120, 215, 120),
        (255, 255, 0, 120),
        (255, 0, 0, 120),
        (200, 0, 0, 150),
    )
    MASK_MATE, MASK_PATT = (200, 0, 0, 130), (128, 128, 128, 130)
    ANIM_FRAMES = 12
    TOP_MARGIN = 40
    BOTTOM_MARGIN = 40

    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode((SQ * 8, TOP_MARGIN + SQ * 8 + BOTTOM_MARGIN))
    pygame.display.set_caption(f"Table {table_id}")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 48)
    label_font = pygame.font.SysFont(None, 40)
    font_big = pygame.font.SysFont(None, 64)
    font_small = pygame.font.SysFont(None, 32)

    MAP = {
        chess.PAWN: "p",
        chess.KNIGHT: "kn",
        chess.BISHOP: "b",
        chess.ROOK: "r",
        chess.QUEEN: "q",
        chess.KING: "k",
    }
    SPR = {}
    for col, prefix in ((chess.WHITE, "w"), (chess.BLACK, "b")):
        for pt, s in MAP.items():
            path = os.path.join(FIGDIR, f"{prefix}{s}.png")
            SPR[(col, pt)] = pygame.transform.smoothscale(
                pygame.image.load(path).convert_alpha(), (SQ, SQ)
            )

    def surf(color):
        """Color surface of chess board."""
        s = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
        s.fill(color)
        return s

    S_LAST, S_MOVE, S_CAP, S_CHK = map(surf, (CLR_LAST, CLR_MOVE, CLR_CAP, CLR_CHK))

    def sq_center(sq):
        """Measure square center."""
        f = chess.square_file(sq)
        r = chess.square_rank(sq)
        r = r if flip_board else 7 - r
        return f * SQ + SQ // 2, r * SQ + SQ // 2 + TOP_MARGIN

    def mouse_sq(x, y):
        """Position mouse."""
        y_on_board = y - TOP_MARGIN
        if y_on_board < 0 or y_on_board >= SQ * 8:
            return None
        f = x // SQ
        r = y_on_board // SQ
        board_r = r if flip_board else 7 - r
        if 0 <= f < 8 and 0 <= board_r < 8:
            return chess.square(f, board_r)
        return None

    class Anim:
        """Animate with pygame."""

        def __init__(self, ptype, col, start, target, orig):
            """Init class."""
            self.ptype, self.col, self.pos = ptype, col, start
            self.start, self.target, self.orig, self.f = start, target, orig, 0

        def tick(self):
            """Tick frames."""
            self.f += 1
            t = min(1, self.f / ANIM_FRAMES)
            ease = 1 - (1 - t) * (1 - t)
            self.pos = (
                self.start[0] + (self.target[0] - self.start[0]) * ease,
                self.start[1] + (self.target[1] - self.start[1]) * ease,
            )
            return t >= 1

    class PromoMenu:
        """Class for pawn promotion menu."""

        def __init__(self, col, to_sq):
            """Init class."""
            self.col = col
            self.opts = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
            w = h = SQ
            pad = 12
            H = h * 4 + pad * 3
            f, r = chess.square_file(to_sq), chess.square_rank(to_sq)
            r_p = r if flip_board else 7 - r
            x = f * SQ
            y = (
                r_p * SQ + SQ + TOP_MARGIN
                if r_p * SQ + SQ + H + TOP_MARGIN <= TOP_MARGIN + SQ * 8
                else r_p * SQ + TOP_MARGIN - H
            )
            self.rects = []
            self.top = (x, y)
            self.surf = pygame.Surface((w, H), pygame.SRCALPHA)
            self.surf.fill((30, 30, 30, 230))
            for i, pt in enumerate(self.opts):
                self.surf.blit(SPR[(col, pt)], (0, i * (h + pad)))
                self.rects.append(pygame.Rect(x, y + i * (h + pad), w, h))

        def draw(self):
            """Blit images."""
            screen.blit(self.surf, self.top)

        def click(self, p):
            """Find colision with board rects."""
            for r, pt in zip(self.rects, self.opts):
                if r.collidepoint(p):
                    return pt
            return None

    def send_move(move):
        """Send move of chess piece."""
        uci = move.uci()
        send_recv(sock, {"action": "move", "table_id": table_id, "uci": uci})

       def draw_labels(table_info):
        """Draw names of players."""
        if table_info:
            white = table_info.get("white", "")
            black = table_info.get("black", "")
            active_players = set(table_info.get("active_players", []))
        else:
            white = "White"
            black = "Black"
            active_players = set()

        if not white or white not in active_players:
            white_label = _("Ожидание белых", locale)
        else:
            white_label = white

        if not black or black not in active_players:
            black_label = _("Ожидание чёрных", locale)
        else:
            black_label = black

        if my_color == "white":
            my_name = username if username else white_label
            opp_name = black_label if black_label != my_name else _("Ожидание чёрных", locale)
        elif my_color == "black":
            my_name = username if username else black_label
            opp_name = white_label if white_label != my_name else _("Ожидание белых", locale)
        else:
            my_name = white_label
            opp_name = black_label

        if flip_board:
            bottom_label = my_name
            top_label = opp_name
        else:
            bottom_label = my_name if my_color != "black" else opp_name
            top_label = opp_name if my_color != "black" else my_name

        if top_label:
            top_text = label_font.render(str(top_label), True, (0, 0, 0))
            top_rect = top_text.get_rect(center=(SQ * 4, TOP_MARGIN // 2))
            screen.blit(top_text, top_rect)
        if bottom_label:
            bottom_text = label_font.render(str(bottom_label), True, (0, 0, 0))
            bottom_rect = bottom_text.get_rect(
                center=(SQ * 4, TOP_MARGIN + SQ * 8 + BOTTOM_MARGIN // 2)
            )
            screen.blit(bottom_text, bottom_rect)

    resp = send_recv(sock, {"action": "get_board", "table_id": table_id})
    if resp["status"] != "ok":
        print(_("Ошибка: нет такой партии!", locale))
        pygame.quit()
        return

    board = chess.Board(resp["data"])
    drag_sq = drag_pos = None
    legal_sqs, capture_sqs = set(), set()
    last = None
    anims = []
    pending = None
    promo = None
    game_over = False

    my_is_white = my_color == "white"
    my_is_black = my_color == "black"
    my_is_player = my_is_white or my_is_black

    POLL_INTERVAL = 0.3
    last_poll = 0
    pending_fen = None

    has_left_table = False
    left_table_time = None

    if board.is_checkmate() or board.is_stalemate():
        game_over = True

    running = True
    while running:
        dt = clock.tick(FPS)
        now = time.time()

        for e in pygame.event.get():
            if e.type == pygame.QUIT or (
                e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE
            ):
                has_left_table = True
                left_table_time = time.time()
                if quit_callback:
                    quit_callback()
                break

            if has_left_table:
                if e.type in [pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN]:
                    running = False
                    break
                continue

            if game_over:
                continue

            if promo:
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    ptype = promo.click(e.pos)
                    if ptype:
                        push_move = chess.Move(
                            pending.from_square, pending.to_square, promotion=ptype
                        )
                        board.push(push_move)
                        last = push_move
                        promo = None
                        send_move(push_move)
                        pending = None
                        if board.is_checkmate() or board.is_stalemate():
                            game_over = True
                continue
            if anims:
                continue
            if my_is_player and (
                (board.turn and my_is_white) or (not board.turn and my_is_black)
            ):
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    sq = mouse_sq(*e.pos)
                    if (
                        sq is not None
                        and board.piece_at(sq)
                        and board.piece_at(sq).color == board.turn
                    ):
                        drag_sq, drag_pos = sq, e.pos
                        legal_sqs, capture_sqs = set(), set()
                        for mv in board.legal_moves:
                            if mv.from_square == sq:
                                if board.piece_at(mv.to_square):
                                    capture_sqs.add(mv.to_square)
                                elif (
                                    board.piece_at(sq).piece_type == chess.PAWN
                                    and board.ep_square is not None
                                    and mv.to_square == board.ep_square
                                ):
                                    capture_sqs.add(mv.to_square)
                                else:
                                    legal_sqs.add(mv.to_square)

                elif e.type == pygame.MOUSEMOTION and (drag_sq is not None):
                    drag_pos = e.pos
                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and (drag_sq is not None):
                    dst = mouse_sq(*e.pos)
                    mv = None
                    for m in board.legal_moves:
                        if m.from_square == drag_sq and m.to_square == dst:
                            mv = m
                            break
                    start = (drag_pos[0] - SQ // 2, drag_pos[1] - SQ // 2)
                    tgt = (
                        (sq_center(dst)[0] - SQ // 2, sq_center(dst)[1] - SQ // 2)
                        if mv
                        else (
                            sq_center(drag_sq)[0] - SQ // 2,
                            sq_center(drag_sq)[1] - SQ // 2,
                        )
                    )
                    anims.append(
                        Anim(
                            board.piece_at(drag_sq).piece_type,
                            board.turn,
                            start,
                            tgt,
                            drag_sq,
                        )
                    )
                    if mv and board.is_castling(mv):
                        rf, rt = (
                            (7, 5) if chess.square_file(mv.to_square) == 6 else (0, 3)
                        )
                        rf, rt = chess.square(
                            rf, chess.square_rank(mv.to_square)
                        ), chess.square(rt, chess.square_rank(mv.to_square))
                        rs, rtg = sq_center(rf), sq_center(rt)
                        rook = board.piece_at(rf)
                        anims.append(
                            Anim(
                                rook.piece_type,
                                rook.color,
                                (rs[0] - SQ // 2, rs[1] - SQ // 2),
                                (rtg[0] - SQ // 2, rtg[1] - SQ // 2),
                                rf,
                            )
                        )
                    pending = mv
                    drag_sq = drag_pos = None
                    legal_sqs.clear()
                    capture_sqs.clear()

        if has_left_table:
            screen.fill((0, 0, 0))
            text = font_big.render(_("Вы покинули стол", locale), True, (255, 255, 255))
            rect = text.get_rect(center=(SQ * 4, TOP_MARGIN + SQ * 4))
            screen.blit(text, rect)
            msg = font_small.render(
                _("Для продолжения вернитесь в терминал", locale), True, (200, 200, 200)
            )