__author__ = 'Jurek'
from decimal import Decimal

from .exceptions import NotEnoughGoods
from .enums import GoodsTile

__all__ = ['GoodsSet', 'Goods', 'Wood', 'Peat', 'Grain', 'Livestock', 'Clay', 'Coin', 'Stone', 'Grapes', 'Malt',
           'Flour', 'Whiskey', 'PeatCoal', 'Straw', 'Meat', 'Ceramic', 'Book', 'Reliquary', 'Ornament', 'Wine', 'Beer',
           'Bread', 'Wonder', 'Energy', 'Food', 'Money', 'Points', 'goods_types', 'goods_symbols', 'building_materials',
           'basic_goods', 'goods_map']


class GoodsSet(set):
    def __contains__(self, item):
        if not isinstance(item, Goods):
            return False
        for v in self:
            if v == item:
                return True
        return False

    def __eq__(self, other):
        if isinstance(other, set):
            for good in other:
                if good not in self:
                    return False
            for good in self:
                if isinstance(other, GoodsSet):
                    if good not in other:
                        return False
                else:
                    if not any([g for g in other if g == good]):
                        return False
            return True
        return False

    def __mul__(self, other):
        if isinstance(other, int) or isinstance(other, Decimal):
            return GoodsSet({g * other for g in self})
        else:
            raise TypeError("unsupported operand type(s) for *: '{0}' and '{1}'".format(type(self).__name__, type(other).__name__))


class Goods(object):
    def __init__(self, count=0):
        super(Goods, self).__init__()
        self._count = count

    def __eq__(self, other):
        if isinstance(other, int) or isinstance(other, Decimal):
            return self.count == other
        if isinstance(other, self.__class__):
            return self.count == other.count
        if not isinstance(other, Goods):
            raise TypeError("unsupported operand type(s) for ==: '{0}' and '{1}'".format(type(self).__name__, type(other).__name__))
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, int) or isinstance(other, Decimal):
            return self.count < other
        if isinstance(other, self.__class__):
            return self.count < other.count
        if not isinstance(other, Goods):
            raise TypeError("unsupported operand type(s) for <: '{0}' and '{1}'".format(type(self).__name__, type(other).__name__))
        raise TypeError("goods types must match")

    def __gt__(self, other):
        if isinstance(other, int) or isinstance(other, Decimal):
            return self.count > other
        if isinstance(other, self.__class__):
            return self.count > other.count
        if not isinstance(other, Goods):
            raise TypeError("unsupported operand type(s) for >: '{0}' and '{1}'".format(type(self).__name__, type(other).__name__))
        raise TypeError("goods types must match")

    def __le__(self, other):
        if isinstance(other, int) or isinstance(other, Decimal):
            return self.count <= other
        if isinstance(other, self.__class__):
            return self.count <= other.count
        if not isinstance(other, Goods):
            raise TypeError("unsupported operand type(s) for <=: '{0}' and '{1}'".format(type(self).__name__, type(other).__name__))
        raise TypeError("goods types must match")

    def __ge__(self, other):
        if isinstance(other, int) or isinstance(other, Decimal):
            return self.count >= other
        if isinstance(other, self.__class__):
            return self.count >= other.count
        if not isinstance(other, Goods):
            raise TypeError("unsupported operand type(s) for >=: '{0}' and '{1}'".format(type(self).__name__, type(other).__name__))
        raise TypeError("goods types must match")

    def __add__(self, other):
        if isinstance(other, int) or isinstance(other, Decimal):
            result = self.__class__(self.count + other)
        elif not isinstance(other, Goods):
            raise TypeError("unsupported operand type(s) for +: '{0}' and '{1}'".format(type(self).__name__, type(other).__name__))
        elif not isinstance(other, self.__class__):
            raise TypeError("goods types must match")
        else:
            result = self.__class__(self.count + other.count)
        if result.count < 0:
            raise NotEnoughGoods("cannot have less than 0 goods")
        return result

    def __sub__(self, other):
        if isinstance(other, int) or isinstance(other, Decimal):
            result = self.__class__(self.count - other)
        elif not isinstance(other, Goods):
            raise TypeError("unsupported operand type(s) for -: '{0}' and '{1}'".format(type(self).__name__, type(other).__name__))
        elif not isinstance(other, self.__class__):
            raise TypeError("goods types must match")
        else:
            result = self.__class__(self.count - other.count)
        if result.count < 0:
            raise NotEnoughGoods("cannot have less than 0 goods")
        return result

    def __mul__(self, other):
        if isinstance(other, int) or isinstance(other, Decimal):
            result = self.__class__(self.count * other)
        else:
            raise TypeError("unsupported operand type(s) for *: '{0}' and '{1}'".format(type(self).__name__, type(other).__name__))
        if result.count < 0:
            raise NotEnoughGoods("cannot have less than 0 goods")
        return result

    @property
    def name(self):
        return self.__class__.__name__.lower()

    @property
    def is_temporary(self):
        return False

    @property
    def energy_value(self):
        return 0

    @property
    def food_value(self):
        return 0

    @property
    def money_value(self):
        return 0

    @property
    def points_value(self):
        return 0

    @property
    def total_energy_value(self):
        return self.count * self.energy_value

    @property
    def total_food_value(self):
        return self.count * self.food_value

    @property
    def total_money_value(self):
        return self.count * self.money_value

    @property
    def total_points_value(self):
        return self.count * self.points_value

    @property
    def count(self):
        return self._count

    def clear(self):
        self._count = 0

    def __str__(self):
        return u'{0}({1})'.format(self.name.capitalize(), self.count)

    def __repr__(self):
        return u'{0}({1})'.format(self.name.capitalize(), self.count)

    def __hash__(self):
        return hash((self.name, self.count))


