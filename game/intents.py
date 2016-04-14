# intents.py


class Intent:
    def __init__(self):
        self.cancelled = False

    def cancel(self):
        self.cancelled = True


class IntentConsumer:
    def get_intent_list(self):
        raise NotImplementedError

    def get_intent_handlers(self, intent):
        raise NotImplementedError


class IntentRouter:
    def __init__(self):
        self._consumers = {}

    def route_intent(self, intent):
        handlers = {}
        for consumer in self._consumers[intent.__class__]:
            consumer_handlers = consumer.get_intent_handlers(intent)
            for priority in consumer_handlers:
                if priority in handlers:
                    handlers[priority] += consumer_handlers[priority]
                else:
                    handlers[priority] = consumer_handlers[priority]

        for priority in sorted(handlers):
            # TODO select order of handlers (?)
            for handler in handlers[priority]:
                handler.handle_intent(intent)
                if intent.cancelled:
                    if priority != PRIORITY_CANCEL and priority != PRIORITY_CANCEL_AND_MODIFY:
                        # TODO warn
                        pass
                    break

    def register(self, consumer):
        for intent in consumer.get_intent_list():
            for intent_class in self._consumers:
                if issubclass(intent, intent_class):
                    self._consumers[intent_class] += consumer
            if intent not in self._consumers:
                self._consumers[intent] = [consumer]

    def unregister(self, consumer):
        # haha nice joke
        raise NotImplementedError

""" Turn Intents """


class StartTurn(Intent):
    def __init__(self, player):
        super().__init__()
        self.player = player


class EndTurn(Intent):
    def __init__(self, player):
        super().__init__()
        self.player = player


""" General Card Intents """


class PlayCard(Intent):
    def __init__(self, card):
        super().__init__()
        self.card = card


class RemoveCardFromPlay(Intent):
    def __init__(self, card):
        super().__init__()
        self.card = card


class DestroyCard(RemoveCardFromPlay):
    def __init__(self, card):
        super().__init__(card)


class PlaceCardOnDeck(RemoveCardFromPlay):
    def __init__(self, card):
        super().__init__(card)


class PlaceCardOnDeckTop(PlaceCardOnDeck):
    def __init__(self, card):
        super().__init__(card)


class PlaceCardOnDeckBottom(PlaceCardOnDeck):
    def __init__(self, card):
        super().__init__(card)


class ReturnCardToHand(RemoveCardFromPlay):
    def __init__(self, card):
        super().__init__(card)


class ResolveCardAbility(Intent):
    def __init__(self, card):
        super().__init__()
        self.card = card


class ChangeCardOwner(Intent):
    def __init__(self, card, new_owner):
        super().__init__()
        self.card = card
        self.new_owner = new_owner


""" Base Card Intents """


class PlayBase(Intent):
    def __init__(self, base):
        super().__init__()
        self.base = base


class BlowBase(Intent):
    def __init__(self, base):
        super().__init__()
        self.base = base


class SwapBase(Intent):
    def __init__(self, base_from, base_to):
        super().__init__()
        self.base_from = base_from
        self.base_to = base_to


class RemoveBase(Intent):
    def __init__(self, base):
        super().__init__()
        self.base = base


class ModifyBasePowerThreshold(Intent):
    def __init__(self, base, off):
        super().__init__()
        self.base = base
        self.off = off


""" Minion Card Intents """


class AffectMinion(Intent):
    def __init__(self, minion):
        super().__init__()
        self.minion = minion


class PlayMinion(PlayCard):
    def __init__(self, minion):
        super().__init__(minion)
        self.minion = minion


class RemoveMinionFromPlay(RemoveCardFromPlay, AffectMinion):
    def __init__(self, minion):
        super().__init__(minion)


class DestroyMinion(RemoveMinionFromPlay, DestroyCard):
    def __init__(self, minion):
        super().__init__(minion)


class PlaceMinionOnDeck(RemoveMinionFromPlay, PlaceCardOnDeck):
    def __init__(self, minion):
        super().__init__(minion)


class PlaceMinionOnDeckTop(PlaceMinionOnDeck, PlaceCardOnDeckTop):
    def __init__(self, minion):
        super().__init__(minion)


class PlaceMinionOnDeckBottom(PlaceMinionOnDeck, PlaceCardOnDeckBottom):
    def __init__(self, minion):
        super().__init__(minion)


class ReturnMinionToHand(RemoveMinionFromPlay, ReturnCardToHand):
    def __init__(self, minion):
        super().__init__(minion)


class MoveMinion(AffectMinion):
    def __init__(self, minion, base):
        super().__init__(minion)
        self.base = base


class ResolveMinionAbility(ResolveCardAbility):
    def __init__(self, minion):
        super().__init__(minion)
        self.minion = minion


class ModifyMinionPower(Intent):
    def __init__(self, minion, off):
        super().__init__()
        self.minion = minion
        self.off = off


""" Action Card Intents """


class PlayAction(PlayCard):
    def __init__(self, action):
        super().__init__(action)
        self.action = action


class PlayActionOnBase(PlayAction):
    def __init__(self, action, target):
        super().__init__(action)
        self.target = target


class PlayActionOnMinion(PlayAction):
    def __init__(self, action, target):
        super().__init__(action)
        self.target = target


class PlayActionOnAction(PlayAction):
    def __init__(self, action, target):
        super().__init__(action)
        self.target = target


class PlayActionOnField(PlayAction):
    def __init__(self, action):
        super().__init__(action)


class RemoveActionFromPlay(RemoveCardFromPlay):
    def __init__(self, action):
        super().__init__(action)
        self.action = action


class DestroyAction(RemoveActionFromPlay, DestroyCard):
    def __init__(self, action):
        super().__init__(action)


class PlaceActionOnDeck(RemoveActionFromPlay, PlaceCardOnDeck):
    def __init__(self, action):
        super().__init__(action)


class PlaceActionOnDeckTop(RemoveActionFromPlay, PlaceCardOnDeckTop):
    def __init__(self, action):
        super().__init__(action)


class PlaceActionOnDeckBottom(RemoveActionFromPlay, PlaceCardOnDeckBottom):
    def __init__(self, action):
        super().__init__(action)


class ReturnActionToHand(RemoveActionFromPlay, ReturnCardToHand):
    def __init__(self, action):
        super().__init__(action)


class ResolveActionAbility(ResolveCardAbility):
    def __init__(self, action):
        super().__init__(action)


""" Priorities """


PRIORITY_CANCEL = 1000
PRIORITY_CANCEL_AND_MODIFY = 2000
PRIORITY_MODIFY = 3000
PRIORITY_PRE_RESOLVE = 7000
PRIORITY_RESOLVE = 8000
PRIORITY_POST_RESOLVE = 9000
