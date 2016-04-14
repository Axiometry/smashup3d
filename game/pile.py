from random import shuffle
from collections import deque


class Pile(object):
    def __init__(self, cards=[], shuffle=False):
        self.cards = deque(cards)
        if shuffle:
            self.shuffle()

    def get_top(self):
        return self.cards[-1]

    def remove_top(self):
        return self.cards.pop()

    def shuffle(self):
        shuffle(self.cards)

    def size(self):
        return len(self.cards)

    def add_bottom(self, card):
        self.cards.appendleft(card)

    def add_top(self, card):
        self.cards.append(card)

    def __iter__(self):
        return self.cards.__iter__()

    def __len__(self):
        return self.cards.__len__()
