__author__ = 'Jurek'

from decimal import Decimal

from ..enums import Age, CardType, LandscapePlot, Variant, BuildingPlayerCount, FunctionJoiner, ResourceToken, \
    LandscapeType, Phase
from ..goods import *
from .card import Card
from .function import UseProductionWheel, UseBuilding, HaveBreaks, \
    SpendExact, SpendBreaks, SpendUnique, SpendChoices, RemoveForest, FellTrees, CutPeat, \
    GainExact, GainBreaks, GainChoices, \
    BuildSettlement, BuildBuilding, PlaceLandscape, \
    SwapTokens, AndConditional, AndOr


class Building(Card):
    def __init__(self, *args, **kwargs):
        super(Building, self).__init__(*args, **kwargs)
        self._assigned_clergy = []

    @property
    def name(self):
        raise NotImplementedError()

    @property
    def id(self):
        raise NotImplementedError()

    @property
    def card_type(self):
        return CardType.Building

    @property
    def age(self):
        raise NotImplementedError()

    @property
    def landscapes(self):
        return super(Building, self).landscapes

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
    def player_counts(self):
        return {BuildingPlayerCount.One, BuildingPlayerCount.Two, BuildingPlayerCount.TwoLong,
                BuildingPlayerCount.Three, BuildingPlayerCount.ThreeShort, BuildingPlayerCount.Four,
                BuildingPlayerCount.FourShort}

    @property
    def is_cloister(self):
        return False

    @property
    def can_be_removed(self):
        return super(Building, self).can_be_removed

    @property
    def assigned_clergy(self):
        return self._assigned_clergy

    def remove_clergy(self, clergy=None):
        if clergy:
            self._assigned_clergy.remove(clergy)
            return clergy
        clergy = self._assigned_clergy.pop()
        return clergy

    def assign_clergy(self, seat, clergy):
        if seat.game.phase != Phase.BonusRound:
            if self.assigned_clergy:
                raise Exception('clergyman {0} is already assigned'.format(self.assigned_clergy))
        self._assigned_clergy.append(clergy)


class ClayMound(Building):
    def __init__(self, *args, **kwargs):
        super(ClayMound, self).__init__(*args, **kwargs)
        self.function.add(UseProductionWheel(
            {ResourceToken.Clay, ResourceToken.Joker},
            next_step=GainExact(GoodsSet({Clay(1)}))
        ))

    @property
    def name(self):
        return 'Clay Mound'

    @property
    def id(self):
        return 'h01'

    @property
    def age(self):
        return Age.Basic

    @property
    def landscapes(self):
        return {LandscapePlot.Hillside}

    @property
    def cost(self):
        return GoodsSet()

    @property
    def economic_value(self):
        return 0

    @property
    def dwelling_value(self):
        return 3

    @property
    def can_be_overbuilt(self):
        return not self.assigned_clergy


class Farmyard(Building):
    def __init__(self, *args, **kwargs):
        super(Farmyard, self).__init__(*args, **kwargs)
        self.function.add(UseProductionWheel(
            {ResourceToken.Grain, ResourceToken.Joker},
            next_step=GainExact(GoodsSet({Grain(1)}))
        ))
        self.function.add(UseProductionWheel(
            {ResourceToken.Livestock, ResourceToken.Joker},
            next_step=GainExact(GoodsSet({Livestock(1)}))
        ), joiner=FunctionJoiner.Or)

    @property
    def name(self):
        return 'Farmyard'

    @property
    def id(self):
        return 'h02'

    @property
    def age(self):
        return Age.Basic

    @property
    def landscapes(self):
        return {LandscapePlot.Plains}

    @property
    def cost(self):
        return set()

    @property
    def economic_value(self):
        return 0

    @property
    def dwelling_value(self):
        return 2


class CloisterOffice(Building):
    def __init__(self, *args, **kwargs):
        super(CloisterOffice, self).__init__(*args, **kwargs)
        self.function.add(UseProductionWheel(
            {ResourceToken.Coin, ResourceToken.Joker},
            next_step=GainExact(GoodsSet({Coin(1)}))
        ))

    @property
    def name(self):
        return 'Cloister Office'

    @property
    def id(self):
        return 'h03'

    @property
    def age(self):
        return Age.Basic

    @property
    def landscapes(self):
        return {LandscapePlot.Plains}

    @property
    def cost(self):
        return set()

    @property
    def economic_value(self):
        return 0

    @property
    def dwelling_value(self):
        return 2

    @property
    def is_cloister(self):
        return True


class Priory(Building):
    def __init__(self, *args, **kwargs):
        super(Priory, self).__init__(*args, **kwargs)
        self.function.add(UseBuilding(criteria=self.find_buildings_with_prior))

    @property
    def name(self):
        return 'Priory'

    @property
    def id(self):
        return 'g01'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Wood(1), Clay(1)})

    @property
    def economic_value(self):
        return 4

    @property
    def dwelling_value(self):
        return 3

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_ThreePlus

    @property
    def is_cloister(self):
        return True

    def find_buildings_with_prior(self, seat):
        spaces = set()
        for s in seat.game.seats:
            spaces.update(s.find_spaces_matching(
                lambda space: space.card and space.card != self and space.card.card_type == CardType.Building and
                    space.card.assigned_clergy and any(c for c in space.card.assigned_clergy if c.name == 'prior')
            ))
        return {s.card for s in spaces}


class CloisterCourtyard(Building):
    def __init__(self, *args, **kwargs):
        super(CloisterCourtyard, self).__init__(*args, **kwargs)
        self.function.add(SpendUnique(
            GoodsSet({Wood(1), Clay(1), Peat(1), Livestock(1), Grain(1), Coin(1), PeatCoal(1), Meat(1), Grapes(1),
                      Wine(1), Flour(1), Bread(1), Ceramic(1), Stone(1), Ornament(1), Straw(1), Wonder(1), Book(1),
                      Coin(5), Reliquary(1), Malt(1), Beer(1), Whiskey(1)}),
            count=3,
            next_step=GainChoices([Clay(6), Wood(6), Peat(6), Livestock(6), Grain(6), Coin(6)])
        ))

    @property
    def name(self):
        return 'Cloister Courtyard'

    @property
    def id(self):
        return 'g02'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Wood(2)})

    @property
    def economic_value(self):
        return 4

    @property
    def dwelling_value(self):
        return 4

    @property
    def is_cloister(self):
        return True


class GrainStorage(Building):
    def __init__(self, *args, **kwargs):
        super(GrainStorage, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(Coin(1), next_step=GainExact(goods=GoodsSet({Grain(6)}), count=1)))

    @property
    def name(self):
        return 'Grain Storage'

    @property
    def id(self):
        return 'f03'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Wood(1), Straw(1)})

    @property
    def economic_value(self):
        return 3

    @property
    def dwelling_value(self):
        return 4

    @property
    def variant(self):
        return Variant.France

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_Four


class Granary(Building):
    def __init__(self, *args, **kwargs):
        super(Granary, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(Coin(1), next_step=GainExact(goods=GoodsSet({Grain(4), Book(1)}))))

    @property
    def name(self):
        return 'Granary'

    @property
    def id(self):
        return 'i03'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Wood(1)})

    @property
    def economic_value(self):
        return 2

    @property
    def dwelling_value(self):
        return 3

    @property
    def variant(self):
        return Variant.Ireland

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_Four

    @property
    def is_cloister(self):
        return True


