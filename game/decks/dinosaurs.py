# DINOSAURS
from cards import Deck, BaseCard, MinionCard, ActionCard
import cards
import intents


class DinosaursDeck(Deck):
    def __init__(self):
        super().__init__('Dinosaurs',
                         [JungleOasis, TarPits],
                         [Laseratops, WarRaptor, ArmorStego, KingRex],
                         [WildlifePreserve, ToothAndClawAndGuns, NaturalSelection,
                          Howl, Rampage, Upgrade, SurvivalOfTheFittest, Augmentation])


class JungleOasis(BaseCard):
    def __init__(self, id, game):
        super().__init__(id, game, 'Jungle Oasis', '', 12, [2, 0, 0])


class TarPits(BaseCard):
    def __init__(self, id, game):
        super().__init__(id, game, 'Tar Pits', 'After each time a minion is destroyed here,'
                                               'place it at the bottom of its owner\'s deck.',
                         16, [4, 3, 2])
        self._minion_tracker = []

    def handle_intent(self, intent, priority):
        if not isinstance(self.state, cards.BaseInPlayState):
            return
        if (priority == intents.PRIORITY_PRE_RESOLVE and
                isinstance(intent, intents.DestroyMinion) and
                self == intent.minion.state.base):
            self._minion_tracker.append(intent.minion)
        if (priority == intents.PRIORITY_POST_RESOLVE and
                isinstance(intent, intents.DestroyMinion) and
                intent.minion in self._minion_tracker):
            self._minion_tracker.remove(intent.minion)
            self.game.perform_intent(intents.PlaceMinionOnDeckBottom(intent.minion))


class Laseratops(MinionCard):
    def __init__(self, id, player):
        super().__init__(id, player, 'Laseratops', 'Destroy a minion of power 2 or less on this base.', 4)

    def handle_intent(self, intent, priority):
        if not isinstance(self.state, cards.MinionOnBaseState):
            return
        if (priority == intents.PRIORITY_RESOLVE and
                isinstance(intent, intents.ResolveMinionAbility) and
                self == intent.minion):
            targets = [m for m in self.state.base.minions if m.power <= 2]
            if len(targets) > 0:
                target = self.game.request_selection(self.player, targets)
                self.game.perform_intent(intents.DestroyMinion(target))


class WildlifePreserve(ActionCard):
    def __init__(self, id, game):
        super().__init__(id, game, 'Wildlife Preserve',
                         'Play on a base. Ongoing: Your minions here '
                         'are not affected by other players\' actions.',
                         [BaseCard])

    def handle_intent(self, intent, priority):
        if not isinstance(self.state, cards.ActionOnBaseState):
            return
        if priority == intent.PRIORITY_CANCEL:
            if (isinstance(intent, intents.AffectMinion) and
                    self.state.owner == intent.minion.state.owner and
                    self.state.base == intent.minion.state.base):
                intent.cancel()


class WarRaptor(MinionCard):
    def __init__(self, id, player):
        super().__init__(id, player, 'War Raptor', 'Ongoing: Gains +1 power for each War Raptor '
                                     'on this base (including this one).', 2)

    def handle_intent(self, intent, priority):
        if (priority == intents.PRIORITY_RESOLVE and
                isinstance(intent, intents.ResolveMinionAbility) and
                self == intent.minion):
            for m in self.state.base.minions:
                if isinstance(m, WarRaptor):
                    self.game.perform_intent(intents.ModifyMinionPower(self, off=1))
                    if self != m:
                        self.game.perform_intent(intents.ModifyMinionPower(m, off=1))
        if (priority == intents.PRIORITY_MODIFY and
                isinstance(intent, intents.DestroyMinion) and
                self == intent.minion):
            for m in self.state.base.minions:
                if isinstance(m, WarRaptor):
                    self.game.perform_intent(intents.ModifyMinionPower(self, off=-1))
                    if self != m:
                        self.game.perform_intent(intents.ModifyMinionPower(m, off=-1))


class ToothAndClawAndGuns(ActionCard):
    def __init__(self, id, player):
        super().__init__(id, player, 'Tooth and Claw... and Guns',
                         'Play on a minion. Ongoing: If an ability would affect this minion,'
                         ' destroy this card and the ability does not affect this minion.',
                         [MinionCard])

    def handle_intent(self, intent, priority):
        if priority == intents.PRIORITY_CANCEL_AND_MODIFY and isinstance(self.state, cards.ActionOnMinionState):
            if isinstance(intent, intents.AffectMinion) and self.state.minion == intent.minion:
                intent.cancel()
                self.game.perform_intent(intents.DestroyAction(self))


