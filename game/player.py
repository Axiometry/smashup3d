from pile import Pile


class Player(object):
    def __init__(self, user, game):
        self.user = user
        self.game = game
        self.deck = Pile()
        self.decks = []
        self.hand = []
        self.discard = []
        self.points = 0

    def end_game(self, game):
        pass


class LocalPlayer(Player):
    def __init__(self, user, game):
        super().__init__(user, game)
        self._connections = []

    def send_packet(self, packet):
        for conn in self._connections:
            conn.send_packet(packet)

    def add_connection(self, connection):
        self._connections.append(connection)

    def remove_connection(self, connection):
        self._connections.remove(connection)

    def has_connection(self, connection):
        return connection in self._connections