from . import Packet


class AuthPacket(Packet):
    def __init__(self, name=None):
        super().__init__()
        self.name = name


class JoinGamePacket(Packet):
    def __init__(self, game_id=None):
        self.game_id = game_id