class NaturalSelection(ActionCard):
    def __init__(self, id, player):
        super().__init__(id, player, 'Natural Selection',
                         'Choose one of your minions on a base. Destroy a '
                         'minion there with less power than yours.', [])

    def handle_intent(self, intent, priority):
        if (priority == intents.PRIORITY_RESOLVE and
                isinstance(intent, intents.ResolveActionAbility) and
                self == intent.action):
            targets = [m for b in self.game.bases for m in b.minions if self.state.owner == m.state.owner]
            if len(targets) > 0:
                target = self.game.request_selection(self.state.owner, targets)
                targets = [m for m in target.state.base.minions if m.state.power < target.state.power]
                if len(targets) > 0:
                    target = self.game.request_selection(self.state.owner, targets)
                    self.game.perform_intent(intents.DestroyMinion(target))


class ArmorStego(MinionCard):
    def __init__(self, id, player):
        super().__init__(id, player, 'Armor Stego', 'Ongoing: Has +2 power during other players\' turns.', 3)

    def handle_intent(self, intent, priority):
        if priority == intents.PRIORITY_PRE_RESOLVE and isinstance(self.state, cards.InPlayState):
            if isinstance(intent, intents.StartTurn) and self.state.owner == intent.player:
                self.game.perform_intent(intents.ModifyMinionPower(self, off=2))
            elif isinstance(intent, intents.EndTurn) and self.state.owner == intent.player:
                self.game.perform_intent(intents.ModifyMinionPower(self, off=-2))
            elif isinstance(intent, intents.ChangeCardOwner) and self == intent.card:
                if self.state.owner == self.game.active_player and intent.new_owner != self.game.active_player:
                    self.game.perform_intent(intents.ModifyMinionPower(self, off=-2))
                elif self.state.owner != self.game.active_player and intent.new_owner == self.game.active_player:
                    self.game.perform_intent(intents.ModifyMinionPower(self, off=2))


class Howl(ActionCard):
    def __init__(self, id, player):
        super().__init__(id, player, 'Howl', 'Each of your minions gains +1 power until the end of your turn.', [])

    def handle_intent(self, intent, priority):
        if (priority == intents.PRIORITY_RESOLVE and
                isinstance(intent, intents.ResolveActionAbility) and
                self == intent.action):
            for b in self.game.bases:
                for m in b.minions:
                    if m.state.owner == self.player:
                        self.game.perform_intent(intents.ModifyMinionPower(m, off=1))
        elif priority == intents.PRIORITY_MODIFY and isinstance(self.state, cards.InPlayState):
            if isinstance(intent, intents.EndTurn) and self.player == intent.player:
                for b in self.game.bases:
                    for m in b.minions:
                        if m.state.owner == self.player:
                            self.game.perform_intent(intents.ModifyMinionPower(m, off=-1))
                self.game.perform_intent(intents.DestroyAction(self))
            elif isinstance(intent, intents.MinionPlayed) and self.player == intent.minion.state.owner:
                self.game.perform_intent(intents.ModifyMinionPower(intent.minion, off=1))


class KingRex(MinionCard):
    def __init__(self, id, player):
        super().__init__(id, player, 'King Rex', '', 7)


class Rampage(ActionCard):
    def __init__(self, id, player):
        super().__init__(id, player, 'Rampage',
                         'Reduce the breakpoint of a base by the power of one '
                         'of your minions on that base until the end of the turn.', [])

    def handle_intent(self, intent, priority):
        if (priority == intents.PRIORITY_CANCEL and
                isinstance(intent, intents.PlayAction) and
                self == intent.action):
            targets = [b for b in self.game.bases if sum([1 for m in b.minions if m.state.owner == self.player]) > 0]
            if len(targets) == 0:
                intent.cancel()
        elif (priority == intents.PRIORITY_RESOLVE and
                isinstance(intent, intents.ResolveActionAbility) and
                self == intent.action):
            targets = [m for b in self.game.bases for m in b.minions]
            if len(targets) > 0:
                target = self.game.request_selection(self.player, targets)
                self.state._rampage_target_power = target.state.power
                self.state._rampage_target_base = target.state.base
                self.game.perform_intent(intents.ModifyBasePowerThreshold(target.state.base, off=-target.state.power))
        elif (priority == intents.PRIORITY_MODIFY and
                isinstance(self.state, cards.InPlayState) and
                isinstance(intent, intents.EndTurn) and
                self.player == intent.player):
            if (hasattr(self.state, '_rampage_target_power') and
                    isinstance(self.state._rampage_target_base.state, cards.InPlayState)):
                self.game.perform_intent(intents.ModifyBasePowerThreshold(
                    self.state._rampage_target_base, off=self.state._rampage_target_power))

            del self.state._rampage_target_power
            del self.state._rampage_target_base
            self.game.perform_intent(intents.DestroyAction(self))


