"""Server for chess."""

import asyncio
import pickle
import chess

HOST = "0.0.0.0"
PORT = 5555

class ChessServer:
    """Class for handling interaction between players and table management."""

    def __init__(self):
        """Init class."""
        self.users = {}
        self.tables = {}
        self.table_id_seq = 1
        self.lock = asyncio.Lock()

    async def handle(self, reader, writer):
        """Handle requests from clients."""
        user = None
        try:
            while True:
                data_len_bytes = await reader.readexactly(4)
                data_len = int.from_bytes(data_len_bytes, "big")
                data = await reader.readexactly(data_len)
                cmd = pickle.loads(data)
                resp = {"status": "ok", "msg": None, "data": None}

                if cmd["action"] == "register":
                    name = cmd["name"]
                    async with self.lock:
                        if name in self.users:
                            resp["status"] = "err"
                            resp["msg"] = "Name taken"
                        else:
                            self.users[name] = Player(name)
                            resp["msg"] = f"Welcome, {name}"
                            user = name

                out_data = pickle.dumps(resp)
                writer.write(len(out_data).to_bytes(4, "big"))
                writer.write(out_data)
                await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionResetError):
            pass
        finally:
            if user is not None:
                async with self.lock:
                    if user in self.users:
                        del self.users[user]
            writer.close()
            await writer.wait_closed()


async def main():
    """Run async server."""
    server = ChessServer()

    async def handle_conn(reader, writer):
        await server.handle(reader, writer)

    srv = await asyncio.start_server(handle_conn, HOST, PORT)
    print(f"Async server listening on {HOST}:{PORT}")
    async with srv:
        await srv.serve_forever()

if __name__ == "__main__":
    """Run application."""
    asyncio.run(main())
