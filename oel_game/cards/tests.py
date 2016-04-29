__author__ = 'Jurek'
from django.test import TestCase

from ..enums import ResourceToken, LandscapeType
from ..exceptions import NotEnoughGoods
from ..landscapes import District, DistrictSide, PlotSide
from ..models import Game, Seat
from ..objects import Prior, LayBrother
from .building import *
from .settlement import *


class CardMethodTests(TestCase):
    def setUp(self):
        self.seat = Seat()
        self.seat.game = Game()
        self.seat.game._seats.append(self.seat)
        self.seat.game._seats.append(Seat())
        self.seat.game._seats.append(Seat())
        self.seat.game.gameboard[ResourceToken.Wheel] += 3
        self.seat.settlements.update({
            ShantyTown(owner=self.seat), FishingVillage(owner=self.seat), FarmingVillage(owner=self.seat),
            MarketTown(owner=self.seat)
        })

    def test_claymound_basic(self):
        card = ClayMound()
        card.use(self.seat, 'choose clay')
        self.assertEqual(self.seat.goods['clay'], 4)

    def test_claymound_joker_basic(self):
        card = ClayMound()
        card.use(self.seat, 'choose joker')
        self.assertEqual(self.seat.goods['clay'], 4)

    def test_farmyard_livestock_basic(self):
        card = Farmyard()
        card.use(self.seat, 'choose livestock to gain 4 livestock')
        self.assertEqual(self.seat.goods['livestock'], 4)
        self.assertEqual(self.seat.goods['grain'], 0)

    def test_farmyard_grain_basic(self):
        card = Farmyard()
        card.use(self.seat, 'choose grain to gain 4 grain')
        self.assertEqual(self.seat.goods['grain'], 4)
        self.assertEqual(self.seat.goods['livestock'], 0)

    def test_farmyard_livestock_joker_basic(self):
        card = Farmyard()
        card.use(self.seat, 'choose joker to gain 4 livestock')
        self.assertEqual(self.seat.goods['livestock'], 4)
        self.assertEqual(self.seat.goods['grain'], 0)

    def test_farmyard_grain_joker_basic(self):
        card = Farmyard()
        card.use(self.seat, 'choose joker to gain 4 grain')
        self.assertEqual(self.seat.goods['grain'], 4)
        self.assertEqual(self.seat.goods['livestock'], 0)

    def test_cloisteroffice_basic(self):
        card = CloisterOffice()
        card.use(self.seat, 'choose coin')
        self.assertEqual(self.seat.goods['coin'], 4)

    def test_cloisteroffice_joker_basic(self):
        card = CloisterOffice()
        card.use(self.seat, 'choose joker')
        self.assertEqual(self.seat.goods['coin'], 4)

    def test_priory_basic(self):
        card = Priory()
        card2 = CloisterChapterHouse()
        card2.owner = self.seat
        self.seat.heartland[3][1].add_card(card2, force_overplay=True)
        card2.assign_clergy(self.seat, Prior(self.seat))
        card.use(self.seat, 'use {0}'.format(card2.id))
        self.assertEqual(self.seat.goods['coin'], 1)
        self.assertEqual(self.seat.goods['peat'], 1)
        self.assertEqual(self.seat.goods['wood'], 1)
        self.assertEqual(self.seat.goods['clay'], 1)
        self.assertEqual(self.seat.goods['livestock'], 1)
        self.assertEqual(self.seat.goods['grain'], 1)

    def test_cloistercourtyard_basic(self):
        self.seat.goods['coin'] += 1
        self.seat.goods['wood'] += 1
        self.seat.goods['grain'] += 1
        card = CloisterCourtyard()
        card.use(self.seat, 'spend 1 coin 1 wood 1 grain to gain 6 livestock')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['wood'], 0)
        self.assertEqual(self.seat.goods['grain'], 0)
        self.assertEqual(self.seat.goods['livestock'], 6)

    def test_grainstorage_basic(self):
        self.seat.goods['coin'] += 1
        card = GrainStorage()
        card.use(self.seat, 'spend 1 coin')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['grain'], 6)

    def test_granary_basic(self):
        self.seat.goods['coin'] += 1
        card = Granary()
        card.use(self.seat, 'spend 1 coin')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['grain'], 4)
        self.assertEqual(self.seat.goods['book'], 1)

    def test_granary_0_coins(self):
        card = Granary()
        card.use(self.seat, '')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['grain'], 0)
        self.assertEqual(self.seat.goods['book'], 0)

    def test_windmill_basic(self):
        self.seat.goods['grain'] += 6
        self.seat.goods['flour'] = Flour()
        card = Windmill()
        card.use(self.seat, 'spend 6 grain')
        self.assertEqual(self.seat.goods['grain'], 0)
        self.assertEqual(self.seat.goods['flour'], 6)
        self.assertEqual(self.seat.goods['straw'], 6)

    def test_windmill_too_many(self):
        self.seat.goods['grain'] += 8
        card = Windmill()
        with self.assertRaises(ValueError):
            card.use(self.seat, 'spend 8 grain')

    def test_windmill_too_few(self):
        self.seat.goods['grain'] += 4
        card = Windmill()
        with self.assertRaises(NotEnoughGoods):
            card.use(self.seat, 'spend 6 grain')

    def test_malthouse_basic(self):
        self.seat.goods['grain'] += 6
        self.seat.goods['malt'] = Malt()
        card = Malthouse()
        card.use(self.seat, 'spend 6 grain')
        self.assertEqual(self.seat.goods['grain'], 0)
        self.assertEqual(self.seat.goods['malt'], 6)
        self.assertEqual(self.seat.goods['straw'], 6)

    def test_bakery_basic(self):
        self.seat.goods['peat'] += 2
        self.seat.goods['flour'] = Flour(6)
        self.seat.goods['bread'] = Bread()
        card = Bakery()
        card.use(self.seat, 'spend 6 flour 2 peat and spend 2 bread')
        self.assertEqual(self.seat.goods['peat'], 0)
        self.assertEqual(self.seat.goods['flour'], 0)
        self.assertEqual(self.seat.goods['bread'], 4)
        self.assertEqual(self.seat.goods['coin'], 8)

    def test_bakery_only_bake(self):
        self.seat.goods['peat'] += 2
        self.seat.goods['flour'] = Flour(6)
        self.seat.goods['bread'] = Bread()
        card = Bakery()
        card.use(self.seat, 'spend 6 flour 2 peat')
        self.assertEqual(self.seat.goods['peat'], 0)
        self.assertEqual(self.seat.goods['flour'], 0)
        self.assertEqual(self.seat.goods['bread'], 6)
        self.assertEqual(self.seat.goods['coin'], 0)

    def test_bakery_only_sell(self):
        self.seat.goods['bread'] = Bread(2)
        card = Bakery()
        card.use(self.seat, 'spend 2 bread')
        self.assertEqual(self.seat.goods['bread'], 0)
        self.assertEqual(self.seat.goods['coin'], 8)

    def test_brewery_basic(self):
        self.seat.goods['grain'] += 6
        self.seat.goods['malt'] = Malt(6)
        self.seat.goods['beer'] = Beer()
        card = Brewery()
        card.use(self.seat, 'spend 6 grain 6 malt and spend 1 beer')
        self.assertEqual(self.seat.goods['grain'], 0)
        self.assertEqual(self.seat.goods['malt'], 0)
        self.assertEqual(self.seat.goods['beer'], 5)
        self.assertEqual(self.seat.goods['coin'], 7)

    def test_brewery_only_bake(self):
        self.seat.goods['grain'] += 4
        self.seat.goods['malt'] = Malt(4)
        self.seat.goods['beer'] = Beer()
        card = Brewery()
        card.use(self.seat, 'spend 4 grain 4 malt')
        self.assertEqual(self.seat.goods['grain'], 0)
        self.assertEqual(self.seat.goods['malt'], 0)
        self.assertEqual(self.seat.goods['beer'], 4)
        self.assertEqual(self.seat.goods['coin'], 0)

    def test_brewery_only_sell(self):
        self.seat.goods['beer'] = Beer(2)
        card = Brewery()
        card.use(self.seat, 'spend 1 beer')
        self.assertEqual(self.seat.goods['beer'], 1)
        self.assertEqual(self.seat.goods['coin'], 7)

    def test_fuelmerchant_level1(self):
        self.seat.goods['peat'] += 6
        card = FuelMerchant()
        card.use(self.seat, 'spend 2 peat')
        self.assertEqual(self.seat.goods['peat'], 4)
        self.assertEqual(self.seat.goods['coin'], 5)

    def test_fuelmerchant_level2(self):
        self.seat.goods['peat'] += 6
        card = FuelMerchant()
        card.use(self.seat, 'spend 3 peat')
        self.assertEqual(self.seat.goods['peat'], 3)
        self.assertEqual(self.seat.goods['coin'], 8)

    def test_fuelmerchant_level3(self):
        self.seat.goods['peat'] += 6
        card = FuelMerchant()
        card.use(self.seat, 'spend 5 peat')
        self.assertEqual(self.seat.goods['peat'], 1)
        self.assertEqual(self.seat.goods['coin'], 10)

    def test_fuelmerchant_level0(self):
        self.seat.goods['peat'] += 6
        card = FuelMerchant()
        card.use(self.seat, 'spend 1 peat')
        self.assertEqual(self.seat.goods['peat'], 5)
        self.assertEqual(self.seat.goods['coin'], 0)

    def test_peatcoalkiln_basic(self):
        self.seat.goods['peat'] += 5
        card = PeatCoalKiln()
        card.use(self.seat, 'spend 5 peat')
        self.assertEqual(self.seat.goods['coin'], 1)
        self.assertEqual(self.seat.goods['peat'], 0)
        self.assertEqual(self.seat.goods['peat-coal'], 6)

    def test_market_basic(self):
        self.seat.goods['clay'] += 1
        self.seat.goods['wood'] += 1
        self.seat.goods['coin'] += 1
        self.seat.goods['grain'] += 1
        self.seat.goods['bread'] = Bread()
        card = Market()
        card.use(self.seat, 'spend 1 coin 1 grain 1 clay 1 wood')
        self.assertEqual(self.seat.goods['coin'], 7)
        self.assertEqual(self.seat.goods['grain'], 0)
        self.assertEqual(self.seat.goods['clay'], 0)
        self.assertEqual(self.seat.goods['wood'], 0)
        self.assertEqual(self.seat.goods['bread'], 1)

    def test_falselighthouse_basic(self):
        self.seat.goods['beer'] = Beer()
        self.seat.goods['whiskey'] = Whiskey()
        card = FalseLighthouse()
        card.use(self.seat, 'gain 1 whiskey')
        self.assertEqual(self.seat.goods['coin'], 3)
        self.assertEqual(self.seat.goods['beer'], 0)
        self.assertEqual(self.seat.goods['whiskey'], 1)

    def test_cloistergarden_basic(self):
        self.seat.goods['coin'] += 1
        self.seat.goods['grapes'] = Grapes()
        card = CloisterGarden()
        card2 = GrainStorage()
        card.owner = self.seat
        card2.owner = self.seat
        self.seat.heartland[3][1].add_card(card, force_overplay=True)
        self.seat.heartland[3][0].add_card(card2, force_overplay=True)
        card.use(self.seat, 'use {0} to spend 1 coin'.format(card2.id))
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['grain'], 6)
        self.assertEqual(self.seat.goods['grapes'], 1)

    def test_spinningmill_level1(self):
        self.seat.goods['livestock'] += 2
        card = SpinningMill()
        card.use(self.seat, '')
        self.assertEqual(self.seat.goods['coin'], 3)

    def test_spinningmill_level2(self):
        self.seat.goods['livestock'] += 5
        card = SpinningMill()
        card.use(self.seat, '')
        self.assertEqual(self.seat.goods['coin'], 5)

    def test_spinningmill_level3(self):
        self.seat.goods['livestock'] += 12
        card = SpinningMill()
        card.use(self.seat, '')
        self.assertEqual(self.seat.goods['coin'], 6)

    def test_spinningmill_level0(self):
        self.seat.goods['livestock'] += 0
        card = SpinningMill()
        card.use(self.seat, '')
        self.assertEqual(self.seat.goods['coin'], 0)

    def test_carpentry_basic(self):
        self.seat.goods['clay'] += 2
        self.seat.goods['grain'] += 2
        self.seat.goods['malt'] = Malt()
        card = Carpentry()
        card2 = Malthouse()
        self.seat.game.available_buildings.append(card2)
        card.use(self.seat, 'remove forest at 30e to build i04 at 31f and place prior to spend 2 grain')
        self.assertEqual(self.seat.goods['clay'], 0)
        self.assertEqual(self.seat.goods['grain'], 0)
        self.assertEqual(self.seat.goods['straw'], 2)
        self.assertEqual(self.seat.goods['malt'], 2)
        self.assertIsNone(self.seat.find_space((30, 'e')).card)
        self.assertEqual(self.seat.find_space((31, 'f')).card, card2)

    def test_cottage_basic(self):
        self.seat.goods['coin'] += 2
        self.seat.goods['malt'] = Malt()
        card = Cottage()
        card2 = BuildersMarket()
        card.owner = self.seat
        card2.owner = self.seat
        self.seat.heartland[3][1].add_card(card, force_overplay=True)
        self.seat.heartland[3][0].add_card(card2, force_overplay=True)
        card.use(self.seat, 'use {0} to spend 2 coin'.format(card2.id))
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['malt'], 1)
        self.assertEqual(self.seat.goods['wood'], 2)
        self.assertEqual(self.seat.goods['clay'], 2)
        self.assertEqual(self.seat.goods['stone'], 1)
        self.assertEqual(self.seat.goods['straw'], 1)

    def test_harborpromenade_basic(self):
        self.seat.goods['wine'] = Wine()
        card = HarborPromenade()
        card.use(self.seat, '')
        self.assertEqual(self.seat.goods['wood'], 1)
        self.assertEqual(self.seat.goods['wine'], 1)
        self.assertEqual(self.seat.goods['coin'], 1)
        self.assertEqual(self.seat.goods['ceramic'], 1)

    def test_houseboat_basic(self):
        self.seat.goods['malt'] = Malt()
        card = Houseboat()
        card.use(self.seat, '')
        self.assertEqual(self.seat.goods['wood'], 1)
        self.assertEqual(self.seat.goods['malt'], 1)
        self.assertEqual(self.seat.goods['coin'], 1)
        self.assertEqual(self.seat.goods['peat'], 1)

    def test_stonemerchant_basic(self):
        self.seat.goods['meat'] += 1
        self.seat.goods['peat-coal'] += 2
        self.seat.goods['beer'] = Beer(1)
        card = StoneMerchant()
        card.use(self.seat, 'spend 1 meat 1 beer 2 peat-coal')
        self.assertEqual(self.seat.goods['meat'], 0)
        self.assertEqual(self.seat.goods['beer'], 0)
        self.assertEqual(self.seat.goods['peat-coal'], 0)
        self.assertEqual(self.seat.goods['stone'], 5)

    def test_buildersmarket_basic(self):
        self.seat.goods['coin'] += 2
        card = BuildersMarket()
        card.use(self.seat, 'spend 2 coin')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['wood'], 2)
        self.assertEqual(self.seat.goods['clay'], 2)
        self.assertEqual(self.seat.goods['stone'], 1)
        self.assertEqual(self.seat.goods['straw'], 1)

    def test_grapevinea_basic(self):
        self.seat.game.gameboard.add_token(ResourceToken.Grapes, self.seat.game.gameboard[ResourceToken.Wood])
        self.seat.goods['grapes'] = Grapes()
        card = GrapevineA()
        card.use(self.seat, 'choose grapes')
        self.assertEqual(self.seat.goods['grapes'], 4)

    def test_sacredsite_basic(self):
        self.seat.goods['malt'] = Malt()
        self.seat.goods['beer'] = Beer()
        self.seat.goods['whiskey'] = Whiskey()
        card = SacredSite()
        card.use(self.seat, 'gain 2 malt gain 1 whiskey')
        self.assertEqual(self.seat.goods['book'], 1)
        self.assertEqual(self.seat.goods['grain'], 0)
        self.assertEqual(self.seat.goods['malt'], 2)
        self.assertEqual(self.seat.goods['beer'], 0)
        self.assertEqual(self.seat.goods['whiskey'], 1)

    def test_financedestate_basic(self):
        self.seat.goods['coin'] += 1
        self.seat.goods['bread'] = Bread()
        self.seat.goods['grapes'] = Grapes()
        self.seat.goods['flour'] = Flour()
        card = FinancedEstate()
        card.use(self.seat, 'spend 1 coin')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['book'], 1)
        self.assertEqual(self.seat.goods['bread'], 1)
        self.assertEqual(self.seat.goods['grapes'], 2)
        self.assertEqual(self.seat.goods['flour'], 2)

    def test_druidshouse_basic(self):
        self.seat.goods['book'] += 1
        card = DruidsHouse()
        card.use(self.seat, 'spend 1 book to gain 5 peat gain 3 livestock')
        self.assertEqual(self.seat.goods['book'], 0)
        self.assertEqual(self.seat.goods['peat'], 5)
        self.assertEqual(self.seat.goods['livestock'], 3)

    def test_cloisterchapterhouse_basic(self):
        card = CloisterChapterHouse()
        card.use(self.seat, '')
        self.assertEqual(self.seat.goods['clay'], 1)
        self.assertEqual(self.seat.goods['livestock'], 1)
        self.assertEqual(self.seat.goods['peat'], 1)
        self.assertEqual(self.seat.goods['grain'], 1)
        self.assertEqual(self.seat.goods['wood'], 1)
        self.assertEqual(self.seat.goods['coin'], 1)

    def test_cloisterlibrary_basic(self):
        self.seat.goods['coin'] += 3
        self.seat.goods['wine'] = Wine()
        card = CloisterLibrary()
        card.use(self.seat, 'spend 3 coin and spend 1 book')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['book'], 2)
        self.assertEqual(self.seat.goods['meat'], 1)
        self.assertEqual(self.seat.goods['wine'], 1)

    def test_cloisterlibrary_only_buy(self):
        self.seat.goods['coin'] += 3
        self.seat.goods['wine'] = Wine()
        card = CloisterLibrary()
        card.use(self.seat, 'spend 3 coin')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['book'], 3)
        self.assertEqual(self.seat.goods['meat'], 0)
        self.assertEqual(self.seat.goods['wine'], 0)

    def test_cloisterlibrary_only_sell_book(self):
        self.seat.goods['book'] += 1
        self.seat.goods['wine'] = Wine()
        card = CloisterLibrary()
        card.use(self.seat, 'spend 1 book')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['book'], 0)
        self.assertEqual(self.seat.goods['meat'], 1)
        self.assertEqual(self.seat.goods['wine'], 1)

    def test_scriptorium_basic(self):
        self.seat.goods['coin'] += 1
        self.seat.goods['whiskey'] = Whiskey()
        card = Scriptorium()
        card.use(self.seat, 'spend 1 coin')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['book'], 1)
        self.assertEqual(self.seat.goods['meat'], 1)
        self.assertEqual(self.seat.goods['whiskey'], 2)

    def test_cloisterworkshop_basic(self):
        self.seat.goods['clay'] += 2
        self.seat.goods['stone'] += 1
        self.seat.goods['peat-coal'] += 1
        card = CloisterWorkshop()
        card.use(self.seat, 'spend 2 clay 1 peat-coal and spend 1 stone')
        self.assertEqual(self.seat.goods['clay'], 0)
        self.assertEqual(self.seat.goods['peat-coal'], 0)
        self.assertEqual(self.seat.goods['stone'], 0)
        self.assertEqual(self.seat.goods['ceramic'], 2)
        self.assertEqual(self.seat.goods['ornament'], 1)

    def test_cloisterworkshop_just_clay(self):
        self.seat.goods['clay'] += 2
        self.seat.goods['peat-coal'] += 1
        card = CloisterWorkshop()
        card.use(self.seat, 'spend 2 clay 1 peat-coal')
        self.assertEqual(self.seat.goods['clay'], 0)
        self.assertEqual(self.seat.goods['peat-coal'], 0)
        self.assertEqual(self.seat.goods['stone'], 0)
        self.assertEqual(self.seat.goods['ceramic'], 2)
        self.assertEqual(self.seat.goods['ornament'], 0)

    def test_cloisterworkshop_just_stone(self):
        self.seat.goods['stone'] += 1
        self.seat.goods['peat-coal'] += 1
        card = CloisterWorkshop()
        card.use(self.seat, 'spend 1 stone 1 peat-coal')
        self.assertEqual(self.seat.goods['clay'], 0)
        self.assertEqual(self.seat.goods['peat-coal'], 0)
        self.assertEqual(self.seat.goods['stone'], 0)
        self.assertEqual(self.seat.goods['ceramic'], 0)
        self.assertEqual(self.seat.goods['ornament'], 1)

    def test_slaughterhouse_basic(self):
        self.seat.goods['livestock'] += 12
        self.seat.goods['straw'] += 12
        card = Slaughterhouse()
        card.use(self.seat, 'spend 12 livestock 12 straw')
        self.assertEqual(self.seat.goods['livestock'], 0)
        self.assertEqual(self.seat.goods['straw'], 0)
        self.assertEqual(self.seat.goods['meat'], 12)

    def test_inn_basic(self):
        self.seat.goods['wine'] = Wine(1)
        self.seat.goods['meat'] += 2
        card = Inn()
        card.use(self.seat, 'spend 1 wine and spend 2 meat')
        self.assertEqual(self.seat.goods['wine'], 0)
        self.assertEqual(self.seat.goods['meat'], 0)
        self.assertEqual(self.seat.goods['coin'], 13)

    def test_inn_just_wine(self):
        self.seat.goods['wine'] = Wine(1)
        card = Inn()
        card.use(self.seat, 'spend 1 wine')
        self.assertEqual(self.seat.goods['wine'], 0)
        self.assertEqual(self.seat.goods['meat'], 0)
        self.assertEqual(self.seat.goods['coin'], 6)

    def test_inn_just_food(self):
        self.seat.goods['wine'] = Wine(0)
        self.seat.goods['meat'] += 2
        card = Inn()
        card.use(self.seat, 'spend 2 meat')
        self.assertEqual(self.seat.goods['wine'], 0)
        self.assertEqual(self.seat.goods['meat'], 0)
        self.assertEqual(self.seat.goods['coin'], 7)

    def test_alehouse_basic(self):
        self.seat.goods['beer'] = Beer(1)
        self.seat.goods['whiskey'] = Whiskey(1)
        card = Alehouse()
        card.use(self.seat, 'spend 1 beer and spend 1 whiskey')
        self.assertEqual(self.seat.goods['beer'], 0)
        self.assertEqual(self.seat.goods['whiskey'], 0)
        self.assertEqual(self.seat.goods['coin'], 15)

    def test_alehouse_just_beer(self):
        self.seat.goods['beer'] = Beer(1)
        self.seat.goods['whiskey'] = Whiskey()
        card = Alehouse()
        card.use(self.seat, 'spend 1 beer')
        self.assertEqual(self.seat.goods['beer'], 0)
        self.assertEqual(self.seat.goods['whiskey'], 0)
        self.assertEqual(self.seat.goods['coin'], 8)

    def test_alehouse_just_whiskey(self):
        self.seat.goods['beer'] = Beer()
        self.seat.goods['whiskey'] = Whiskey(1)
        card = Alehouse()
        card.use(self.seat, 'spend 1 whiskey')
        self.assertEqual(self.seat.goods['beer'], 0)
        self.assertEqual(self.seat.goods['whiskey'], 0)
        self.assertEqual(self.seat.goods['coin'], 7)

    def test_winery_basic(self):
        self.seat.goods['grapes'] = Grapes(7)
        self.seat.goods['wine'] = Wine()
        card = Winery()
        card.use(self.seat, 'spend 7 grapes and spend 1 wine')
        self.assertEqual(self.seat.goods['grapes'], 0)
        self.assertEqual(self.seat.goods['wine'], 6)
        self.assertEqual(self.seat.goods['coin'], 7)

    def test_winery_just_grapes(self):
        self.seat.goods['grapes'] = Grapes(7)
        self.seat.goods['wine'] = Wine()
        card = Winery()
        card.use(self.seat, 'spend 7 grapes')
        self.assertEqual(self.seat.goods['grapes'], 0)
        self.assertEqual(self.seat.goods['wine'], 7)
        self.assertEqual(self.seat.goods['coin'], 0)

    def test_winery_just_wine(self):
        self.seat.goods['grapes'] = Grapes()
        self.seat.goods['wine'] = Wine(3)
        card = Winery()
        card.use(self.seat, 'spend 1 wine')
        self.assertEqual(self.seat.goods['grapes'], 0)
        self.assertEqual(self.seat.goods['wine'], 2)
        self.assertEqual(self.seat.goods['coin'], 7)

    def test_whiskeydistillery_basic(self):
        self.seat.goods['wood'] += 4
        self.seat.goods['peat'] += 5
        self.seat.goods['malt'] = Malt(4)
        self.seat.goods['whiskey'] = Whiskey(0)
        card = WhiskeyDistillery()
        card.use(self.seat, 'spend 4 wood 4 peat 4 malt')
        self.assertEqual(self.seat.goods['wood'], 0)
        self.assertEqual(self.seat.goods['peat'], 1)
        self.assertEqual(self.seat.goods['malt'], 0)
        self.assertEqual(self.seat.goods['whiskey'], 8)

    def test_quarryb_basic(self):
        self.seat.game.gameboard.add_token(ResourceToken.Stone, self.seat.game.gameboard[ResourceToken.Wood])
        card = QuarryB()
        card.use(self.seat, 'choose joker')
        self.assertEqual(self.seat.goods['stone'], 4)

    def test_bathhouse_basic(self):
        self.seat.goods['coin'] += 1
        card = Bathhouse()
        clergy = self.seat.clergy_pool.pop()
        self.seat.find_space((30, 'g')).card.assign_clergy(self.seat, clergy)
        clergy = self.seat.clergy_pool.pop()
        self.seat.find_space((31, 'e')).card.assign_clergy(self.seat, clergy)
        clergy = self.seat.clergy_pool.pop()
        self.seat.find_space((31, 'g')).card.assign_clergy(self.seat, clergy)

        card.use(self.seat, 'spend 1 coin')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['book'], 1)
        self.assertEqual(self.seat.goods['ceramic'], 1)
        self.assertEqual(self.seat.find_space((30, 'g')).card.assigned_clergy, [])
        self.assertEqual(self.seat.find_space((31, 'e')).card.assigned_clergy, [])
        self.assertEqual(self.seat.find_space((31, 'g')).card.assigned_clergy, [])
        self.assertEqual(len(self.seat.clergy_pool), 3)

    def test_locutory_basic(self):
        self.seat.goods['coin'] += 2
        self.seat.goods['clay'] += 2
        self.seat.goods['peat'] += 3
        card = Locutory()
        self.seat.game.available_buildings.append(PeatCoalKiln())
        priors = {c for c in self.seat.clergy_pool if c.name == 'prior'}
        prior = priors.pop()
        self.seat.clergy_pool.remove(prior)
        self.seat.find_space((31, 'e')).card.assign_clergy(self.seat, prior)

        card.use(self.seat, 'spend 2 coin to build g07 at 30f and place prior to spend 3 peat')
        self.assertEqual(self.seat.goods['coin'], 1)
        self.assertEqual(self.seat.goods['clay'], 1)
        self.assertEqual(self.seat.goods['peat'], 0)
        self.assertEqual(self.seat.goods['peat-coal'], 4)

    def test_cloisterchurch_basic(self):
        self.seat.goods['bread'] = Bread(3)
        self.seat.goods['wine'] = Wine(2)
        card = CloisterChurch()
        card.use(self.seat, 'spend 2 bread 2 wine')
        self.assertEqual(self.seat.goods['bread'], 1)
        self.assertEqual(self.seat.goods['wine'], 0)
        self.assertEqual(self.seat.goods['reliquary'], 2)

    def test_chapel_basic(self):
        self.seat.goods['coin'] += 1
        self.seat.goods['beer'] = Beer(3)
        self.seat.goods['whiskey'] = Whiskey(4)
        card = Chapel()
        card.use(self.seat, 'spend 1 coin and spend 3 beer 3 whiskey')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['book'], 1)
        self.assertEqual(self.seat.goods['beer'], 0)
        self.assertEqual(self.seat.goods['whiskey'], 1)
        self.assertEqual(self.seat.goods['reliquary'], 3)

    def test_chapel_just_book(self):
        self.seat.goods['coin'] += 1
        self.seat.goods['beer'] = Beer()
        self.seat.goods['whiskey'] = Whiskey(0)
        card = Chapel()
        card.use(self.seat, 'spend 1 coin')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['book'], 1)
        self.assertEqual(self.seat.goods['beer'], 0)
        self.assertEqual(self.seat.goods['whiskey'], 0)
        self.assertEqual(self.seat.goods['reliquary'], 0)

    def test_chapel_just_reliquary(self):
        self.seat.goods['beer'] = Beer(3)
        self.seat.goods['whiskey'] = Whiskey(4)
        card = Chapel()
        card.use(self.seat, 'spend 3 beer 3 whiskey')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['book'], 0)
        self.assertEqual(self.seat.goods['beer'], 0)
        self.assertEqual(self.seat.goods['whiskey'], 1)
        self.assertEqual(self.seat.goods['reliquary'], 3)

    def test_chamberofwonders_basic(self):
        self.seat.goods['grain'] += 1
        self.seat.goods['clay'] += 1
        self.seat.goods['wood'] += 1
        self.seat.goods['peat'] += 1
        self.seat.goods['peat-coal'] += 1
        self.seat.goods['straw'] += 1
        self.seat.goods['book'] += 1
        self.seat.goods['stone'] += 1
        self.seat.goods['livestock'] += 1
        self.seat.goods['coin'] += 6
        self.seat.goods['grapes'] = Grapes(1)
        self.seat.goods['flour'] = Flour(1)
        card = ChamberOfWonders()
        card.use(self.seat, 'spend 1 grain 1 clay 1 wood 1 peat 1 peat-coal 1 straw 1 book 1 stone 1 livestock 1 grapes 1 flour 1 coin 5 coin')
        self.assertEqual(self.seat.goods['grain'], 0)
        self.assertEqual(self.seat.goods['clay'], 0)
        self.assertEqual(self.seat.goods['wood'], 0)
        self.assertEqual(self.seat.goods['peat'], 0)
        self.assertEqual(self.seat.goods['peat-coal'], 0)
        self.assertEqual(self.seat.goods['straw'], 0)
        self.assertEqual(self.seat.goods['book'], 0)
        self.assertEqual(self.seat.goods['stone'], 0)
        self.assertEqual(self.seat.goods['livestock'], 0)
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['grapes'], 0)
        self.assertEqual(self.seat.goods['flour'], 0)
        self.assertEqual(self.seat.goods['wonder'], 1)

    def test_portico_basic(self):
        self.seat.goods['reliquary'] += 1
        card = Portico()
        card.use(self.seat, 'spend 1 reliquary')
        self.assertEqual(self.seat.goods['reliquary'], 0)
        self.assertEqual(self.seat.goods['clay'], 2)
        self.assertEqual(self.seat.goods['coin'], 2)
        self.assertEqual(self.seat.goods['peat'], 2)
        self.assertEqual(self.seat.goods['wood'], 2)
        self.assertEqual(self.seat.goods['grain'], 2)
        self.assertEqual(self.seat.goods['livestock'], 2)
        self.assertEqual(self.seat.goods['stone'], 2)

    def test_shipyard_basic(self):
        self.seat.goods['wood'] += 2
        card = Shipyard()
        card.use(self.seat, 'spend 2 wood')
        self.assertEqual(self.seat.goods['wood'], 0)
        self.assertEqual(self.seat.goods['ornament'], 1)
        self.assertEqual(self.seat.goods['coin'], 5)

    def test_palace_basic(self):
        self.seat.goods['grain'] += 6
        self.seat.goods['wine'] = Wine(1)
        self.seat.goods['flour'] = Flour()
        card = Palace()
        card2 = Windmill()
        card2.owner = self.seat
        card2.assign_clergy(self.seat, LayBrother(self.seat))
        self.seat.heartland[4][0].add_card(card2, force_overplay=True)
        card.use(self.seat, 'spend 1 wine to use {0} to spend 6 grain'.format(card2.id))
        self.assertEqual(self.seat.goods['wine'], 0)
        self.assertEqual(self.seat.goods['grain'], 0)
        self.assertEqual(self.seat.goods['flour'], 6)
        self.assertEqual(self.seat.goods['straw'], 6)

    def test_grandmanor_basic(self):
        self.seat.goods['livestock'] += 5
        self.seat.goods['beer'] = Beer(2)
        self.seat.goods['whiskey'] = Whiskey(1)
        card = GrandManor()
        card2 = Estate()
        card2.owner = self.seat
        card2.assign_clergy(self.seat, LayBrother(self.seat))
        self.seat.heartland[3][0].add_card(card2, force_overplay=True)
        card.use(self.seat, 'spend 1 whiskey to use {0} to spend 5 livestock 2 beer'.format(card2.id))
        self.assertEqual(self.seat.goods['livestock'], 0)
        self.assertEqual(self.seat.goods['beer'], 0)
        self.assertEqual(self.seat.goods['whiskey'], 0)
        self.assertEqual(self.seat.goods['book'], 2)
        self.assertEqual(self.seat.goods['ornament'], 2)

    def test_castle_basic(self):
        self.seat.goods['grain'] += 1
        self.seat.goods['wood'] += 1
        card = Castle()
        card.use(self.seat, 'build s01 at 31f with 1 grain 1 wood')
        self.assertEqual(self.seat.goods['grain'], 0)
        self.assertEqual(self.seat.goods['wood'], 0)
        self.assertIsNotNone(self.seat.heartland[3][1].card)
        self.assertEqual(self.seat.heartland[3][1].card.id, 's01')

    def test_quarryc_basic(self):
        self.seat.game.gameboard.add_token(ResourceToken.Stone, self.seat.game.gameboard[ResourceToken.Wood])
        card = QuarryC()
        card.use(self.seat, 'choose stone')
        self.assertEqual(self.seat.goods['stone'], 4)

    def test_foresthut_basic(self):
        card = ForestHut()
        card.use(self.seat, 'remove forest at 30d')
        self.assertEqual(self.seat.goods['livestock'], 2)
        self.assertEqual(self.seat.goods['wood'], 2)
        self.assertEqual(self.seat.goods['stone'], 1)
        self.assertIsNone(self.seat.heartland[1][0].card)

    def test_townestate_basic(self):
        self.seat.goods['ceramic'] += 1
        card = TownEstate()
        card.use(self.seat, 'spend 1 ceramic')
        self.assertEqual(self.seat.goods['coin'], 12)

    def test_refectory_basic(self):
        self.seat.goods['meat'] += 4
        self.seat.goods['beer'] = Beer()
        card = Refectory()
        card.use(self.seat, 'spend 4 meat')
        self.assertEqual(self.seat.goods['meat'], 1)
        self.assertEqual(self.seat.goods['beer'], 1)
        self.assertEqual(self.seat.goods['ceramic'], 4)

    def test_grapevinec_basic(self):
        self.seat.game.gameboard.add_token(ResourceToken.Grapes, self.seat.game.gameboard[ResourceToken.Wood])
        self.seat.goods['grapes'] = Grapes()
        card = GrapevineC()
        card.use(self.seat, 'choose joker')
        self.assertEqual(self.seat.goods['grapes'], 4)

    def test_coalharbor_basic(self):
        self.seat.goods['peat-coal'] += 4
        self.seat.goods['whiskey'] = Whiskey()
        card = CoalHarbor()
        card.use(self.seat, 'spend 3 peat-coal')
        self.assertEqual(self.seat.goods['peat-coal'], 1)
        self.assertEqual(self.seat.goods['coin'], 9)
        self.assertEqual(self.seat.goods['whiskey'], 3)

    def test_calefactory_basic(self):
        self.seat.goods['coin'] += 1
        self.seat.game.gameboard[ResourceToken.Joker] += 1
        card = Calefactory()
        card.use(self.seat, 'spend 1 coin to fell-trees at 30e to choose wood and cut-peat at 31c to choose joker')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['wood'], 4)
        self.assertEqual(self.seat.goods['peat'], 3)

    def test_filialchurch_basic(self):
        self.seat.goods['grain'] += 1
        self.seat.goods['clay'] += 1
        self.seat.goods['wood'] += 1
        self.seat.goods['livestock'] += 1
        self.seat.goods['coin'] += 1
        card = FilialChurch()
        card.use(self.seat, 'spend 1 grain 1 clay 1 wood 1 livestock 1 coin')
        self.assertEqual(self.seat.goods['grain'], 0)
        self.assertEqual(self.seat.goods['clay'], 0)
        self.assertEqual(self.seat.goods['wood'], 0)
        self.assertEqual(self.seat.goods['livestock'], 0)
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['reliquary'], 1)

    def test_shippingcompany_basic(self):
        self.seat.goods['peat'] += 2
        self.seat.goods['bread'] = Bread()
        self.seat.goods['wine'] = Wine()
        card = ShippingCompany()
        card.use(self.seat, 'spend 2 peat to choose joker to gain 4 meat')
        self.assertEqual(self.seat.goods['peat'], 0)
        self.assertEqual(self.seat.goods['bread'], 0)
        self.assertEqual(self.seat.goods['wine'], 0)
        self.assertEqual(self.seat.goods['meat'], 4)

    def test_cooperage_basic(self):
        self.seat.goods['wood'] += 3
        self.seat.goods['beer'] = Beer()
        self.seat.goods['whiskey'] = Whiskey()
        card = Cooperage()
        card.use(self.seat, 'spend 3 wood to choose joker to gain 4 beer')
        self.assertEqual(self.seat.goods['wood'], 0)
        self.assertEqual(self.seat.goods['beer'], 4)
        self.assertEqual(self.seat.goods['whiskey'], 0)

    def test_sacristy_basic(self):
        self.seat.goods['book'] += 1
        self.seat.goods['ceramic'] += 1
        self.seat.goods['ornament'] += 1
        self.seat.goods['reliquary'] += 1
        card = Sacristy()
        card.use(self.seat, 'spend 1 book 1 ceramic 1 ornament 1 reliquary')
        self.assertEqual(self.seat.goods['book'], 0)
        self.assertEqual(self.seat.goods['ceramic'], 0)
        self.assertEqual(self.seat.goods['ornament'], 0)
        self.assertEqual(self.seat.goods['reliquary'], 0)
        self.assertEqual(self.seat.goods['wonder'], 1)

    def test_forgersworkshop_basic(self):
        self.seat.goods['coin'] += 25
        card = ForgersWorkshop()
        card.use(self.seat, 'spend 5 coin and spend 20 coin')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['reliquary'], 3)

    def test_forgersworkshop_just_first(self):
        self.seat.goods['coin'] += 25
        card = ForgersWorkshop()
        card.use(self.seat, 'spend 5 coin')
        self.assertEqual(self.seat.goods['coin'], 20)
        self.assertEqual(self.seat.goods['reliquary'], 1)

    def test_forgersworkshop_just_second_attempted(self):
        self.seat.goods['coin'] += 25
        card = ForgersWorkshop()
        with self.assertRaises(ValueError):
            card.use(self.seat, 'spend 20 coin')

    def test_roundtower_basic(self):
        self.seat.goods['coin'] += 5
        self.seat.goods['whiskey'] = Whiskey(1)
        self.seat.goods['reliquary'] += 2
        card = RoundTower()
        card.use(self.seat, 'spend 5 coin 1 whiskey 2 reliquary')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['whiskey'], 0)
        self.assertEqual(self.seat.goods['reliquary'], 0)
        self.assertEqual(self.seat.goods['wonder'], 1)

    def test_roundtower_basic2(self):
        self.seat.goods['coin'] += 5
        self.seat.goods['whiskey'] = Whiskey(1)
        self.seat.goods['book'] += 2
        self.seat.goods['ceramic'] += 3
        self.seat.goods['ornament'] += 2
        card = RoundTower()
        card.use(self.seat, 'spend 5 coin 1 whiskey 2 book 1 ceramic 2 ornament')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['whiskey'], 0)
        self.assertEqual(self.seat.goods['book'], 0)
        self.assertEqual(self.seat.goods['ceramic'], 2)
        self.assertEqual(self.seat.goods['ornament'], 0)
        self.assertEqual(self.seat.goods['wonder'], 1)

    def test_pilgrimage_basic1(self):
        self.seat.goods['book'] += 2
        card = PilgrimageSite()
        card.use(self.seat, 'spend 1 book and spend 1 book')
        self.assertEqual(self.seat.goods['book'], 0)
        self.assertEqual(self.seat.goods['ceramic'], 2)

    def test_pilgrimage_basic2(self):
        self.seat.goods['ceramic'] += 2
        card = PilgrimageSite()
        card.use(self.seat, 'spend 1 ceramic and spend 1 ceramic')
        self.assertEqual(self.seat.goods['ceramic'], 0)
        self.assertEqual(self.seat.goods['ornament'], 2)

    def test_pilgrimage_basic3(self):
        self.seat.goods['ornament'] += 2
        card = PilgrimageSite()
        card.use(self.seat, 'spend 1 ornament and spend 1 ornament')
        self.assertEqual(self.seat.goods['ornament'], 0)
        self.assertEqual(self.seat.goods['reliquary'], 2)

    def test_pilgrimage_basic4(self):
        self.seat.goods['book'] += 1
        card = PilgrimageSite()
        card.use(self.seat, 'spend 1 book and spend 1 ceramic')
        self.assertEqual(self.seat.goods['book'], 0)
        self.assertEqual(self.seat.goods['ceramic'], 0)
        self.assertEqual(self.seat.goods['ornament'], 1)

    def test_pilgrimage_basic5(self):
        self.seat.goods['ceramic'] += 1
        card = PilgrimageSite()
        card.use(self.seat, 'spend 1 ceramic and spend 1 ornament')
        self.assertEqual(self.seat.goods['ceramic'], 0)
        self.assertEqual(self.seat.goods['ornament'], 0)
        self.assertEqual(self.seat.goods['reliquary'], 1)

    def test_pilgrimage_basic6(self):
        self.seat.goods['book'] += 1
        self.seat.goods['ornament'] += 1
        card = PilgrimageSite()
        card.use(self.seat, 'spend 1 book and spend 1 ornament')
        self.assertEqual(self.seat.goods['book'], 0)
        self.assertEqual(self.seat.goods['ceramic'], 1)
        self.assertEqual(self.seat.goods['ornament'], 0)
        self.assertEqual(self.seat.goods['reliquary'], 1)

    def test_camera_basic(self):
        self.seat.goods['book'] += 2
        self.seat.goods['ceramic'] += 2
        card = Camera()
        card.use(self.seat, 'spend 2 book 2 ceramic')
        self.assertEqual(self.seat.goods['book'], 0)
        self.assertEqual(self.seat.goods['ceramic'], 0)
        self.assertEqual(self.seat.goods['coin'], 2)
        self.assertEqual(self.seat.goods['clay'], 2)
        self.assertEqual(self.seat.goods['reliquary'], 2)

    def test_dormitory_basic(self):
        self.seat.goods['straw'] += 5
        self.seat.goods['wood'] += 7
        card = Dormitory()
        card.use(self.seat, 'spend 5 straw 5 wood')
        self.assertEqual(self.seat.goods['ceramic'], 1)
        self.assertEqual(self.seat.goods['straw'], 0)
        self.assertEqual(self.seat.goods['wood'], 2)
        self.assertEqual(self.seat.goods['book'], 5)

    def test_bulwark_basic(self):
        self.seat.goods['book'] += 1
        card = Bulwark()
        card.use(self.seat, 'spend 1 book to place district9 as side1 at 32 and place plot6 as side1 at 30')
        self.assertEqual(self.seat.goods['book'], 0)
        self.assertEqual(len(self.seat.landscapes), 2)
        self.assertEqual(self.seat.landscapes[0].id, 'district9')
        self.assertEqual(self.seat.landscapes[0].landscape_side, DistrictSide.MoorForestForestHillsideHillside)
        self.assertIsNotNone(self.seat.landscapes[0].landscape_spaces[0][0].card)
        self.assertEqual(self.seat.landscapes[0].landscape_spaces[0][0].card.card_type, CardType.Moor)
        self.assertEqual(self.seat.landscapes[1].id, 'plot6')
        self.assertEqual(self.seat.landscapes[1].landscape_side, PlotSide.Coastal)

    def test_bulwark_no_districts(self):
        self.seat.goods['book'] += 1
        self.seat.game.available_landscapes[LandscapeType.District] = []
        card = Bulwark()
        card.use(self.seat, 'spend 1 book to place plot1 as side1 at 30')
        self.assertEqual(self.seat.goods['book'], 0)
        self.assertEqual(len(self.seat.landscapes), 1)
        self.assertEqual(self.seat.landscapes[0].id, 'plot1')
        self.assertEqual(self.seat.landscapes[0].landscape_side, PlotSide.Coastal)

    def test_bulwark_no_plots(self):
        self.seat.goods['book'] += 1
        self.seat.game.available_landscapes[LandscapeType.Plot] = []
        card = Bulwark()
        card.use(self.seat, 'spend 1 book to place district7 as side1 at 32')
        self.assertEqual(self.seat.goods['book'], 0)
        self.assertEqual(len(self.seat.landscapes), 1)
        self.assertEqual(self.seat.landscapes[0].id, 'district7')
        self.assertEqual(self.seat.landscapes[0].landscape_side, DistrictSide.MoorForestForestHillsideHillside)
        self.assertIsNotNone(self.seat.landscapes[0].landscape_spaces[0][0].card)
        self.assertEqual(self.seat.landscapes[0].landscape_spaces[0][0].card.card_type, CardType.Moor)

    def test_printingoffice_basic(self):
        card = PrintingOffice()
        card.use(self.seat, 'remove forest at 30d 30e 31d')
        self.assertEqual(self.seat.goods['book'], 3)

    def test_festivalground_basic(self):
        self.seat.goods['beer'] = Beer(1)
        d1 = District('district1', 2)
        d1.landscape_side = DistrictSide.MoorForestForestHillsideHillside
        d1.row = 29
        self.seat.landscapes.append(d1)
        d2 = District('district2', 3)
        d2.landscape_side = DistrictSide.ForestPlainsPlainsPlainsHillside
        d2.row = 28
        self.seat.landscapes.append(d2)
        card = FestivalGround()
        card.use(self.seat, 'spend 1 beer to gain 2 book 1 ornament')
        self.assertEqual(self.seat.goods['beer'], 0)
        self.assertEqual(self.seat.goods['book'], 2)
        self.assertEqual(self.seat.goods['ornament'], 1)

    def test_estate_food(self):
        self.seat.goods['meat'] += 4
        card = Estate()
        card.use(self.seat, 'spend 4 meat')
        self.assertEqual(self.seat.goods['meat'], 0)
        self.assertEqual(self.seat.goods['book'], 2)
        self.assertEqual(self.seat.goods['ornament'], 2)

    def test_estate_energy(self):
        self.seat.goods['peat-coal'] += 4
        card = Estate()
        card.use(self.seat, 'spend 4 peat-coal')
        self.assertEqual(self.seat.goods['peat-coal'], 0)
        self.assertEqual(self.seat.goods['book'], 2)
        self.assertEqual(self.seat.goods['ornament'], 2)

    def test_estate_food_energy(self):
        self.seat.goods['peat'] += 2
        self.seat.goods['peat-coal'] += 1
        self.seat.goods['bread'] = Bread(4)
        card = Estate()
        card.use(self.seat, 'spend 4 bread 2 peat 1 peat-coal')
        self.assertEqual(self.seat.goods['bread'], 0)
        self.assertEqual(self.seat.goods['peat'], 0)
        self.assertEqual(self.seat.goods['peat-coal'], 0)
        self.assertEqual(self.seat.goods['book'], 2)
        self.assertEqual(self.seat.goods['ornament'], 2)

    def test_hospice_basic(self):
        self.seat.goods['bread'] = Bread(2)
        self.seat.goods['wine'] = Wine(1)
        card = Hospice()
        card2 = CloisterChurch()
        self.seat.game.available_buildings.append(card2)
        card.use(self.seat, 'use {0} to spend 1 bread 1 wine'.format(card2.id))
        self.assertEqual(self.seat.goods['bread'], 1)
        self.assertEqual(self.seat.goods['wine'], 0)
        self.assertEqual(self.seat.goods['reliquary'], 1)

    def test_guesthouse_basic(self):
        self.seat.goods['book'] += 1
        card = Guesthouse()
        card2 = DruidsHouse()
        self.seat.game.available_buildings.append(card2)
        card.use(self.seat, 'use {0} to spend 1 book to gain 5 peat gain 3 wood'.format(card2.id))
        self.assertEqual(self.seat.goods['book'], 0)
        self.assertEqual(self.seat.goods['peat'], 5)
        self.assertEqual(self.seat.goods['wood'], 3)

    def test_houseofthebrotherhood_basic(self):
        self.seat.goods['coin'] += 5
        card = HouseOfTheBrotherhood()
        card.use(self.seat, 'spend 5 coin to gain 1 book')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['book'], 1)

    def test_houseofthebrotherhood_2player_long(self):
        self.seat.goods['coin'] += 5
        self.seat.game.seats.pop()
        self.seat.game.options.add('long-game')
        card2 = Priory()
        card2.owner = self.seat
        self.seat.heartland[3][1].add_card(card2, force_overplay=True)
        card3 = CloisterCourtyard()
        card3.owner = self.seat
        self.seat.heartland[3][0].add_card(card3, force_overplay=True)
        card4 = Sacristy()
        card4.owner = self.seat
        self.seat.heartland[2][0].add_card(card4, force_overplay=True)

        card = HouseOfTheBrotherhood()
        card.use(self.seat, 'spend 5 coin to gain 1 book 1 ornament')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['book'], 1)
        self.assertEqual(self.seat.goods['ornament'], 1)

    def test_houseofthebrotherhood_solo_game(self):
        self.seat.goods['coin'] += 5
        self.seat.game.seats.pop()
        self.seat.game.seats.pop()
        card2 = Priory()
        card2.owner = self.seat
        self.seat.heartland[3][1].add_card(card2, force_overplay=True)
        card3 = CloisterCourtyard()
        card3.owner = self.seat
        self.seat.heartland[3][0].add_card(card3, force_overplay=True)
        card4 = Sacristy()
        card4.owner = self.seat
        self.seat.heartland[2][0].add_card(card4, force_overplay=True)

        card = HouseOfTheBrotherhood()
        card.use(self.seat, 'spend 5 coin to gain 1 ceramic')
        self.assertEqual(self.seat.goods['coin'], 0)
        self.assertEqual(self.seat.goods['ceramic'], 1)

    def test_houseofthebrotherhood_too_many_goods(self):
        self.seat.goods['coin'] += 5
        card2 = Priory()
        card2.owner = self.seat
        self.seat.heartland[3][1].add_card(card2, force_overplay=True)
        card3 = CloisterCourtyard()
        card3.owner = self.seat
        self.seat.heartland[3][0].add_card(card3, force_overplay=True)
        card4 = Sacristy()
        card4.owner = self.seat
        self.seat.heartland[2][0].add_card(card4, force_overplay=True)

        card = HouseOfTheBrotherhood()
        with self.assertRaises(ValueError):
            card.use(self.seat, 'spend 5 coin to gain 3 ceramic')