class Windmill(Building):
    def __init__(self, *args, **kwargs):
        super(Windmill, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            Grain(1),
            max_count=7,
            next_step=GainExact(goods=GoodsSet({Flour(1), Straw(1)}))
        ))

    @property
    def name(self):
        return "Windmill"

    @property
    def id(self):
        return 'f04'

    @property
    def age(self):
        return Age.Start

    @property
    def landscapes(self):
        return {LandscapePlot.Coast, LandscapePlot.Hillside}

    @property
    def cost(self):
        return GoodsSet({Wood(3), Clay(2)})

    @property
    def economic_value(self):
        return 10

    @property
    def dwelling_value(self):
        return 6

    @property
    def variant(self):
        return Variant.France


class Malthouse(Building):
    def __init__(self, *args, **kwargs):
        super(Malthouse, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            Grain(1),
            max_count=None,
            next_step=GainExact(goods=GoodsSet({Malt(1), Straw(1)}))
        ))

    @property
    def name(self):
        return "Malthouse"

    @property
    def id(self):
        return 'i04'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Clay(2)})

    @property
    def economic_value(self):
        return 5

    @property
    def dwelling_value(self):
        return 4

    @property
    def variant(self):
        return Variant.Ireland


class Bakery(Building):
    def __init__(self, *args, **kwargs):
        super(Bakery, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Flour(1), Energy(Decimal(0.5))}),
            max_count=None,
            next_step=GainExact(goods=GoodsSet({Bread(1)}))
        ))
        self.function.add(SpendExact(
            Bread(1),
            max_count=2,
            next_step=GainExact(goods=GoodsSet({Coin(4)}))
        ), joiner=FunctionJoiner.AndThenOr)

    @property
    def name(self):
        return "Bakery"

    @property
    def id(self):
        return 'f05'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Clay(2), Straw(1)})

    @property
    def economic_value(self):
        return 4

    @property
    def dwelling_value(self):
        return 5

    @property
    def variant(self):
        return Variant.France


class Brewery(Building):
    def __init__(self, *args, **kwargs):
        super(Brewery, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Malt(1), Grain(1)}),
            max_count=None,
            next_step=GainExact(goods=GoodsSet({Beer(1)}))
        ))
        self.function.add(SpendExact(
            GoodsSet({Beer(1)}),
            next_step=GainExact(goods=GoodsSet({Coin(7)})),
        ), joiner=FunctionJoiner.AndThenOr)

    @property
    def name(self):
        return "Brewery"

    @property
    def id(self):
        return 'i05'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Stone(2), Straw(1)})

    @property
    def economic_value(self):
        return 9

    @property
    def dwelling_value(self):
        return 7

    @property
    def variant(self):
        return Variant.Ireland


class FuelMerchant(Building):
    def __init__(self, *args, **kwargs):
        super(FuelMerchant, self).__init__(*args, **kwargs)
        self.function.add(SpendBreaks(
            [Energy(3), Energy(6), Energy(9)],
            next_step=GainBreaks([Coin(5), Coin(8), Coin(10)])
        ))

    @property
    def name(self):
        return "Fuel Merchant"

    @property
    def id(self):
        return 'g06'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Clay(1), Straw(1)})

    @property
    def economic_value(self):
        return 5

    @property
    def dwelling_value(self):
        return 2

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_ThreePlus


class PeatCoalKiln(Building):
    def __init__(self, *args, **kwargs):
        super(PeatCoalKiln, self).__init__(*args, **kwargs)
        self.function.add(GainExact(goods=GoodsSet({PeatCoal(1), Coin(1)}), count=1))
        self.function.add(SpendExact(
            GoodsSet({Peat(1)}),
            max_count=None,
            next_step=GainExact(goods=GoodsSet({PeatCoal(1)})),
        ), joiner=FunctionJoiner.Additionally)

    @property
    def name(self):
        return "Peat Coal Kiln"

    @property
    def id(self):
        return 'g07'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Clay(1)})

    @property
    def economic_value(self):
        return 4

    @property
    def dwelling_value(self):
        return -2


class Market(Building):
    def __init__(self, *args, **kwargs):
        super(Market, self).__init__(*args, **kwargs)
        self.function.add(SpendUnique(
            GoodsSet({Wood(1), Clay(1), Peat(1), Livestock(1), Grain(1), Coin(1), PeatCoal(1), Meat(1), Grapes(1),
                      Wine(1), Flour(1), Bread(1), Ceramic(1), Stone(1), Ornament(1), Straw(1), Wonder(1), Book(1),
                      Coin(5), Reliquary(1)}),
            count=4,
            next_step=GainExact(goods=GoodsSet({Bread(1), Coin(7)}))
        ))

    @property
    def name(self):
        return "Market"

    @property
    def id(self):
        return 'f08'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Stone(2)})

    @property
    def economic_value(self):
        return 5

    @property
    def dwelling_value(self):
        return 8

    @property
    def variant(self):
        return Variant.France


class FalseLighthouse(Building):
    def __init__(self, *args, **kwargs):
        super(FalseLighthouse, self).__init__(*args, **kwargs)
        self.function.add(GainExact(goods=GoodsSet({Coin(3)}), count=1))
        self.function.add(GainChoices([Beer(1), Whiskey(1)]), joiner=FunctionJoiner.And)

    @property
    def name(self):
        return "False Lighthouse"

    @property
    def id(self):
        return 'i08'

    @property
    def age(self):
        return Age.Start

    @property
    def landscapes(self):
        return {LandscapePlot.Coast}

    @property
    def cost(self):
        return GoodsSet({Wood(2), Clay(1)})

    @property
    def economic_value(self):
        return 5

    @property
    def dwelling_value(self):
        return 5

    @property
    def variant(self):
        return Variant.Ireland


class CloisterGarden(Building):
    def __init__(self, *args, **kwargs):
        super(CloisterGarden, self).__init__(*args, **kwargs)
        self.used_this_action = False
        self.function.add(GainExact(goods=GoodsSet({Grapes(1)}), count=1))
        self.function.add(UseBuilding(criteria=self.find_adjacent_empty_buildings), joiner=FunctionJoiner.And)

    @property
    def name(self):
        return "Cloister Garden"

    @property
    def id(self):
        return 'f09'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Coin(3)})

    @property
    def economic_value(self):
        return 5

    @property
    def dwelling_value(self):
        return 0

    @property
    def variant(self):
        return Variant.France

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_ThreePlus

    @property
    def is_cloister(self):
        return True

    def use(self, seat, parameters):
        if not self.used_this_action:
            super(CloisterGarden, self).use(seat, parameters)
        self.used_this_action = True

    def reset(self):
        super(CloisterGarden, self).reset()
        self.used_this_action = False

    def find_adjacent_empty_buildings(self, seat):
        def _find_card_location():
            for s in seat.game.seats:
                for landscape in [s.heartland] + s.landscapes:
                    for ri in range(landscape.vertical_size):
                        for ci in range(landscape.horizontal_size):
                            space = landscape[ci][ri]
                            if space and space.card and space.card.id == self.id:
                                return s, landscape.row + ri, landscape.column + ci
            return None, None, None

        my_seat, row, column = _find_card_location()
        adjacent_spaces = my_seat.find_spaces_adjacent((row, column))

        return {space.card for space in adjacent_spaces if space.card and
                space.card.card_type == CardType.Building and not space.card.assigned_clergy}


class SpinningMill(Building):
    def __init__(self, *args, **kwargs):
        super(SpinningMill, self).__init__(*args, **kwargs)
        self.function.add(HaveBreaks(
            [Livestock(1), Livestock(5), Livestock(9)],
            next_step=GainBreaks([Coin(3), Coin(5), Coin(6)])
        ))

    @property
    def name(self):
        return "Spinning Mill"

    @property
    def id(self):
        return 'i09'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Wood(1), Straw(1)})

    @property
    def economic_value(self):
        return 3

    @property
    def dwelling_value(self):
        return 3

    @property
    def variant(self):
        return Variant.Ireland

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_ThreePlus


