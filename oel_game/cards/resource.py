__author__ = 'Jurek'

from ..enums import Age, CardType, Variant, ResourceToken, LandscapePlot
from ..goods import *
from .card import Card
from .function import UseProductionWheel, GainExact, FellTrees, CutPeat


class Forest(Card):
    def __init__(self, *args, **kwargs):
        super(Forest, self).__init__(*args, **kwargs)
        self.function.add(FellTrees())

    @property
    def name(self):
        return 'Forest'

    @property
    def id(self):
        return 'r01'

    @property
    def card_type(self):
        return CardType.Forest

    @property
    def age(self):
        return Age.Basic

    @property
    def landscapes(self):
        return super(Forest, self).landscapes

    @property
    def cost(self):
        return {}

    @property
    def economic_value(self):
        return None

    @property
    def dwelling_value(self):
        return None

    @property
    def variant(self):
        return Variant.All

    @property
    def can_be_removed(self):
        return True


class Moor(Card):
    def __init__(self, *args, **kwargs):
        super(Moor, self).__init__(*args, **kwargs)
        self.function.add(CutPeat())

    @property
    def name(self):
        return 'Moor'

    @property
    def id(self):
        return 'r02'

    @property
    def card_type(self):
        return CardType.Moor

    @property
    def age(self):
        return Age.Basic

    @property
    def landscapes(self):
        return super(Moor, self).landscapes

    @property
    def cost(self):
        return {}

    @property
    def economic_value(self):
        return None

    @property
    def dwelling_value(self):
        return None

    @property
    def variant(self):
        return Variant.All

    @property
    def can_be_removed(self):
        return True


class Water(Card):
    @property
    def name(self):
        return 'Water'

    @property
    def id(self):
        return 'p01'

    @property
    def card_type(self):
        return CardType.Water

    @property
    def age(self):
        return Age.Basic

    @property
    def landscapes(self):
        return {LandscapePlot.Water}

    @property
    def cost(self):
        return {}

    @property
    def economic_value(self):
        return None

    @property
    def dwelling_value(self):
        return 3

    @property
    def variant(self):
        return Variant.All

    @property
    def can_be_removed(self):
        return False

    @property
    def can_be_overbuilt(self):
        return True