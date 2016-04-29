__author__ = 'Jurek'

from ..enums import Age, CardType, LandscapePlot, Variant
from ..goods import *
from .card import Card


class Settlement(Card):

    @property
    def name(self):
        raise NotImplementedError()

    @property
    def id(self):
        raise NotImplementedError()

    @property
    def card_type(self):
        return CardType.Settlement

    @property
    def age(self):
        raise NotImplementedError()

    @property
    def landscapes(self):
        return super(Settlement, self).landscapes

    @property
    def cost(self):
        raise NotImplementedError()

    @property
    def economic_value(self):
        raise NotImplementedError()

    @property
    def dwelling_value(self):
        raise NotImplementedError()

    @property
    def variant(self):
        return Variant.All

    @property
    def can_be_removed(self):
        return super(Settlement, self).can_be_removed


class ShantyTown(Settlement):
    @property
    def name(self):
        return 'Shanty Town'

    @property
    def id(self):
        return 's01'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Energy(1), Food(1)})

    @property
    def economic_value(self):
        return 0

    @property
    def dwelling_value(self):
        return -3


class FarmingVillage(Settlement):
    @property
    def name(self):
        return 'Farming Village'

    @property
    def id(self):
        return 's02'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Energy(3), Food(3)})

    @property
    def economic_value(self):
        return 1

    @property
    def dwelling_value(self):
        return 1


class MarketTown(Settlement):
    @property
    def name(self):
        return 'Market Town'

    @property
    def id(self):
        return 's03'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Energy(0), Food(7)})

    @property
    def economic_value(self):
        return 2

    @property
    def dwelling_value(self):
        return 2


class FishingVillage(Settlement):
    @property
    def name(self):
        return 'Fishing Village'

    @property
    def id(self):
        return 's04'

    @property
    def age(self):
        return Age.Start

    @property
    def landscapes(self):
        return {LandscapePlot.Coast}

    @property
    def cost(self):
        return GoodsSet({Energy(3), Food(8)})

    @property
    def economic_value(self):
        return 4

    @property
    def dwelling_value(self):
        return 6


class ArtistsColony(Settlement):
    @property
    def name(self):
        return "Artist's Colony"

    @property
    def id(self):
        return 's05'

    @property
    def age(self):
        return Age.A

    @property
    def cost(self):
        return GoodsSet({Energy(1), Food(5)})

    @property
    def economic_value(self):
        return -1

    @property
    def dwelling_value(self):
        return 5


class Hamlet(Settlement):
    @property
    def name(self):
        return 'Hamlet'

    @property
    def id(self):
        return 's06'

    @property
    def age(self):
        return Age.B

    @property
    def cost(self):
        return GoodsSet({Energy(3), Food(3)})

    @property
    def economic_value(self):
        return 3

    @property
    def dwelling_value(self):
        return 4


class Village(Settlement):
    @property
    def name(self):
        return 'Village'

    @property
    def id(self):
        return 's07'

    @property
    def age(self):
        return Age.C

    @property
    def cost(self):
        return GoodsSet({Energy(9), Food(15)})

    @property
    def economic_value(self):
        return 3

    @property
    def dwelling_value(self):
        return 4


class HilltopVillage(Settlement):
    @property
    def name(self):
        return 'Hilltop Village'

    @property
    def id(self):
        return 's08'

    @property
    def age(self):
        return Age.D

    @property
    def landscapes(self):
        return {LandscapePlot.Hillside}

    @property
    def cost(self):
        return GoodsSet({Energy(3), Food(30)})

    @property
    def economic_value(self):
        return 10

    @property
    def dwelling_value(self):
        return 8