class Carpentry(Building):
    def __init__(self, *args, **kwargs):
        super(Carpentry, self).__init__(*args, **kwargs)
        self.function.add(RemoveForest(
            next_step=BuildBuilding()
        ))

    @property
    def name(self):
        return "Carpentry"

    @property
    def id(self):
        return 'f10'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Wood(2), Clay(1)})

    @property
    def economic_value(self):
        return 7

    @property
    def dwelling_value(self):
        return 0

    @property
    def variant(self):
        return Variant.France

    @property
    def player_counts(self):
        return {BuildingPlayerCount.Four}


class Cottage(Building):
    def __init__(self, *args, **kwargs):
        super(Cottage, self).__init__(*args, **kwargs)
        self.used_this_action = False
        self.function.add(GainExact(goods=GoodsSet({Malt(1)}), count=1))
        self.function.add(UseBuilding(criteria=self.find_adjacent_empty_buildings), joiner=FunctionJoiner.And)

    @property
    def name(self):
        return "Cottage"

    @property
    def id(self):
        return 'i10'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Stone(1), Straw(1)})

    @property
    def economic_value(self):
        return 5

    @property
    def dwelling_value(self):
        return 0

    @property
    def variant(self):
        return Variant.Ireland

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_Four

    def use(self, seat, parameters):
        if not self.used_this_action:
            super(Cottage, self).use(seat, parameters)
        self.used_this_action = True

    def reset(self):
        super(Cottage, self).reset()
        self.used_this_action = False

    def find_adjacent_empty_buildings(self, seat):
        def _find_card_location():
            for s in seat.game.seats:
                for landscape in [s.heartland] + s.landscapes:
                    for ri in range(landscape.vertical_size):
                        for ci in range(landscape.horizontal_size):
                            space = landscape[ci][ri]
                            if space and space.card and space.card.id == self.id:
                                return s, landscape.row + ri, landscape.column + ci
            return None, None, None

        my_seat, row, column = _find_card_location()
        adjacent_spaces = my_seat.find_spaces_adjacent((row, column))

        return {space.card for space in adjacent_spaces if space.card and
                space.card.card_type == CardType.Building and not space.card.assigned_clergy}


class HarborPromenade(Building):
    def __init__(self, *args, **kwargs):
        super(HarborPromenade, self).__init__(*args, **kwargs)
        self.function.add(GainExact(goods=GoodsSet({Wood(1), Wine(1), Coin(1), Ceramic(1)}), count=1))

    @property
    def name(self):
        return "Harbor Promenade"

    @property
    def id(self):
        return 'f11'

    @property
    def age(self):
        return Age.Start

    @property
    def landscapes(self):
        return {LandscapePlot.Coast}

    @property
    def cost(self):
        return GoodsSet({Wood(1), Stone(1)})

    @property
    def economic_value(self):
        return 1

    @property
    def dwelling_value(self):
        return 7

    @property
    def variant(self):
        return Variant.France


class Houseboat(Building):
    def __init__(self, *args, **kwargs):
        super(Houseboat, self).__init__(*args, **kwargs)
        self.function.add(GainExact(goods=GoodsSet({Wood(1), Malt(1), Coin(1), Peat(1)}), count=1))

    @property
    def name(self):
        return "Houseboat"

    @property
    def id(self):
        return 'i11'

    @property
    def age(self):
        return Age.Start

    @property
    def landscapes(self):
        return {LandscapePlot.Water}

    @property
    def cost(self):
        return GoodsSet({Wood(1)})

    @property
    def economic_value(self):
        return 4

    @property
    def dwelling_value(self):
        return 6

    @property
    def variant(self):
        return Variant.Ireland


class StoneMerchant(Building):
    def __init__(self, *args, **kwargs):
        super(StoneMerchant, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Food(2), Energy(1)}),
            max_count=5,
            next_step=GainExact(goods=GoodsSet({Stone(1)}))
        ))

    @property
    def name(self):
        return "Stone Merchant"

    @property
    def id(self):
        return 'g12'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Wood(1)})

    @property
    def economic_value(self):
        return 6

    @property
    def dwelling_value(self):
        return 1


class BuildersMarket(Building):
    def __init__(self, *args, **kwargs):
        super(BuildersMarket, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Coin(2)}),
            next_step=GainExact(goods=GoodsSet({Wood(2), Clay(2), Stone(1), Straw(1)}))
        ))

    @property
    def name(self):
        return "Builders' Market"

    @property
    def id(self):
        return 'g13'

    @property
    def age(self):
        return Age.Start

    @property
    def cost(self):
        return GoodsSet({Clay(2)})

    @property
    def economic_value(self):
        return 6

    @property
    def dwelling_value(self):
        return 1

    @property
    def player_counts(self):
        return {BuildingPlayerCount.TwoLong, BuildingPlayerCount.Four}


class GrapevineA(Building):
    def __init__(self, *args, **kwargs):
        super(GrapevineA, self).__init__(*args, **kwargs)
        self.function.add(UseProductionWheel(
            {ResourceToken.Grapes, ResourceToken.Joker},
            next_step=GainExact(GoodsSet({Grapes(1)}))
        ))

    @property
    def name(self):
        return "Grapevine"

    @property
    def id(self):
        return 'f14'

    @property
    def age(self):
        return Age.A

    @property
    def landscapes(self):
        return {LandscapePlot.Hillside}

    @property
    def cost(self):
        return GoodsSet({Wood(1)})

    @property
    def economic_value(self):
        return 3

    @property
    def dwelling_value(self):
        return 6

    @property
    def variant(self):
        return Variant.France

    @property
    def player_counts(self):
        return {BuildingPlayerCount.Two, BuildingPlayerCount.TwoLong, BuildingPlayerCount.Three,
                BuildingPlayerCount.ThreeShort, BuildingPlayerCount.Four, BuildingPlayerCount.FourShort}


class SacredSite(Building):
    def __init__(self, *args, **kwargs):
        super(SacredSite, self).__init__(*args, **kwargs)
        self.function.add(GainExact(goods=GoodsSet({Book(1)}), count=1))
        self.function.add(GainChoices([Grain(2), Malt(2)]), joiner=FunctionJoiner.And)
        self.function.add(GainChoices([Beer(1), Whiskey(1)]), joiner=FunctionJoiner.And)

    @property
    def name(self):
        return "Sacred Site"

    @property
    def id(self):
        return 'i14'

    @property
    def age(self):
        return Age.A

    @property
    def cost(self):
        return GoodsSet({Stone(1)})

    @property
    def economic_value(self):
        return 3

    @property
    def dwelling_value(self):
        return 6

    @property
    def variant(self):
        return Variant.Ireland


class FinancedEstate(Building):
    def __init__(self, *args, **kwargs):
        super(FinancedEstate, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Coin(1)}),
            next_step=GainExact(goods=GoodsSet({Book(1), Bread(1), Grapes(2), Flour(2)}))
        ))

    @property
    def name(self):
        return "Financed Estate"

    @property
    def id(self):
        return 'f15'

    @property
    def age(self):
        return Age.A

    @property
    def cost(self):
        return GoodsSet({Clay(1), Stone(1)})

    @property
    def economic_value(self):
        return 4

    @property
    def dwelling_value(self):
        return 6

    @property
    def variant(self):
        return Variant.France

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_Four