class Upgrade(ActionCard):
    def __init__(self, id, player):
        super().__init__(id, player, 'Upgrade', 'Play on a minion. Ongoing: This minion has +2 power.', [MinionCard])

    def handle_intent(self, intent, priority):
        if (priority == intents.PRIORITY_RESOLVE and
                isinstance(intent, intents.ResolveActionAbility) and
                self == intent.action):
            self.game.perform_intent(intents.ModifyMinionPower(self.state.minion, off=2))
        elif (priority == intents.PRIORITY_PRE_RESOLVE and
                isinstance(intent, intents.DestroyAction) and
                self == intent.action):
            self.game.perform_intent(intents.ModifyMinionPower(self.state.minion, off=-2))


class SurvivalOfTheFittest(ActionCard):
    def __init__(self, id, player):
        super().__init__(id, player, 'Survival of the Fittest',
                         'Destroy the lowest-power minion (you choose in case of a tie)'
                         ' on each base with a higher-power minion.', [])

    def handle_intent(self, intent, priority):
        if (priority == intents.PRIORITY_RESOLVE and
                isinstance(intent, intents.ResolveActionAbility) and
                self == intent.action):
            for base in self.game.bases:
                targets = []
                for m in base.minions:
                    if len(targets) == 0 or m.state.power < targets[0].state.power:
                        targets = [m]
                    if len(targets) != 0 and m.state.power == targets[0].state.power:
                        targets.append(m)
                if 0 < len(targets) < len(base.minions):
                    if len(targets) > 1:
                        target = self.game.request_selection(self.player, targets)
                    else:
                        target = targets[0]
                    self.game.perform_intent(intents.DestroyMinion(target))


class Augmentation(ActionCard):
    def __init__(self, id, player):
        super().__init__(id, player, 'Augmentation', 'One minion gains +4 power until the end of your turn.', [])

    def handle_intent(self, intent, priority):
        if (priority == intents.PRIORITY_RESOLVE and
                isinstance(intent, intents.ResolveActionAbility) and
                self == intent.action):
            targets = [m for b in self.game.bases for m in b.minions]
            target = self.game.request_selection(self.player, targets)
            self.state._target = target
            self.game.perform_intent(intents.ModifyMinionPower(target, off=4))
        elif (priority == intents.PRIORITY_PRE_RESOLVE and isinstance(intent, intents.DestroyAction) and
                self == intent.action):
            self.game.perform_intent(intents.ModifyMinionPower(self.state._target, off=-4))
        elif isinstance(intent, intents.EndTurn) and self.state.owner == intent.player:
            self.game.perform_intent(intents.DestroyAction(self))


class TenatiousZ(MinionCard):
    def __init__(self, id, player):
        super().__init__(id, player, 'Tenatious Z', 'Special: blag', 2)

    def handle_intent(self, intent, priority):
        if (priority == intents.PRIORITY_CANCEL and
                isinstance(intent, intents.PlayMinion) and
                self == intent.minion and
                hasattr(self.game.turn_state, 'tenatiousz_used')):
            intent.cancel()
        elif (priority == intents.PRIORITY_RESOLVE and
                isinstance(intent, intents.ResolveMinionAbility) and
                self == intent.minion and
                isinstance(intent, cards.InDiscardState)):
            self.game.turn_state.tenatiousz_used = True
            self.game.turn_state.minions += 1
        elif (priority == intents.PRIORITY_MODIFY and
                isinstance(intent, intents.EndTurn) and
                self.player == intent.player):
            del self.game.turn_state.tenatiousz_used
