__author__ = 'Jurek'
from abc import ABCMeta, abstractproperty

from .enums import Gameboard, ProductionWheel, ResourceToken

# This section is mostly temporary until the classes can get moved to their own files


class ModX(int):
    def __new__(cls, val, x, **kwargs):
        return super(ModX, cls).__new__(cls, val % x)

    def __init__(self, val, x):
        super(ModX, self).__init__()
        self._x = x

    def __add__(self, other):
        return ModX((int.__add__(self, other)) % self._x, self._x)

    def __sub__(self, other):
        return ModX((int.__sub__(self, other)) % self._x, self._x)


class LedgerEntry(object):
    def __init__(self, text, executor_index=None):
        self._text = text
        self._executor_index = executor_index

    @property
    def text(self):
        return self._text

    @property
    def executor_index(self):
        return self._executor_index


class GameLedger(list):
    # Not sure if these are needed.  Shelving for now
    """
    def __init__(self, iterable=None):
        if not all([isinstance(x, LedgerEntry) for x in iterable]):
            raise TypeError("iterable items must all be LedgerEntry objects")
        super(GameLedger, self).__init__(iterable)

    def __setslice__(self, i, j, iterable):
        if not all([isinstance(x, LedgerEntry) for x in iterable]):
            raise TypeError("iterable items must all be LedgerEntry objects")
        super(GameLedger, self).__setslice__(i, j, iterable)

    def __setitem__(self, i, value):
        if not isinstance(value, LedgerEntry):
            raise TypeError("value must be a LedgerEntry")
        super(GameLedger, self).__setitem__(i, value)

    def append(self, value):
        if not isinstance(value, LedgerEntry):
            raise TypeError("value must be a LedgerEntry")
        super(GameLedger, self).append(value)

    def extend(self, iterable):
        if not all([isinstance(x, LedgerEntry) for x in iterable]):
            raise TypeError("iterable items must all be LedgerEntry objects")
        super(GameLedger, self).extend(iterable)

    def insert(self, i, value):
        if not isinstance(value, LedgerEntry):
            raise TypeError("value must be a LedgerEntry")
        super(GameLedger, self).insert(i, value)
    """


class GameBoard(dict):
    def __init__(self, gameboard_type, wheel_type):
        self.gameboard_type = gameboard_type
        self.wheel_type = wheel_type
        super(GameBoard, self).__init__()
        self.update({
            ResourceToken.Wheel: 0,
            ResourceToken.Wood: 0,
            ResourceToken.Peat: 0,
            ResourceToken.Grain: 0,
            ResourceToken.Livestock: 0,
            ResourceToken.Clay: 0,
            ResourceToken.Coin: 0,
            ResourceToken.Joker: 0,
            ResourceToken.House: 0
        })

    def add_token(self, token, position):
        self[token] = position % 13

    @staticmethod
    def production_list(player_count, is_long_game):
        if player_count == 2 and not is_long_game:
            return 0, 1, 2, 2, 3, 4, 4, 5, 6, 6, 7, 8, 10
        else:
            return 0, 2, 3, 4, 5, 6, 6, 7, 7, 8, 8, 9, 10

    def production_value(self, player_count, is_long_game, resource_token):
        if resource_token in {ResourceToken.Wood, ResourceToken.Peat, ResourceToken.Grain, ResourceToken.Livestock,
                              ResourceToken.Clay, ResourceToken.Coin, ResourceToken.Joker, ResourceToken.Stone,
                              ResourceToken.Grapes}:
            if resource_token not in self:
                raise ValueError("resource_token {0} doesn't exist on the gameboard".format(resource_token))

            production_list = self.production_list(player_count, is_long_game)
            return production_list[(self[ResourceToken.Wheel] - self[resource_token]) % 13]
        elif resource_token in {ResourceToken.Wheel, ResourceToken.House}:
            raise ValueError("resource_token {0} not valid here".format(resource_token))
        else:
            raise TypeError("resource_token must be a ResourceToken")

    def produce(self, player_count, is_long_game, resource_token):
        production = self.production_value(player_count, is_long_game, resource_token)
        self[resource_token] = self[ResourceToken.Wheel]
        return production


class GameOptions(set):
    pass


class Clergy(object):
    __metaclass__ = ABCMeta

    def __init__(self, owner):
        self._owner = owner

    @abstractproperty
    def name(self):
        pass

    @property
    def owner(self):
        return self._owner

    def __repr__(self):
        return u'Clergy[{0}]'.format(self.name)


class Prior(Clergy):
    @property
    def name(self):
        return 'prior'


class LayBrother(Clergy):
    @property
    def name(self):
        return 'lay-brother'