class DruidsHouse(Building):
    def __init__(self, *args, **kwargs):
        super(DruidsHouse, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Book(1)}),
            next_step=GainChoices(
                [Clay(5), Wood(5), Peat(5), Livestock(5), Grain(5), Coin(5)],
                next_step=GainChoices(
                    [Clay(3), Wood(3), Peat(3), Livestock(3), Grain(3), Coin(3)],
                    distinct=True
                )
            )
        ))

    @property
    def name(self):
        return "Druid's House"

    @property
    def id(self):
        return 'i15'

    @property
    def age(self):
        return Age.A

    @property
    def landscapes(self):
        return {LandscapePlot.Hillside}

    @property
    def cost(self):
        return GoodsSet({Clay(1), Stone(1)})

    @property
    def economic_value(self):
        return 6

    @property
    def dwelling_value(self):
        return 6

    @property
    def variant(self):
        return Variant.Ireland

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_Four


class CloisterChapterHouse(Building):
    def __init__(self, *args, **kwargs):
        super(CloisterChapterHouse, self).__init__(*args, **kwargs)
        self.function.add(GainExact(
            goods=GoodsSet({Clay(1), Livestock(1), Wood(1), Grain(1), Peat(1), Coin(1)}),
            count=1
        ))

    @property
    def name(self):
        return "Cloister Chapter House"

    @property
    def id(self):
        return 'g16'

    @property
    def age(self):
        return Age.A

    @property
    def cost(self):
        return GoodsSet({Clay(3), Straw(1)})

    @property
    def economic_value(self):
        return 2

    @property
    def dwelling_value(self):
        return 5

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_ThreePlus

    @property
    def is_cloister(self):
        return True


class CloisterLibrary(Building):
    def __init__(self, *args, **kwargs):
        super(CloisterLibrary, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            Coin(1),
            max_count=3,
            next_step=GainExact(goods=GoodsSet({Book(1)}))
        ))
        self.function.add(SpendExact(
            Book(1),
            next_step=GainExact(goods=GoodsSet({Meat(1), Wine(1)}))
        ), joiner=FunctionJoiner.AndThenOr)

    @property
    def name(self):
        return "Cloister Library"

    @property
    def id(self):
        return 'f17'

    @property
    def age(self):
        return Age.A

    @property
    def cost(self):
        return GoodsSet({Stone(2), Straw(1)})

    @property
    def economic_value(self):
        return 7

    @property
    def dwelling_value(self):
        return 7

    @property
    def variant(self):
        return Variant.France

    @property
    def is_cloister(self):
        return True


class Scriptorium(Building):
    def __init__(self, *args, **kwargs):
        super(Scriptorium, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Coin(1)}),
            next_step=GainExact(goods=GoodsSet({Book(1), Meat(1), Whiskey(2)}))
        ))

    @property
    def name(self):
        return "Scriptorium"

    @property
    def id(self):
        return 'i17'

    @property
    def age(self):
        return Age.A

    @property
    def cost(self):
        return GoodsSet({Wood(1), Straw(1)})

    @property
    def economic_value(self):
        return 3

    @property
    def dwelling_value(self):
        return 5

    @property
    def variant(self):
        return Variant.Ireland

    @property
    def is_cloister(self):
        return True


class CloisterWorkshop(Building):
    def __init__(self, *args, **kwargs):
        super(CloisterWorkshop, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Clay(1), Energy(1)}),
            max_count=3,
            next_step=GainExact(goods=GoodsSet({Ceramic(1)}))
        ))
        self.function.add(SpendExact(
            GoodsSet({Stone(1), Energy(1)}),
            next_step=GainExact(goods=GoodsSet({Ornament(1)}))
        ), joiner=FunctionJoiner.AndOr)

    @property
    def name(self):
        return "Cloister Workshop"

    @property
    def id(self):
        return 'g18'

    @property
    def age(self):
        return Age.A

    @property
    def cost(self):
        return GoodsSet({Wood(3)})

    @property
    def economic_value(self):
        return 7

    @property
    def dwelling_value(self):
        return 2

    @property
    def is_cloister(self):
        return True


class Slaughterhouse(Building):
    def __init__(self, *args, **kwargs):
        super(Slaughterhouse, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Livestock(1), Straw(1)}),
            max_count=None,
            next_step=GainExact(goods=GoodsSet({Meat(1)}))
        ))

    @property
    def name(self):
        return "Slaughterhouse"

    @property
    def id(self):
        return 'g19'

    @property
    def age(self):
        return Age.A

    @property
    def cost(self):
        return GoodsSet({Wood(2), Clay(2)})

    @property
    def economic_value(self):
        return 8

    @property
    def dwelling_value(self):
        return -3


class Inn(Building):
    def __init__(self, *args, **kwargs):
        super(Inn, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Wine(1)}),
            next_step=GainExact(goods=GoodsSet({Coin(6)}))
        ))
        self.function.add(SpendExact(
            GoodsSet({Food(1)}),
            max_count=7,
            next_step=GainExact(goods=GoodsSet({Coin(1)}))
        ), joiner=FunctionJoiner.AndOr)

    @property
    def name(self):
        return 'Inn'

    @property
    def id(self):
        return 'f20'

    @property
    def age(self):
        return Age.B

    @property
    def cost(self):
        return GoodsSet({Wood(2), Straw(2)})

    @property
    def economic_value(self):
        return 4

    @property
    def dwelling_value(self):
        return 6

    @property
    def variant(self):
        return Variant.France

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_ThreePlus


class Alehouse(Building):
    def __init__(self, *args, **kwargs):
        super(Alehouse, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Beer(1)}),
            next_step=GainExact(goods=GoodsSet({Coin(8)}))
        ))
        self.function.add(SpendExact(
            GoodsSet({Whiskey(1)}),
            next_step=GainExact(goods=GoodsSet({Coin(7)}))
        ), joiner=FunctionJoiner.AndOr)

    @property
    def name(self):
        return 'Alehouse'

    @property
    def id(self):
        return 'i20'

    @property
    def age(self):
        return Age.B

    @property
    def cost(self):
        return GoodsSet({Wood(1), Stone(1)})

    @property
    def economic_value(self):
        return 3

    @property
    def dwelling_value(self):
        return 6

    @property
    def variant(self):
        return Variant.Ireland

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_ThreePlus


class Winery(Building):
    def __init__(self, *args, **kwargs):
        super(Winery, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Grapes(1)}),
            max_count=None,
            next_step=GainExact(goods=GoodsSet({Wine(1)}))
        ))
        self.function.add(SpendExact(
            GoodsSet({Wine(1)}),
            next_step=GainExact(goods=GoodsSet({Coin(7)}))
        ), joiner=FunctionJoiner.AndThenOr)

    @property
    def name(self):
        return 'Winery'

    @property
    def id(self):
        return 'f21'

    @property
    def age(self):
        return Age.B

    @property
    def cost(self):
        return GoodsSet({Clay(2), Straw(2)})

    @property
    def economic_value(self):
        return 4

    @property
    def dwelling_value(self):
        return 5

    @property
    def variant(self):
        return Variant.Ireland


class WhiskeyDistillery(Building):
    def __init__(self, *args, **kwargs):
        super(WhiskeyDistillery, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Malt(1), Wood(1), Peat(1)}),
            max_count=None,
            next_step=GainExact(goods=GoodsSet({Whiskey(2)}))
        ))

    @property
    def name(self):
        return 'Whiskey Distillery'

    @property
    def id(self):
        return 'i21'

    @property
    def age(self):
        return Age.B

    @property
    def cost(self):
        return GoodsSet({Clay(2), Straw(2)})

    @property
    def economic_value(self):
        return 6

    @property
    def dwelling_value(self):
        return 5

    @property
    def variant(self):
        return Variant.Ireland


