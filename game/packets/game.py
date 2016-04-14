from . import Packet


class RequestSelectionPacket(Packet):
    def __init__(self, request_id=None, text=None, options=None):
        super().__init__()
        self.request_id = request_id
        self.text = text
        self.options = options


class ReplySelectionPacket(Packet):
    def __init__(self, request_id=None, option_id=None):
        super().__init__()
        self.request_id = request_id
        self.option_id = option_id


class EndTurnPacket(Packet):
    def __init__(self):
        super().__init__()


class EndGamePacket(Packet):
    def __init__(self, winner=None):
        super().__init__()
        self.winner = winner


class PlayCardPacket(Packet):
    def __init__(self, card_id=None):
        super().__init__()
        self.card_id = card_id


class SetCardsPacket(Packet):
    """
    cards[{
        id
        name
        text
        type
        player -- if minion or action
        power -- if minion
        power_threshold -- if base
        award_points { -- if base
            first
            second
            third
        }
    }]
    """
    def __init__(self, cards):
        super().__init__()
        self.cards = cards


class SetGameStatePacket(Packet):
    """
    game_state {
        bases [{
            id
            power_total
            cards {
                id
                power   -- if minion
                actions[action]
            }
        }]
        players [{
            name
            points
            hand_size
            discard[id]
        }]
        turn {
            name
            minions
            actions
        }
        hand[id]
    }
    """
    def __init__(self, game_id=None, bases=None, players=None, turn=None, hand=None):
        super().__init__()
        self.game_id = game_id
        self.bases = bases
        self.players = players
        self.turn = turn
        self.hand = hand