class Wood(Goods):
    @property
    def energy_value(self):
        return 1


class Peat(Goods):
    @property
    def energy_value(self):
        return 2


class Grain(Goods):
    @property
    def food_value(self):
        return 1


class Livestock(Goods):
    @property
    def food_value(self):
        return 2


class Clay(Goods):
    pass


class Coin(Goods):
    @property
    def food_value(self):
        return 1

    @property
    def money_value(self):
        return 1

    @property
    def total_points_value(self):
        return self.count / 5 * 2


class Stone(Goods):
    pass


class Grapes(Goods):
    @property
    def food_value(self):
        return 1


class Malt(Goods):
    @property
    def food_value(self):
        return 1


class Flour(Goods):
    @property
    def food_value(self):
        return 1


class Whiskey(Goods):
    @property
    def food_value(self):
        return 2

    @property
    def money_value(self):
        return 2

    @property
    def points_value(self):
        return 1


class PeatCoal(Goods):
    @property
    def name(self):
        return u'peat-coal'

    @property
    def energy_value(self):
        return 3


class Straw(Goods):
    @property
    def energy_value(self):
        return Decimal(0.5)


class Meat(Goods):
    @property
    def food_value(self):
        return 5


class Ceramic(Goods):
    @property
    def points_value(self):
        return 3


class Book(Goods):
    @property
    def points_value(self):
        return 2


class Reliquary(Goods):
    @property
    def points_value(self):
        return 8


class Ornament(Goods):
    @property
    def points_value(self):
        return 4


class Wine(Goods):
    @property
    def food_value(self):
        return 1

    @property
    def money_value(self):
        return 1

    @property
    def points_value(self):
        return 1


class Beer(Goods):
    @property
    def food_value(self):
        return 5


class Bread(Goods):
    @property
    def food_value(self):
        return 3


class Wonder(Goods):
    @property
    def points_value(self):
        return 30


class Energy(Goods):
    @property
    def is_temporary(self):
        return True

    @property
    def energy_value(self):
        return 1


class Food(Goods):
    @property
    def is_temporary(self):
        return True

    @property
    def food_value(self):
        return 1


class Points(Goods):
    @property
    def is_temporary(self):
        return True

    @property
    def points_value(self):
        return 1


class Money(Goods):
    @property
    def is_temporary(self):
        return True

    @property
    def money_value(self):
        return 1

goods_types = GoodsSet({Peat, PeatCoal, Livestock, Meat, Grapes, Wine, Flour, Bread, Wood, Whiskey, Clay, Ceramic,
                        Stone, Ornament, Grain, Straw, Wonder, Coin, Book, Reliquary, Malt, Beer})

goods_symbols = GoodsSet({Food, Energy, Money, Points})

building_materials = GoodsSet({Wood, Clay, Stone, Straw})

basic_goods = GoodsSet({Clay, Wood, Peat, Livestock, Grain, Coin})

goods_map = {
    'wood': Wood,
    'peat': Peat,
    'grain': Grain,
    'livestock': Livestock,
    'clay': Clay,
    'coin': Coin,
    'stone': Stone,
    'grapes': Grapes,
    'malt': Malt,
    'flour': Flour,
    'whiskey': Whiskey,
    'peat-coal': PeatCoal,
    'straw': Straw,
    'meat': Meat,
    'ceramic': Ceramic,
    'book': Book,
    'reliquary': Reliquary,
    'ornament': Ornament,
    'wine': Wine,
    'beer': Beer,
    'bread': Bread,
    'wonder': Wonder,
    'energy': Energy,
    'food': Food,
    'points': Points,
    'money': Money
}