class QuarryB(Building):
    def __init__(self, *args, **kwargs):
        super(QuarryB, self).__init__(*args, **kwargs)
        self.function.add(UseProductionWheel(
            {ResourceToken.Stone, ResourceToken.Joker},
            next_step=GainExact(GoodsSet({Stone(1)}))
        ))

    @property
    def name(self):
        return 'Quarry'

    @property
    def id(self):
        return 'g22'

    @property
    def age(self):
        return Age.B

    @property
    def landscapes(self):
        return {LandscapePlot.Mountain}

    @property
    def cost(self):
        return GoodsSet({Coin(5)})

    @property
    def economic_value(self):
        return 7

    @property
    def dwelling_value(self):
        return -4


class Bathhouse(Building):
    def __init__(self, *args, **kwargs):
        super(Bathhouse, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Coin(1)}),
            next_step=GainExact(goods=GoodsSet({Book(1), Ceramic(1)}))
        ))

    @property
    def name(self):
        return 'Bathhouse'

    @property
    def id(self):
        return 'f23'

    @property
    def age(self):
        return Age.B

    @property
    def cost(self):
        return GoodsSet({Stone(1), Straw(1)})

    @property
    def economic_value(self):
        return 2

    @property
    def dwelling_value(self):
        return 6

    @property
    def variant(self):
        return Variant.France

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_Four

    @property
    def is_cloister(self):
        return True

    def use(self, seat, parameters):
        ret = super(Bathhouse, self).use(seat, parameters)
        # Return the user's clergy
        seat.return_clergy()
        # Also return the clergy on Bathhouse if there's one there
        if self.owner and self.assigned_clergy:
            self.owner.available_clergy.add(self.remove_clergy())

        return ret


class Locutory(Building):
    def __init__(self, *args, **kwargs):
        super(Locutory, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            goods=GoodsSet({Coin(2)}),
            next_step=BuildBuilding(return_prior=True)
        ))

    @property
    def name(self):
        return 'Locutory'

    @property
    def id(self):
        return 'i23'

    @property
    def age(self):
        return Age.B

    @property
    def cost(self):
        return GoodsSet({Wood(3), Clay(2)})

    @property
    def economic_value(self):
        return 7

    @property
    def dwelling_value(self):
        return 1

    @property
    def variant(self):
        return Variant.Ireland

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_Four

    @property
    def is_cloister(self):
        return True


class CloisterChurch(Building):
    def __init__(self, *args, **kwargs):
        super(CloisterChurch, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Bread(1), Wine(1)}),
            max_count=2,
            next_step=GainExact(goods=GoodsSet({Reliquary(1)}))
        ))

    @property
    def name(self):
        return 'Cloister Church'

    @property
    def id(self):
        return 'f24'

    @property
    def age(self):
        return Age.B

    @property
    def cost(self):
        return GoodsSet({Clay(5), Stone(3)})

    @property
    def economic_value(self):
        return 12

    @property
    def dwelling_value(self):
        return 9

    @property
    def variant(self):
        return Variant.France

    @property
    def is_cloister(self):
        return True


class Chapel(Building):
    def __init__(self, *args, **kwargs):
        super(Chapel, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Coin(1)}),
            next_step=GainExact(goods=GoodsSet({Book(1)}))
        ))
        self.function.add(SpendExact(
            GoodsSet({Beer(1), Whiskey(1)}),
            max_count=3,
            next_step=GainExact(goods=GoodsSet({Reliquary(1)}))
        ), joiner=FunctionJoiner.AndOr)

    @property
    def name(self):
        return 'Chapel'

    @property
    def id(self):
        return 'i24'

    @property
    def age(self):
        return Age.B

    @property
    def cost(self):
        return GoodsSet({Clay(3), Stone(3)})

    @property
    def economic_value(self):
        return 10

    @property
    def dwelling_value(self):
        return 8

    @property
    def variant(self):
        return Variant.Ireland

    @property
    def is_cloister(self):
        return True


class ChamberOfWonders(Building):
    def __init__(self, *args, **kwargs):
        super(ChamberOfWonders, self).__init__(*args, **kwargs)
        self.function.add(SpendUnique(
            GoodsSet({Wood(1), Clay(1), Peat(1), Livestock(1), Grain(1), Coin(1), PeatCoal(1), Meat(1), Grapes(1),
                      Wine(1), Flour(1), Bread(1), Ceramic(1), Stone(1), Ornament(1), Straw(1), Wonder(1), Book(1),
                      Coin(5), Reliquary(1)}),
            count=13,
            next_step=GainExact(goods=GoodsSet({Wonder(1)}))
        ))

    @property
    def name(self):
        return 'Chamber of Wonders'

    @property
    def id(self):
        return 'f25'

    @property
    def age(self):
        return Age.B

    @property
    def cost(self):
        return GoodsSet({Wood(1), Clay(1)})

    @property
    def economic_value(self):
        return 0

    @property
    def dwelling_value(self):
        return 6

    @property
    def variant(self):
        return Variant.France

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_Four


class Portico(Building):
    def __init__(self, *args, **kwargs):
        super(Portico, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Reliquary(1)}),
            next_step=GainExact(goods=GoodsSet({Clay(2), Livestock(2), Wood(2), Grain(2), Peat(2), Coin(2), Stone(2)}))
        ))

    @property
    def name(self):
        return 'Portico'

    @property
    def id(self):
        return 'i25'

    @property
    def age(self):
        return Age.B

    @property
    def cost(self):
        return GoodsSet({Clay(2)})

    @property
    def economic_value(self):
        return 2

    @property
    def dwelling_value(self):
        return 6

    @property
    def variant(self):
        return Variant.Ireland

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_Four

    @property
    def is_cloister(self):
        return True


class Shipyard(Building):
    def __init__(self, *args, **kwargs):
        super(Shipyard, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Wood(2)}),
            next_step=GainExact(goods=GoodsSet({Ornament(1), Coin(5)}))
        ))

    @property
    def name(self):
        return 'Shipyard'

    @property
    def id(self):
        return 'g26'

    @property
    def age(self):
        return Age.B

    @property
    def landscapes(self):
        return {LandscapePlot.Coast}

    @property
    def cost(self):
        return GoodsSet({Clay(4), Stone(1)})

    @property
    def economic_value(self):
        return 15

    @property
    def dwelling_value(self):
        return -2


class Palace(Building):
    def __init__(self, *args, **kwargs):
        super(Palace, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            goods=GoodsSet({Wine(1)}),
            next_step=UseBuilding(criteria=self.find_occupied_buildings)
        ))

    @property
    def name(self):
        return 'Palace'

    @property
    def id(self):
        return 'f27'

    @property
    def age(self):
        return Age.C

    @property
    def landscapes(self):
        return {LandscapePlot.Hillside}

    @property
    def cost(self):
        return GoodsSet({Coin(25)})

    @property
    def economic_value(self):
        return 25

    @property
    def dwelling_value(self):
        return 8

    def find_occupied_buildings(self, seat):
        spaces = set()
        for s in seat.game.seats:
            spaces.update(s.find_spaces_matching(
                lambda space: space.card and space.card != self and space.card.card_type == CardType.Building and
                              space.card.assigned_clergy
            ))

        return {s.card for s in spaces}


