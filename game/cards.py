import intents


class CardState(object):
    pass


class InPlayState(CardState):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner


class OnBaseState(InPlayState):
    def __init__(self, owner, base):
        super().__init__(owner)
        self.base = base


class OnMinionState(InPlayState):
    def __init__(self, owner, minion):
        super().__init__(owner)
        self.minion = minion


class MinionOnBaseState(OnBaseState):
    def __init__(self, owner, base, power):
        super().__init__(owner, base)
        self.raw_power = power
        self.actions = []

    @property
    def power(self):
        if self.raw_power <= 0:
            return 0
        return self.raw_power


class ActionOnBaseState(OnBaseState):
    def __init__(self, owner, base):
        super().__init__(owner, base)


class ActionOnMinionState(OnMinionState):
    def __init__(self, owner, minion):
        super().__init__(owner, minion)


class InHandState(CardState):
    pass


class InDeckState(CardState):
    pass


class InDiscardState(CardState):
    pass


class BaseInPlayState(CardState):
    def __init__(self, power_threshold):
        super().__init__()
        self.actions = []
        self.minions = []
        self.power_threshold = power_threshold

    @property
    def power(self):
        return sum([m.power for m in self.minions])


class BaseInDeckState(CardState):
    def __init__(self):
        super().__init__()


class BaseInDiscardState(CardState):
    def __init__(self):
        super().__init__()


class Card(intents.IntentConsumer):
    def __init__(self, id, game, name, text):
        self.id = id
        self.game = game
        self.name = name
        self.text = text
        self.state = None

    def get_intent_list(self):
        return []

    def get_intent_handlers(self, intent):
        return {}


class BaseCard(Card):
    def __init__(self, id, game, name, text, power_threshold, award_points):
        super().__init__(id, game, name, text)
        self.power_threshold = power_threshold
        self.award_points = award_points


class MinionCard(Card):
    def __init__(self, id, player, name, text, power):
        super().__init__(id, player.game, name, text)
        self.player = player
        self.base_power = power


class ActionCard(Card):
    TARGET_BASE = 10
    TARGET_MINION = 20
    TARGET_OWNED_MINION = 30
    TARGET_ACTION = 40
    TARGET_FIELD = 50

    def __init__(self, id, player, name, text, targets):
        super().__init__(id, player.game, name, text)
        self.player = player
        self.targets = targets


class Deck:
    def __init__(self, name, bases, minions, actions):
        self.name = name
        self.bases = bases
        self.minions = minions
        self.actions = actions

    def create_cards(self, player, produce_id):
        cards = []
        for card_class in self.minions+self.actions:
            card = card_class(produce_id(card_class), player)
            cards.append(card)
        return cards

    def create_bases(self, game, produce_id):
        bases = []
        for base_class in self.bases:
            base = base_class(produce_id(base_class), game)
            bases.append(base)
        return bases
