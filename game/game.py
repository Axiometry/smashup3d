import threading
from pile import Pile
from intents import IntentRouter
from queue import Queue, Empty
import packets
import packets.game
import cards
from util import CountDownLatch
from player import Player, LocalPlayer


class GameConfig:
    def __init__(self, users, decks, point_max=15):
        super().__init__()
        self.users = users
        self.decks = decks
        self.point_max = point_max


class Game:
    def __init__(self, id, config):
        super().__init__()
        self.id = id
        self.users = config.users
        self.decks = config.decks
        self.point_max = config.point_max
        self.turn_state = None

    def start(self):
        pass

    def request_selection(self, player, text, options):
        raise NotImplementedError

    def request_selections(self, selections):
        raise NotImplementedError

    def get_player(self, user):
        raise NotImplementedError

    def has_player(self, user):
        raise NotImplementedError


class LocalGame(Game, threading.Thread):
    def __init__(self, id, config):
        super().__init__(id, config)

        self.players = []
        self._players_by_user = {}
        for user in config.users:
            player = LocalPlayer(user, self)
            self.players.append(player)
            self._players_by_user[user] = player

        self.bases = []
        self.base_deck = Pile()
        self.base_discard = Pile()
        self.actions = []
        self.intent_router = IntentRouter()

        self._card_id_counter = 0
        self._cards_by_id = {}

        self._packet_queue = Queue()

        self._request_id_counter = 0
        self._request_options = {}
        self._replies = {}
        self._reply_latch = CountDownLatch(0)

    def start(self):
        threading.Thread.start(self)

    def run(self):
        print('[Game'+str(self.id)+'] Starting...')
        self._distribute_decks()

        self.bases = [self.base_deck.remove_top() for i in range(len(self.players)+1)]
        for base in self.bases:
            base.state = cards.BaseInPlayState(base.power_threshold)
        for base in self.base_deck:
            base.state = cards.BaseInDeckState()

        for player in self.players:
            for card in player.deck:
                card.state = cards.InDeckState()

        for player in self.players:
            for i in range(5):
                self.draw_card(player)

        self._send_cards()

        while not self.is_won():
            self._take_turn()

        winner = self.get_winner()
        for player in self.players:
            player.send_packet(packets.game.EndGamePacket(winner.user.name))

    def _distribute_decks(self):
        print('[Game'+str(self.id)+'] Selecting decks...')
        remaining_decks = self.decks
        for player in self.players+list(reversed(self.players)):
            deck = self._choose_deck(player, remaining_decks)
            player.decks.append(deck)
            remaining_decks.remove(deck)

            for card in deck.create_cards(player, self._next_card_id):
                self._cards_by_id[card.id] = card
                player.deck.add_top(card)

        for player in self.players:
            player.deck.shuffle()
            for deck in player.decks:
                for base in deck.create_bases(self, self._next_card_id):
                    self._cards_by_id[base.id] = base
                    self.base_deck.add_top(base)

        self.base_deck.shuffle()

    def _choose_deck(self, player, remaining_decks):
        print('[Game'+str(self.id)+'] Player ' + player.user.name + ' selecting...')
        return self.request_selection(player, 'Choose a deck.', remaining_decks)

    def _next_card_id(self, card_class):
        card_id = self._card_id_counter
        self._card_id_counter += 1
        return card_id

    def is_won(self):
        return self.get_winner() is not None

    def get_winner(self):
        best, count = 0, 0
        for player in self.players:
            if count == 0 or player.points > best:
                best = player.points
                count = 1
            elif player.points == best:
                count += 1
        if best >= self.point_max and count == 1:
            return best
        return None

    def _next_turn_state(self):
        if self.turn_state is None:
            return TurnState(self.players[0])
        idx = self.players.index(self.turn_state.player)+1
        if idx >= len(self.players):
            idx = 0
        return TurnState(self.players[idx])

    def _take_turn(self):
        self.turn_state = self._next_turn_state()

        while True:
            self._send_game_state()
            (player, packet) = self._packet_queue.get(block=True)
            if player == self.turn_state.player:
                if isinstance(packet, packets.game.EndTurnPacket):
                    break
                elif isinstance(packet, packets.game.PlayCardPacket):
                    pass

        self.draw_card(self.turn_state.player)
        self.draw_card(self.turn_state.player)

    def draw_card(self, player):
        card = player.deck.remove_top()
        if len(player.deck) == 0:
            player.deck = player.discard
            player.discard = Pile()
            player.deck.shuffle()
        player.hand.append(card)
        return card

    def _send_cards(self):
        card_info = []
        for card_id in self._cards_by_id:
            card = self._cards_by_id[card_id]
            info = {'id': card_id, 'name': card.name, 'text': card.text}
            if isinstance(card, cards.MinionCard):
                info['type'] = 'minion'
                info['player'] = card.player.user.name
                info['power'] = card.base_power
            elif isinstance(card, cards.ActionCard):
                info['type'] = 'action'
                info['player'] = card.player.user.name
            elif isinstance(card, cards.BaseCard):
                info['type'] = 'base'
                info['power_threshold'] = card.power_threshold
                info['award_points'] = {
                    'first': card.award_points[0],
                    'second': card.award_points[1],
                    'third': card.award_points[2]
                }
            else:
                raise ValueError('Unknown card type')
            card_info.append(info)

        packet = packets.game.SetCardsPacket(card_info)
        for player in self.players:
            player.send_packet(packet)

    def _send_game_state(self):
        base_info = []
        for base in self.bases:
            base_info.append({
                'id': base.id,
                'power_total': base.state.power,
                'cards': [self._create_card_info(c) for c in base.state.minions+base.state.actions]
            })
        player_info = []
        for player in self.players:
            player_info.append({
                'name': player.user.name,
                'points': player.points,
                'hand_size': len(player.hand),
                'discard': [c.id for c in player.discard]
            })
        turn_info = {
            'name': self.turn_state.player.user.name,
            'minions': self.turn_state.minions_left,
            'actions': self.turn_state.actions_left
        }
        for player in self.players:
            hand = [c.id for c in player.hand]
            player.send_packet(packets.game.SetGameStatePacket(self.id, base_info, player_info, turn_info, hand))

    def _create_card_info(self, card):
        info = {'id': card.id, 'actions': [self._create_card_info(a) for a in card.actions]}
        if isinstance(card, cards.MinionCard):
            info['power'] = card.state.power
        return info

    def request_selection(self, player, text, options):
        self._reply_latch.counter = 1
        request_id = self._make_request(player, text, options)
        self._reply_latch.await()

        reply = self._replies[request_id]
        self._replies = {}
        return reply

    def request_selections(self, selections):
        self._reply_latch.counter = len(selections)
        selection_ids = {}
        for id in selections:
            player = selections[id]['player']
            text = selections[id]['text']
            options = selections[id]['options']
            selection_ids[self._make_request(player, text, options)] = id
        self._reply_latch.await()
        replies = {}
        for request_id in self._replies:
            replies[selection_ids[request_id]] = self._replies[request_id]
        self._replies = {}
        return replies

    def _make_request(self, player, text, options):
        request_id = self._request_id_counter
        self._request_id_counter += 1
        options_indexed = []
        options_out = []
        for opt in options:
            opt_id = len(options_indexed)
            options_indexed.append(opt)
            if isinstance(opt, cards.Card):
                options_out.append({'id': opt_id, 'type': 'card', 'card_id': opt.id})
            elif isinstance(opt, cards.Deck):
                options_out.append({'id': opt_id, 'type': 'deck', 'deck_name': opt.name})
            elif isinstance(opt, Player):
                options_out.append({'id': opt_id, 'type': 'player', 'player_name': opt.user.name})
            elif isinstance(opt, str):
                options_out.append({'id': opt_id, 'type': 'string', 'text': opt})
            else:
                raise ValueError('Bad selection option')
        self._request_options[request_id] = options_indexed
        player.send_packet(packets.game.RequestSelectionPacket(request_id, text, options_out))
        return request_id

    def reply_selection(self, request_id, option_id):
        self._replies[request_id] = self._request_options[request_id][option_id]
        self._reply_latch.count_down()

    def handle_packet(self, player, packet):
        if isinstance(packet, packets.game.ReplySelectionPacket):
            self.reply_selection(packet.request_id, packet.option_id)
        else:
            self._packet_queue.put(packet)

    def perform_intent(self, intent):
        self.intent_router.route_intent(intent)

    def receive_packet(self, user, connection, packet):
        if isinstance(packet, packets.game.ReplySelectionPacket):
            self.reply_selection(packet.request_id, packet.option_id)
            return
        self._packet_queue.put((self._players_by_user[user], packet))

    def add_connection(self, user, connection):
        if user in self._players_by_user:
            connection.serializer.register(packets.game.RequestSelectionPacket, 'request_selection')
            connection.serializer.register(packets.game.EndGamePacket, 'end_game')
            connection.serializer.register(packets.game.SetCardsPacket, 'set_cards')
            connection.serializer.register(packets.game.SetGameStatePacket, 'set_state')
            connection.deserializer.register(packets.game.ReplySelectionPacket, 'reply_selection')
            connection.deserializer.register(packets.game.PlayCardPacket, 'play_card')
            connection.deserializer.register(packets.game.EndTurnPacket, 'end_turn')
            self._players_by_user[user].add_connection(connection)

    def remove_connection(self, user, connection):
        if user in self._players_by_user:
            self._players_by_user[user].remove_connection(connection)
            connection.serializer.unregister(packets.game.RequestSelectionPacket)
            connection.serializer.unregister(packets.game.EndGamePacket)
            connection.serializer.unregister(packets.game.SetCardsPacket)
            connection.serializer.unregister(packets.game.SetGameStatePacket)
            connection.deserializer.unregister(packets.game.ReplySelectionPacket)
            connection.deserializer.unregister(packets.game.EndTurnPacket)

    def has_connection(self, user, connection):
        return user in self._players_by_user and self._players_by_user[user].has_connection(connection)

    def get_player(self, user):
        return self._players_by_user[user]

    def has_player(self, user):
        return user in self._players_by_user


class TurnState:
    def __init__(self, player):
        self.player = player
        self.minions_left = 1
        self.actions_left = 1
