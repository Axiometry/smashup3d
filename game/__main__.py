from server import LocalServer
from game import Game, GameConfig
import threading
import decks.dinosaurs
import packets.server


class CustomServer(LocalServer):
    def __init__(self, port):
        super().__init__(port)

        self._connected_users_lock = threading.Lock()
        self._connected_users = {}

    def on_user_connect(self, user, conn):
        print('user connected: ' + user.name)
        super().on_user_connect(user, conn)
        self._connected_users_lock.acquire()
        try:
            self._connected_users[user] = conn
            if len(self._connected_users) == 1:
                dino_deck = decks.dinosaurs.DinosaursDeck()
                config = GameConfig(list(self._connected_users.keys()), [dino_deck]*10)
                game = self.create_game(config)
                for user in self._connected_users:
                    game.add_connection(user, self._connected_users[user])
                    self._connected_users[user].send_packet(packets.server.JoinGamePacket(game.id))
                game.start()
        finally:
            self._connected_users_lock.release()


print('starting server...')
server = CustomServer(25565)
server.start()