class GrandManor(Building):
    def __init__(self, *args, **kwargs):
        super(GrandManor, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            goods=GoodsSet({Whiskey(1)}),
            next_step=UseBuilding(criteria=self.find_occupied_buildings)
        ))

    @property
    def name(self):
        return 'Grand Manor'

    @property
    def id(self):
        return 'i27'

    @property
    def age(self):
        return Age.C

    @property
    def cost(self):
        return GoodsSet({Coin(20)})

    @property
    def economic_value(self):
        return 18

    @property
    def dwelling_value(self):
        return 7

    @property
    def variant(self):
        return Variant.Ireland

    def find_occupied_buildings(self, seat):
        spaces = set()
        for s in seat.game.seats:
            spaces.update(s.find_spaces_matching(
                lambda space: space.card and space.card != self and space.card.card_type == CardType.Building and
                              space.card.assigned_clergy
            ))

        return {s.card for s in spaces}


class Castle(Building):
    def __init__(self, *args, **kwargs):
        super(Castle, self).__init__(*args, **kwargs)
        self.function.add(BuildSettlement())

    @property
    def name(self):
        return 'Castle'

    @property
    def id(self):
        return 'g28'

    @property
    def age(self):
        return Age.C

    @property
    def landscapes(self):
        return {LandscapePlot.Hillside, LandscapePlot.Mountain}

    @property
    def cost(self):
        return GoodsSet({Wood(6), Stone(5)})

    @property
    def economic_value(self):
        return 15

    @property
    def dwelling_value(self):
        return 7


class QuarryC(Building):
    def __init__(self, *args, **kwargs):
        super(QuarryC, self).__init__(*args, **kwargs)
        self.function.add(UseProductionWheel(
            {ResourceToken.Stone, ResourceToken.Joker},
            next_step=GainExact(GoodsSet({Stone(1)}))
        ))

    @property
    def name(self):
        return 'Quarry'

    @property
    def id(self):
        return 'f29'

    @property
    def age(self):
        return Age.C

    @property
    def landscapes(self):
        return {LandscapePlot.Mountain}

    @property
    def cost(self):
        return GoodsSet({Coin(5)})

    @property
    def economic_value(self):
        return 7

    @property
    def dwelling_value(self):
        return -4

    @property
    def variant(self):
        return Variant.France

    @property
    def player_counts(self):
        return {BuildingPlayerCount.Three, BuildingPlayerCount.Four, BuildingPlayerCount.FourShort}


class ForestHut(Building):
    def __init__(self, *args, **kwargs):
        super(ForestHut, self).__init__(*args, **kwargs)
        self.function.add(RemoveForest(
            next_step=GainExact(goods=GoodsSet({Livestock(2), Wood(2), Stone(1)}))
        ))

    @property
    def name(self):
        return 'Forest Hut'

    @property
    def id(self):
        return 'i29'

    @property
    def age(self):
        return Age.C

    @property
    def cost(self):
        return GoodsSet({Clay(1), Straw(1)})

    @property
    def economic_value(self):
        return 1

    @property
    def dwelling_value(self):
        return 5

    @property
    def variant(self):
        return Variant.Ireland

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_ThreePlus


class TownEstate(Building):
    def __init__(self, *args, **kwargs):
        super(TownEstate, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Ceramic(1)}),
            next_step=GainExact(goods=GoodsSet({Coin(12)}))
        ))

    @property
    def name(self):
        return 'Town Estate'

    @property
    def id(self):
        return 'f30'

    @property
    def age(self):
        return Age.C

    @property
    def cost(self):
        return GoodsSet({Stone(2), Straw(2)})

    @property
    def economic_value(self):
        return 6

    @property
    def dwelling_value(self):
        return 5

    @property
    def variant(self):
        return Variant.France


class Refectory(Building):
    def __init__(self, *args, **kwargs):
        super(Refectory, self).__init__(*args, **kwargs)
        self.function.add(GainExact(goods=GoodsSet({Beer(1), Meat(1)}), count=1))
        self.function.add(SpendExact(
            GoodsSet({Meat(1)}),
            max_count=4,
            next_step=GainExact(goods=GoodsSet({Ceramic(1)}))
        ), joiner=FunctionJoiner.Additionally)

    @property
    def name(self):
        return 'Refectory'

    @property
    def id(self):
        return 'i30'

    @property
    def age(self):
        return Age.C

    @property
    def cost(self):
        return GoodsSet({Wood(1), Clay(2)})

    @property
    def economic_value(self):
        return 4

    @property
    def dwelling_value(self):
        return 5

    @property
    def variant(self):
        return Variant.Ireland

    @property
    def is_cloister(self):
        return True


class GrapevineC(Building):
    def __init__(self, *args, **kwargs):
        super(GrapevineC, self).__init__(*args, **kwargs)
        self.function.add(UseProductionWheel(
            {ResourceToken.Grapes, ResourceToken.Joker},
            next_step=GainExact(GoodsSet({Grapes(1)}))
        ))

    @property
    def name(self):
        return 'Grapevine'

    @property
    def id(self):
        return 'f31'

    @property
    def age(self):
        return Age.C

    @property
    def landscapes(self):
        return {LandscapePlot.Hillside}

    @property
    def cost(self):
        return GoodsSet({Wood(1)})

    @property
    def economic_value(self):
        return 3

    @property
    def dwelling_value(self):
        return 6

    @property
    def variant(self):
        return Variant.France

    @property
    def player_counts(self):
        return {BuildingPlayerCount.Four}


class CoalHarbor(Building):
    def __init__(self, *args, **kwargs):
        super(CoalHarbor, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({PeatCoal(1)}),
            max_count=3,
            next_step=GainExact(goods=GoodsSet({Coin(3), Whiskey(1)}))
        ))

    @property
    def name(self):
        return 'Coal Harbor'

    @property
    def id(self):
        return 'i31'

    @property
    def age(self):
        return Age.C

    @property
    def landscapes(self):
        return {LandscapePlot.Coast}

    @property
    def cost(self):
        return GoodsSet({Clay(1), Stone(2)})

    @property
    def economic_value(self):
        return 12

    @property
    def dwelling_value(self):
        return 0

    @property
    def variant(self):
        return Variant.Ireland

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_Four


class Calefactory(Building):
    def __init__(self, *args, **kwargs):
        super(Calefactory, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Coin(1)}),
            next_step=AndOr(
                next_step1=FellTrees(),
                next_step2=CutPeat()
            )
        ))

    @property
    def name(self):
        return 'Calefactory'

    @property
    def id(self):
        return 'f32'

    @property
    def age(self):
        return Age.C

    @property
    def cost(self):
        return GoodsSet({Stone(1)})

    @property
    def economic_value(self):
        return 2

    @property
    def dwelling_value(self):
        return 5

    @property
    def variant(self):
        return Variant.France

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_ThreePlus

    @property
    def is_cloister(self):
        return True


class FilialChurch(Building):
    def __init__(self, *args, **kwargs):
        super(FilialChurch, self).__init__(*args, **kwargs)
        self.function.add(SpendUnique(
            GoodsSet({Wood(1), Clay(1), Peat(1), Livestock(1), Grain(1), Coin(1), PeatCoal(1), Meat(1), Ceramic(1),
                      Stone(1), Ornament(1), Straw(1), Wonder(1), Book(1), Coin(5), Reliquary(1), Malt(1), Beer(1),
                      Whiskey(1)}),
            count=5,
            next_step=GainExact(goods=GoodsSet({Reliquary(1)}))
        ))

    @property
    def name(self):
        return 'Filial Church'

    @property
    def id(self):
        return 'i32'

    @property
    def age(self):
        return Age.C

    @property
    def cost(self):
        return GoodsSet({Wood(3), Clay(4)})

    @property
    def economic_value(self):
        return 6

    @property
    def dwelling_value(self):
        return 7

    @property
    def variant(self):
        return Variant.Ireland

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_Four

    @property
    def is_cloister(self):
        return True


