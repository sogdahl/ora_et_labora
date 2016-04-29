__author__ = 'Jurek'
from abc import ABCMeta, abstractproperty, abstractmethod
from decimal import Decimal

from .enums import LandscapeType, LandscapePlot, DistrictSide, PlotSide
from .exceptions import CardAlreadyExists, CardCantBeRemoved, InvalidCardSpace, NoCardToRemove
from .cards import Forest, Moor, Farmyard, ClayMound, CloisterOffice, Water
from .goods import Coin


class LandscapeSpace(object):
    def __init__(self, landscape_plot, card=None):
        self.landscape_plot = landscape_plot
        self._cards = []
        if card:
            self.add_card(card)

    @property
    def card(self):
        if self._cards:
            return self._cards[-1]
        return None

    @property
    def all_cards(self):
        return self._cards

    def add_card(self, new_card, force_overplay=False):
        if self._cards and not force_overplay:
            raise CardAlreadyExists("{0} is already in this space".format(self._cards[-1]))
        if self.landscape_plot not in new_card.landscapes:
            raise InvalidCardSpace("{0} can't be placed in a {1} space".format(new_card, self.landscape_plot))
        if new_card.id == "FL1":
            if not self._cards or self._cards[-1].id != "H01":
                raise InvalidCardSpace("{0} can't be placed in a {1} space".format(new_card, self.landscape_plot))
        self._cards.append(new_card)

    def remove_card(self):
        if not self._cards:
            raise NoCardToRemove()
        if not self._cards[-1].can_be_removed:
            raise CardCantBeRemoved()
        return self._cards.pop()


class LandscapeColumn(list):
    def __init__(self, offset=0, iterable=None):
        super(LandscapeColumn, self).__init__(iterable)
        self.offset = offset


class Landscape(object):
    __metaclass__ = ABCMeta

    def __getitem__(self, item):
        return self.landscape_spaces[item]

    @abstractproperty
    def landscape_spaces(self):
        pass

    @abstractproperty
    def landscape_type(self):
        pass

    @abstractproperty
    def horizontal_size(self):
        pass

    @abstractproperty
    def vertical_size(self):
        pass

    @abstractproperty
    def row(self):
        pass

    @row.setter
    @abstractmethod
    def row(self, value):
        pass

    @abstractproperty
    def column(self):
        pass


class Heartland(Landscape):

    def __init__(self):
        super(Heartland, self).__init__()
        self._landscape_spaces = [
            LandscapeColumn(iterable=[
                LandscapeSpace(LandscapePlot.Plains, Moor(owner=self)),
                LandscapeSpace(LandscapePlot.Plains, Moor(owner=self))
            ]),
            LandscapeColumn(iterable=[
                LandscapeSpace(LandscapePlot.Plains, Forest(owner=self)),
                LandscapeSpace(LandscapePlot.Plains, Forest(owner=self))
            ]),
            LandscapeColumn(iterable=[
                LandscapeSpace(LandscapePlot.Plains, Forest(owner=self)),
                LandscapeSpace(LandscapePlot.Plains, Farmyard(owner=self))
            ]),
            LandscapeColumn(iterable=[
                LandscapeSpace(LandscapePlot.Plains),
                LandscapeSpace(LandscapePlot.Plains)
            ]),
            LandscapeColumn(iterable=[
                LandscapeSpace(LandscapePlot.Hillside, ClayMound(owner=self)),
                LandscapeSpace(LandscapePlot.Plains, CloisterOffice(owner=self))
            ])
        ]

    def __getitem__(self, item):
        return self.landscape_spaces[item]

    @property
    def landscape_spaces(self):
        return self._landscape_spaces

    @property
    def landscape_type(self):
        return LandscapeType.Heartland

    @property
    def horizontal_size(self):
        return 5

    @property
    def vertical_size(self):
        return 2

    @property
    def row(self):
        return 30

    @property
    def column(self):
        return 2


