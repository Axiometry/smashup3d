import threading
from game import LocalGame
from queue import Queue, Empty
from websocket import AsyncioWebSocketServer
import packets
import packets.server
from user import User


class Server:
    def start(self):
        raise NotImplementedError

    def get_user(self, name):
        raise NotImplementedError

    def create_user(self, name):
        raise NotImplementedError

    def create_game(self, config):
        raise NotImplementedError

    def remove_game(self, game):
        raise NotImplementedError

    def get_game(self, game_id):
        raise NotImplementedError

    def get_games_by_user(self, user):
        raise NotImplementedError

    def handle_packet(self, connection, packet):
        raise NotImplementedError


class LocalServer(Server, threading.Thread):
    def __init__(self, port):
        super().__init__()
        self.port = port
        self._users_by_name = {}
        self._users_lock = threading.RLock()
        self._games_by_id = {}
        self._games_lock = threading.RLock()
        self._game_id_counter = 0
        self._server = AsyncioWebSocketServer(port, self._accept_connection)

    def start(self):
        self._server.start()

    def get_user(self, name):
        self._users_lock.acquire()
        try:
            if name in self._users_by_name:
                return self._users_by_name[name]
            return None
        finally:
            self._users_lock.release()

    def create_user(self, name):
        self._users_lock.acquire()
        try:
            if name not in self._users_by_name:
                user = User(name)
                self._users_by_name[name] = user
            return self._users_by_name[name]
        finally:
            self._users_lock.release()

    def _accept_connection(self, send_packet, close_connection):
        conn = LocalConnection(self, send_packet, close_connection)

        conn.deserializer.register(packets.server.AuthPacket, 'auth')
        conn.serializer.register(packets.server.JoinGamePacket, 'join_game')

        return conn.on_open, conn.on_message, conn.on_close

    def on_user_connect(self, user, conn):
        pass

    def on_user_disconnect(self, user, conn):
        pass

    def create_game(self, config):
        self._games_lock.acquire()
        try:
            self._game_id_counter += 1
            game = LocalGame(self._game_id_counter, config)
            self._games_by_id[game.id] = game
        finally:
            self._games_lock.release()
        return game

    def remove_game(self, game):
        self._games_lock.acquire()
        try:
            del self._games_by_id[game.id]
        finally:
            self._games_lock.release()

    def get_game(self, game_id):
        self._games_lock.acquire()
        try:
            return self._games_by_id[game_id]
        finally:
            self._games_lock.release()

    def get_games_by_user(self, user):
        games = []
        self._games_lock.acquire()
        try:
            for game_id in self._games_by_id:
                game = self._games_by_id[game_id]
                if user in game.users:
                    games.append(game)
        finally:
            self._games_lock.release()
        return games

    def handle_packet(self, connection, packet):
        print('[Server] Received packet ' + packet.__class__.__name__)
        if connection.user is None:
            if isinstance(packet, packets.server.AuthPacket):
                connection.user = self.create_user(packet.name)
                self.on_user_connect(connection.user, connection)
        else:
            for game in self.get_games_by_user(connection.user):
                if game.has_connection(connection.user, connection):
                    game.receive_packet(connection.user, connection, packet)

    def handle_close(self, connection):
        if connection.user is not None:
            self.on_user_disconnect(connection.user, connection)


class LocalConnection:
    def __init__(self, server, send_message, close_connection):
        self.server = server
        self.serializer = packets.PacketSerializer()
        self.deserializer = packets.PacketSerializer()
        self._send_message = send_message
        self.close_connection = close_connection
        self.user = None

    def send_packet(self, packet):
        message = self.serializer.serialize(packet)
        self._send_message(message)

    def on_open(self):
        pass

    def on_message(self, message):
        packet = self.deserializer.deserialize(message)
        self.server.handle_packet(self, packet)

    def on_close(self):
        self.server.handle_close(self)