class ShippingCompany(Building):
    def __init__(self, *args, **kwargs):
        super(ShippingCompany, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            goods=GoodsSet({Energy(3)}),
            next_step=UseProductionWheel(
                {ResourceToken.Joker},
                next_step=GainChoices([Meat(1), Bread(1), Wine(1)])
            )
        ))

    @property
    def name(self):
        return 'Shipping Company'

    @property
    def id(self):
        return 'f33'

    @property
    def age(self):
        return Age.C

    @property
    def landscapes(self):
        return {LandscapePlot.Coast}

    @property
    def cost(self):
        return GoodsSet({Wood(3), Clay(3)})

    @property
    def economic_value(self):
        return 8

    @property
    def dwelling_value(self):
        return 4

    @property
    def variant(self):
        return Variant.France


class Cooperage(Building):
    def __init__(self, *args, **kwargs):
        super(Cooperage, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            goods=GoodsSet({Wood(3)}),
            next_step=UseProductionWheel(
                {ResourceToken.Joker},
                next_step=GainChoices([Beer(1), Whiskey(1)])
            )
        ))

    @property
    def name(self):
        return 'Cooperage'

    @property
    def id(self):
        return 'i33'

    @property
    def age(self):
        return Age.C

    @property
    def cost(self):
        return GoodsSet({Clay(3), Straw(1)})

    @property
    def economic_value(self):
        return 5

    @property
    def dwelling_value(self):
        return 3

    @property
    def variant(self):
        return Variant.Ireland


class Sacristy(Building):
    def __init__(self, *args, **kwargs):
        super(Sacristy, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Book(1), Ceramic(1), Ornament(1), Reliquary(1)}),
            next_step=GainExact(goods=GoodsSet({Wonder(1)}))
        ))

    @property
    def name(self):
        return 'Sacristy'

    @property
    def id(self):
        return 'g34'

    @property
    def age(self):
        return Age.D

    @property
    def cost(self):
        return GoodsSet({Stone(3), Straw(2)})

    @property
    def economic_value(self):
        return 10

    @property
    def dwelling_value(self):
        return 7

    @property
    def is_cloister(self):
        return True


class ForgersWorkshop(Building):
    def __init__(self, *args, **kwargs):
        super(ForgersWorkshop, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Coin(5)}),
            next_step=GainExact(goods=GoodsSet({Reliquary(1)}))
        ))
        self.function.add(SpendExact(
            GoodsSet({Coin(10)}),
            max_count=None,
            next_step=GainExact(goods=GoodsSet({Reliquary(1)}))
        ), joiner=FunctionJoiner.Additionally)

    @property
    def name(self):
        return "Forger's Workshop"

    @property
    def id(self):
        return 'f35'

    @property
    def age(self):
        return Age.D

    @property
    def cost(self):
        return GoodsSet({Clay(2), Straw(1)})

    @property
    def economic_value(self):
        return 4

    @property
    def dwelling_value(self):
        return 2

    @property
    def variant(self):
        return Variant.France


class RoundTower(Building):
    def __init__(self, *args, **kwargs):
        super(RoundTower, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Coin(5), Whiskey(1), Points(14)}),
            next_step=GainExact(goods=GoodsSet({Wonder(1)}))
        ))

    @property
    def name(self):
        return 'Round Tower'

    @property
    def id(self):
        return 'i35'

    @property
    def age(self):
        return Age.D

    @property
    def landscapes(self):
        return {LandscapePlot.Hillside}

    @property
    def cost(self):
        return GoodsSet({Stone(4)})

    @property
    def economic_value(self):
        return 6

    @property
    def dwelling_value(self):
        return 9

    @property
    def variant(self):
        return Variant.Ireland


class PilgrimageSite(Building):
    def __init__(self, *args, **kwargs):
        super(PilgrimageSite, self).__init__(*args, **kwargs)
        self.function.add(SpendChoices(
            [Book(1), Ceramic(1), Ornament(1)],
            next_step=GainChoices([Ceramic(1), Ornament(1), Reliquary(1)])
        ))
        self.function.add(SpendChoices(
            [Book(1), Ceramic(1), Ornament(1)],
            next_step=GainChoices([Ceramic(1), Ornament(1), Reliquary(1)])
        ), FunctionJoiner.AndThenOr)

    @property
    def name(self):
        return 'Pilgrimage Site'

    @property
    def id(self):
        return 'f36'

    @property
    def age(self):
        return Age.D

    @property
    def cost(self):
        return GoodsSet({Coin(6)})

    @property
    def economic_value(self):
        return 2

    @property
    def dwelling_value(self):
        return 6

    @property
    def variant(self):
        return Variant.France

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_ThreePlus


class Camera(Building):
    def __init__(self, *args, **kwargs):
        super(Camera, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Book(1), Ceramic(1)}),
            max_count=2,
            next_step=GainExact(goods=GoodsSet({Coin(1), Clay(1), Reliquary(1)}))
        ))

    @property
    def name(self):
        return 'Camera'

    @property
    def id(self):
        return 'i36'

    @property
    def age(self):
        return Age.D

    @property
    def cost(self):
        return GoodsSet({Clay(2)})

    @property
    def economic_value(self):
        return 5

    @property
    def dwelling_value(self):
        return 3

    @property
    def variant(self):
        return Variant.Ireland

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_ThreePlus

    @property
    def is_cloister(self):
        return True


class Dormitory(Building):
    def __init__(self, *args, **kwargs):
        super(Dormitory, self).__init__(*args, **kwargs)
        self.function.add(GainExact(goods=GoodsSet({Ceramic(1)}), count=1))
        self.function.add(SpendExact(
            GoodsSet({Straw(1), Wood(1)}),
            max_count=None,
            next_step=GainExact(goods=GoodsSet({Book(1)}))
        ), joiner=FunctionJoiner.Additionally)

    @property
    def name(self):
        return 'Dormitory'

    @property
    def id(self):
        return 'f37'

    @property
    def age(self):
        return Age.D

    @property
    def cost(self):
        return GoodsSet({Clay(3)})

    @property
    def economic_value(self):
        return 3

    @property
    def dwelling_value(self):
        return 4

    @property
    def variant(self):
        return Variant.France

    @property
    def is_cloister(self):
        return True


class Bulwark(Building):
    def __init__(self, *args, **kwargs):
        super(Bulwark, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Book(1)}),
            next_step=AndConditional(
                next_step1=PlaceLandscape(LandscapeType.District),
                next_step2=PlaceLandscape(LandscapeType.Plot)
            )
        ))

    @property
    def name(self):
        return 'Bulwark'

    @property
    def id(self):
        return 'i37'

    @property
    def age(self):
        return Age.D

    @property
    def cost(self):
        return GoodsSet({Wood(2), Clay(4)})

    @property
    def economic_value(self):
        return 8

    @property
    def dwelling_value(self):
        return 6

    @property
    def variant(self):
        return Variant.Ireland


class PrintingOffice(Building):
    def __init__(self, *args, **kwargs):
        super(PrintingOffice, self).__init__(*args, **kwargs)
        self.function.add(RemoveForest(
            max_count=4,
            next_step=GainExact(goods=GoodsSet({Book(1)}))
        ))

    @property
    def name(self):
        return 'Printing Office'

    @property
    def id(self):
        return 'f38'

    @property
    def age(self):
        return Age.D

    @property
    def cost(self):
        return GoodsSet({Wood(1), Stone(2)})

    @property
    def economic_value(self):
        return 5

    @property
    def dwelling_value(self):
        return 5

    @property
    def variant(self):
        return Variant.France