class District(Landscape):

    def __init__(self, landscape_id, cost):
        self._id = 'district{0}'.format(landscape_id)
        self._landscape_side = DistrictSide.MoorForestForestHillsideHillside
        self._row = None
        if isinstance(cost, int):
            cost = Coin(cost)
        self._cost = cost
        self._landscape_spaces = {
            DistrictSide.MoorForestForestHillsideHillside: [
                LandscapeColumn(iterable=[LandscapeSpace(LandscapePlot.Plains, Moor())]),
                LandscapeColumn(iterable=[LandscapeSpace(LandscapePlot.Plains, Forest())]),
                LandscapeColumn(iterable=[LandscapeSpace(LandscapePlot.Plains, Forest())]),
                LandscapeColumn(iterable=[LandscapeSpace(LandscapePlot.Hillside)]),
                LandscapeColumn(iterable=[LandscapeSpace(LandscapePlot.Hillside)])
            ],
            DistrictSide.ForestPlainsPlainsPlainsHillside: [
                LandscapeColumn(iterable=[LandscapeSpace(LandscapePlot.Plains, Forest())]),
                LandscapeColumn(iterable=[LandscapeSpace(LandscapePlot.Plains)]),
                LandscapeColumn(iterable=[LandscapeSpace(LandscapePlot.Plains)]),
                LandscapeColumn(iterable=[LandscapeSpace(LandscapePlot.Plains)]),
                LandscapeColumn(iterable=[LandscapeSpace(LandscapePlot.Hillside)])
            ]
            }

    @property
    def id(self):
        return self._id

    @property
    def landscape_side(self):
        return self._landscape_side

    @landscape_side.setter
    def landscape_side(self, value):
        if value not in (DistrictSide.MoorForestForestHillsideHillside, DistrictSide.ForestPlainsPlainsPlainsHillside):
            raise TypeError("landscape_side must be of type DistrictSide")
        self._landscape_side = value

    @property
    def landscape_spaces(self):
        return self._landscape_spaces[self.landscape_side]

    @property
    def landscape_type(self):
        return LandscapeType.District

    @property
    def cost(self):
        return self._cost

    @property
    def horizontal_size(self):
        return 5

    @property
    def vertical_size(self):
        return 1

    @property
    def row(self):
        return self._row

    @row.setter
    def row(self, value):
        self._row = value

    @property
    def column(self):
        return 2


class Plot(Landscape):

    def __init__(self, landscape_id, cost):
        self._id = 'plot{0}'.format(landscape_id)
        self._landscape_side = PlotSide.Coastal
        self._row = None
        if isinstance(cost, int):
            cost = Coin(cost)
        self._cost = cost
        self._landscape_spaces = {
            PlotSide.Coastal: [
                LandscapeColumn(iterable=[
                    LandscapeSpace(LandscapePlot.Water, Water()),
                    LandscapeSpace(LandscapePlot.Water, Water())
                ]),
                LandscapeColumn(iterable=[
                    LandscapeSpace(LandscapePlot.Coast),
                    LandscapeSpace(LandscapePlot.Coast)
                ])
            ],
            PlotSide.Mountain: [
                LandscapeColumn(iterable=[
                    LandscapeSpace(LandscapePlot.Hillside),
                    LandscapeSpace(LandscapePlot.Hillside)
                ]),
                LandscapeColumn(offset=Decimal(0.5), iterable=[
                    LandscapeSpace(LandscapePlot.Mountain),
                    None
                ])
            ]
            }

    @property
    def id(self):
        return self._id

    @property
    def landscape_side(self):
        return self._landscape_side

    @landscape_side.setter
    def landscape_side(self, value):
        if value not in (PlotSide.Coastal, PlotSide.Mountain):
            raise TypeError("landscape_side must be of type PlotSide")
        self._landscape_side = value

    @property
    def landscape_spaces(self):
        return self._landscape_spaces[self.landscape_side]

    @property
    def landscape_type(self):
        return LandscapeType.Plot

    @property
    def cost(self):
        return self._cost

    @property
    def horizontal_size(self):
        return 2

    @property
    def vertical_size(self):
        return 2

    @property
    def row(self):
        return self._row

    @row.setter
    def row(self, value):
        self._row = value

    @property
    def column(self):
        return 0 if self.landscape_side == PlotSide.Coastal else 7