class FestivalGround(Building):
    def __init__(self, *args, **kwargs):
        super(FestivalGround, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Beer(1)}),
            next_step=GainExact(
                goods=GoodsSet({Points(1)}),
                goods_pool=GoodsSet({Book(1), Ceramic(1), Ornament(1), Reliquary(1)}),
                per_lookup=FestivalGround.count_moors_forests
            )
        ))

    @property
    def name(self):
        return 'Festival Ground'

    @property
    def id(self):
        return 'i38'

    @property
    def age(self):
        return Age.D

    @property
    def cost(self):
        return GoodsSet({Coin(10)})

    @property
    def economic_value(self):
        return 3

    @property
    def dwelling_value(self):
        return 7

    @property
    def variant(self):
        return Variant.Ireland

    @staticmethod
    def count_moors_forests(seat):
        # Count the number of Moors and Forests this seat has
        return len(seat.find_spaces_matching(
            lambda space: space.card and space.card.card_type in (CardType.Moor, CardType.Forest)
        ))


class Estate(Building):
    def __init__(self, *args, **kwargs):
        super(Estate, self).__init__(*args, **kwargs)
        self.function.add(SpendChoices(
            [Energy(6), Food(10)],
            max_count=2,
            next_step=GainExact(goods=GoodsSet({Book(1), Ornament(1)}))
        ))

    @property
    def name(self):
        return 'Estate'

    @property
    def id(self):
        return 'g39'

    @property
    def age(self):
        return Age.D

    @property
    def cost(self):
        return GoodsSet({Wood(2), Stone(2)})

    @property
    def economic_value(self):
        return 5

    @property
    def dwelling_value(self):
        return 6

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_Four


class Hospice(Building):
    def __init__(self, *args, **kwargs):
        super(Hospice, self).__init__(*args, **kwargs)
        self.function.add(UseBuilding(criteria=self.find_buildings_unbuilt))

    @property
    def name(self):
        return 'Hospice'

    @property
    def id(self):
        return 'f40'

    @property
    def age(self):
        return Age.D

    @property
    def cost(self):
        return GoodsSet({Wood(3), Straw(1)})

    @property
    def economic_value(self):
        return 7

    @property
    def dwelling_value(self):
        return 5

    @property
    def variant(self):
        return Variant.France

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_ThreePlus

    @property
    def is_cloister(self):
        return True

    def find_buildings_unbuilt(self, seat):
        return seat.game.available_buildings


class Guesthouse(Building):
    def __init__(self, *args, **kwargs):
        super(Guesthouse, self).__init__(*args, **kwargs)
        self.function.add(UseBuilding(criteria=self.find_buildings_unbuilt))

    @property
    def name(self):
        return 'Guesthouse'

    @property
    def id(self):
        return 'i40'

    @property
    def age(self):
        return Age.D

    @property
    def cost(self):
        return GoodsSet({Wood(3), Straw(1)})

    @property
    def economic_value(self):
        return 7

    @property
    def dwelling_value(self):
        return 5

    @property
    def variant(self):
        return Variant.Ireland

    @property
    def player_counts(self):
        return BuildingPlayerCount.Count_ThreePlus

    def find_buildings_unbuilt(self, seat):
        return seat.game.available_buildings


class HouseOfTheBrotherhood(Building):
    def __init__(self, *args, **kwargs):
        super(HouseOfTheBrotherhood, self).__init__(*args, **kwargs)
        self.function.add(SpendExact(
            GoodsSet({Coin(5)}),
            next_step=GainExact(
                goods_lookup=HouseOfTheBrotherhood.determine_points_gain,
                goods_pool=GoodsSet({Book(1), Ceramic(1), Ornament(1), Reliquary(1)}),
                per_lookup=HouseOfTheBrotherhood.count_cloister_buildings
            )
        ))

    @property
    def name(self):
        return 'House of the Brotherhood'

    @property
    def id(self):
        return 'g41'

    @property
    def age(self):
        return Age.D

    @property
    def cost(self):
        return GoodsSet({Clay(1), Stone(1)})

    @property
    def economic_value(self):
        return 3

    @property
    def dwelling_value(self):
        return 3

    @property
    def is_cloister(self):
        return True

    @staticmethod
    def determine_points_gain(seat):
        key = BuildingPlayerCount.map(
            seat.game.number_of_players,
            'short-game' in seat.game.options,
            'long-game' in seat.game.options
        )
        if key == BuildingPlayerCount.One:
            return GoodsSet({Points(1)})
        elif key == BuildingPlayerCount.TwoLong:
            return GoodsSet({Points(Decimal(1.5))})
        else:
            return GoodsSet({Points(2)})

    @staticmethod
    def count_cloister_buildings(seat):
        # Count the number of Cloister buildings this seat has
        return len(seat.find_spaces_matching(
            lambda space: space.card and space.card.card_type == CardType.Building and space.card.is_cloister
        ))


class LoamyLandscape(Building):
    def __init__(self, *args, **kwargs):
        super(LoamyLandscape, self).__init__(*args, **kwargs)
        self.function.add(SwapTokens())
        self.function.add(UseProductionWheel(
            {ResourceToken.Clay, ResourceToken.Livestock, ResourceToken.Grain, ResourceToken.Joker},
            next_step=GainChoices([Clay(1), Livestock(1), Grain(1)])
        ), joiner=FunctionJoiner.AndThen)

    @property
    def name(self):
        return 'Loamy Landscape'

    @property
    def id(self):
        return 'fl1'

    @property
    def age(self):
        return Age.A

    @property
    def landscapes(self):
        return {LandscapePlot.ClayMound}

    @property
    def cost(self):
        return GoodsSet({Coin(3)})

    @property
    def economic_value(self):
        return 2

    @property
    def dwelling_value(self):
        return 0

__all__ = ['ClayMound', 'Farmyard', 'CloisterOffice', 'Priory', 'CloisterCourtyard', 'GrainStorage', 'Granary',
           'Windmill', 'Malthouse', 'Bakery', 'Brewery', 'FuelMerchant', 'PeatCoalKiln', 'Market', 'FalseLighthouse',
           'CloisterGarden', 'SpinningMill', 'Carpentry', 'Cottage', 'HarborPromenade', 'Houseboat', 'StoneMerchant',
           'BuildersMarket', 'GrapevineA', 'SacredSite', 'FinancedEstate', 'DruidsHouse', 'CloisterChapterHouse',
           'CloisterLibrary', 'Scriptorium', 'CloisterWorkshop', 'Slaughterhouse', 'Inn', 'Alehouse', 'Winery',
           'WhiskeyDistillery', 'QuarryB', 'Bathhouse', 'Locutory', 'CloisterChurch', 'Chapel', 'ChamberOfWonders',
           'Portico', 'Shipyard', 'Palace', 'GrandManor', 'Castle', 'QuarryC', 'ForestHut', 'TownEstate', 'Refectory',
           'GrapevineC', 'CoalHarbor', 'Calefactory', 'FilialChurch', 'ShippingCompany', 'Cooperage', 'Sacristy',
           'ForgersWorkshop', 'RoundTower', 'PilgrimageSite', 'Camera', 'Bulwark', 'Dormitory', 'PrintingOffice',
           'FestivalGround', 'Estate', 'Hospice', 'Guesthouse', 'HouseOfTheBrotherhood', 'LoamyLandscape']