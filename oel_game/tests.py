import random

from django.contrib.auth.models import User
from django.test import TestCase

from .cards.building import PeatCoalKiln
from .enums import Gameboard, Variant, LandscapeType
from .exceptions import NotEnoughGoods, LandscapeAlreadyPurchased, BuildingPresent, InvalidLandscapePlot, SpaceNotFound
from .models import Game, Seat, GameLog
from .objects import GameOptions
from .goods import Coin


# TODO -- Need to make tests for GoodsSet and various Goods comparisons and operations


def create_user(**kwargs):
    return User.objects.create(**kwargs)


def create_and_start_game(player_count, variant, options):
    users = []
    for i in range(player_count):
        users.append(create_user(username='user_{0}'.format(i + 1)))

    game = Game.objects.create_game(player_count, variant, options, owner=users[0])
    for user in users:
        game.join(user)

    game.start()
    # Refresh from the DB
    game = Game.objects.get(pk=game.id)
    return game, users


class GameMethodTests(TestCase):
    def test_game_creation(self):
        """
        Let's verify that we can create a game properly
        """
        game = Game.objects.create_game(4, Variant.France, GameOptions(), owner=create_user())
        self.assertEqual(game.variant, Variant.France)
        self.assertEqual(game.number_of_seats, 4)
        self.assertEqual(game.number_of_players, 4)

    def test_game_setup(self):
        """
        Add some non-standard options to verify that they're getting set up properly
        """
        options = GameOptions()
        options.add('short-game')
        options.add('loamy-landscape')
        options.add('randomize-seats')
        game = Game.objects.create_game(4, Variant.France, options, owner=create_user())
        self.assertEqual('short-game' in game.options, True)
        self.assertEqual('loamy-landscape' in game.options, True)
        self.assertEqual('randomize-seats' in game.options, True)
        self.assertEqual('long-game' in game.options, False)
        self.assertEqual(game.gameboard.gameboard_type, Gameboard.ShortThreeFourPlayer)

    def test_game_join(self):
        """
        We should be able to join a game
        """
        owner = create_user()
        options = GameOptions()
        game = Game.objects.create_game(4, Variant.France, options, owner=owner)
        game.join(owner)
        self.assertEqual(len([s for s in game.players if s.player == owner]), 1)

    def test_game_start(self):
        """
        A game should be able to be started
        """
        # The random seed is needed to properly test the seat randomization
        options = GameOptions()
        options.add('randomize-seats')
        random.seed('vwxyz1234567890')
        game, users = create_and_start_game(3, Variant.Ireland, options)

        # Exact ordering doesn't *really* matter, but it should be consistent for all test runs.
        # The gamestate needs to be able to be created the same way every single time
        self.assertEqual(game.seats[0].player.username, 'user_2')
        self.assertEqual(game.seats[1].player.username, 'user_1')
        self.assertEqual(game.seats[2].player.username, 'user_3')

        self.assertEqual(len(game.available_buildings), 10)
        self.assertEqual(game.action_seat.player, users[1])
        self.assertIn('malt', game.action_seat.goods)

        # This should go in its own test
        game.add_command('convert 1 grain to 1 straw', executor=game.action_seat)
        game.build_gamestate()
        self.assertEqual(game.action_seat.goods['grain'], 0)
        self.assertEqual(game.action_seat.goods['straw'], 1)

    def test_game_one_player(self):
        """
        Test that one-player games are set up properly
        """
        options = GameOptions()
        game, users = create_and_start_game(1, Variant.Ireland, options)

        self.assertEqual(game.number_of_seats, 2)
        self.assertEqual(len(game.available_buildings), 12)
        self.assertEqual(game.available_landscapes[LandscapeType.District][0].cost, Coin(8))
        self.assertEqual(game.available_landscapes[LandscapeType.Plot][0].cost, Coin(7))

    def test_buy_landscape(self):
        """
        A player should be able to buy a landscape (district) and place it
        """
        options = GameOptions()
        options.add('randomize-seats')
        game, users = create_and_start_game(3, Variant.Ireland, options)

        game.action_seat.goods['coin'] += 5
        game.add_command('buy DISTRICT as SIDE1 at 29', executor=game.action_seat)
        game.build_gamestate()
        self.assertEqual(game.action_seat.landscapes[0].cost, 2)
        self.assertEqual(len(game.available_landscapes[LandscapeType.District]), 8)
        self.assertEqual(game.action_seat.landscapes[0].row, 29)

    def test_buy_landscape_without_money(self):
        """
        A player shouldn't be able to buy a landscape (district) without enough coins
        """
        options = GameOptions()
        options.add('randomize-seats')
        game, users = create_and_start_game(3, Variant.Ireland, options)

        game.add_command('buy district as side2 at 32', executor=game.action_seat)
        with self.assertRaises(NotEnoughGoods):
            game.build_gamestate()

    def test_find_space_standard(self):
        """
        A player's find_space function should work
        """
        options = GameOptions()
        options.add('randomize-seats')
        game, users = create_and_start_game(3, Variant.Ireland, options)

        # 4 standard cases
        self.assertEqual(game.action_seat.find_space(('30', 'c')).card.name, 'Moor')
        self.assertEqual(game.action_seat.find_space((30, 'g')).card.name, 'Clay Mound')
        self.assertEqual(game.action_seat.find_space(('31', 'e')).card.name, 'Farmyard')
        self.assertIsNone(game.action_seat.find_space((31, 'f')).card)
        # Bunch of edge cases
        self.assertIsNone(game.action_seat.find_space(('30', 'a')))
        self.assertIsNone(game.action_seat.find_space(('32', 'c')))
        self.assertIsNone(game.action_seat.find_space(('17', 'p')))
        self.assertIsNone(game.action_seat.find_space(('-1', ']')))

    def test_buy_landscapes_complicated_layout(self):
        """
        A very complicated landscape layout should be doable.  Example:
               MV
               M^
               Mv
          DDDDDM^
          DDDDD
          DDDDD
          DDDDD
          HHHHH
        CCHHHHH
        CC
        CC
        CC
        """
        options = GameOptions()
        options.add('randomize-seats')
        game, users = create_and_start_game(3, Variant.France, options)

        game.action_seat.goods['coin'] += 25
        game.add_commands([
            'buy plot as side1 at 31',
            'buy plot as side1 at 33',
            'buy district as side1 at 29',
            'buy district as side2 at 29',
            'buy district as side2 at 28',
            'buy district as side1 at 27',
            'buy plot as side2 at 26',
            'buy plot as side2 at 24',
        ], executor=game.action_seat)

        # This now fails because players can only build 1 Landscape per Action/Settlement
        with self.assertRaises(LandscapeAlreadyPurchased):
            game.build_gamestate()
        self.assertEqual(len(game.action_seat.landscapes), 1)
        self.assertEqual(len(game.available_landscapes[LandscapeType.District]), 9)
        self.assertEqual(len(game.available_landscapes[LandscapeType.Plot]), 8)
        self.assertEqual(game.action_seat.goods['coin'].total_money_value, 23)

    def test_build_building_id(self):
        """
        A player should be able to build a building by id
        """
        options = GameOptions()
        options.add('randomize-seats')
        game, users = create_and_start_game(3, Variant.Ireland, options)

        game.add_command('build g07 at 30f', executor=game.action_seat)
        game.build_gamestate()
        self.assertEqual(game.action_seat.goods['clay'].count, 0)
        space = game.action_seat.find_space((30, 'f'))
        self.assertIsNotNone(space)
        self.assertEqual(space.card.name, 'Peat Coal Kiln')

#    def test_build_building_name(self):
#        """
#        A player should be able to build a building by name
#        """
#        options = GameOptions()
#        options.add('randomize-seats')
#        game, users = create_and_start_game(3, Variant.France, options)
#
#        game.add_command('build peat COAL KILN at 31f', executor=game.action_seat)
#        game.build_gamestate()
#        self.assertEqual(game.action_seat.goods['clay'].count, 0)
#        space = game.action_seat.find_space((31, 'f'))
#        self.assertIsNotNone(space)
#        self.assertEqual(space.card.name, 'Peat Coal Kiln')

    def test_build_building_existing(self):
        """
        Players shouldn't be able to overbuild an existing card (Forest, Moor, or other Building)
        """
        options = GameOptions()
        options.add('randomize-seats')
        game, users = create_and_start_game(3, Variant.Ireland, options)

        game.add_command('build g07 at 30e', executor=game.action_seat)
        with self.assertRaises(BuildingPresent):
            game.build_gamestate()

    def test_build_building_not_enough_resources(self):
        """
        Make sure resource checking is upheld
        """
        options = GameOptions()
        options.add('randomize-seats')
        game, users = create_and_start_game(3, Variant.Ireland, options)

        game.add_command('build i05 at 30f', executor=game.action_seat)
        with self.assertRaises(NotEnoughGoods):
            game.build_gamestate()

    def test_build_building_wrong_landscape(self):
        """
        Make sure landscape type is enforced
        """
        options = GameOptions()
        options.add('randomize-seats')
        game, users = create_and_start_game(3, Variant.Ireland, options)

        game.add_command('build i11 at 30f', executor=game.action_seat)
        with self.assertRaises(InvalidLandscapePlot):
            game.build_gamestate()

    def test_buy_landscape_build_building(self):
        """
        A player should be able to buy a landscape (and place it) and build a building on it
        """
        options = GameOptions()
        options.add('randomize-seats')
        game, users = create_and_start_game(3, Variant.Ireland, options)

        game.action_seat.goods['coin'] += 5
        game.add_command('buy PLOT as SIDE1 at 31', executor=game.action_seat)
        game.build_gamestate()
        game.add_command('build i11 at 32a', executor=game.action_seat)
        game.build_gamestate()
        self.assertEqual(game.action_seat.goods['wood'].count, 0)
        space = game.action_seat.find_space((32, 'a'))
        self.assertIsNotNone(space)
        self.assertEqual(space.card.name, 'Houseboat')

    def test_build_building_no_coordinate(self):
        """
        Ensure a bad coordinate is handled
        """
        options = GameOptions()
        options.add('randomize-seats')
        game, users = create_and_start_game(3, Variant.Ireland, options)

        game.add_command('build i11 at 99f', executor=game.action_seat)
        with self.assertRaises(SpaceNotFound):
            game.build_gamestate()

    def test_build_cloister_building(self):
        """
        Make sure building a Cloister building works
        """
        options = GameOptions()
        options.add('randomize-seats')
        game, users = create_and_start_game(3, Variant.Ireland, options)

        game.add_command('build g01 at 31f', executor=game.action_seat)
        game.build_gamestate()
        self.assertEqual(game.action_seat.goods['wood'].count, 0)
        self.assertEqual(game.action_seat.goods['clay'].count, 0)
        space = game.action_seat.find_space((31, 'f'))
        self.assertIsNotNone(space)
        self.assertEqual(space.card.name, 'Priory')

    def test_build_cloister_away_from_others(self):
        """
        Make sure building a Cloister building away from others is checked for
        """
        options = GameOptions()
        options.add('randomize-seats')
        game, users = create_and_start_game(3, Variant.Ireland, options)

        game.add_command('build g01 at 30f', executor=game.action_seat)
        with self.assertRaises(InvalidLandscapePlot):
            game.build_gamestate()

    def test_build_building_and_use_prior(self):
        """
        Make sure building a building and using your Prior works
        """
        options = GameOptions()
        options.add('randomize-seats')
        game, users = create_and_start_game(3, Variant.Ireland, options)

        game.action_seat.goods['coin'] += 3
        game.add_command('buy PLOT as SIDE1 at 30', executor=game.action_seat)
        game.build_gamestate()
        game.add_command('build i11 at 30a and place prior', executor=game.action_seat)
        game.build_gamestate()
        self.assertEqual(game.action_seat.goods['wood'].count, 1)
        self.assertEqual(game.action_seat.goods['clay'].count, 1)
        self.assertEqual(game.action_seat.goods['coin'].count, 2)
        self.assertEqual(game.action_seat.goods['malt'].count, 1)
        self.assertEqual(game.action_seat.goods['peat'].count, 2)
        space = game.action_seat.find_space((30, 'a'))
        self.assertEqual(len(space.card.assigned_clergy), 1)
        self.assertEqual(space.card.assigned_clergy[0].name, 'prior')

    def test_build_building_and_use_prior_2(self):
        """
        Make sure building a building and using your Prior works
        """
        options = GameOptions()
        options.add('randomize-seats')
        game, users = create_and_start_game(3, Variant.Ireland, options)

        game.add_command('convert 1 grain to 1 straw; build i09 at 30f and place prior', executor=game.action_seat)
        game.build_gamestate()
        self.assertEqual(game.action_seat.goods['wood'].count, 0)
        self.assertEqual(game.action_seat.goods['coin'].count, 4)
        self.assertEqual(game.action_seat.goods['grain'].count, 0)
        self.assertEqual(game.action_seat.goods['straw'].count, 0)
        self.assertEqual(game.action_seat.goods['livestock'].count, 1)
        space = game.action_seat.find_space((30, 'f'))
        self.assertEqual(len(space.card.assigned_clergy), 1)
        self.assertEqual(space.card.assigned_clergy[0].name, 'prior')

    def test_take_action_and_pass(self):
        """
        Make sure passing is a valid command to execute
        """
        options = GameOptions()
        options.add('randomize-seats')
        game, users = create_and_start_game(3, Variant.Ireland, options)

        active_seat = game.action_seat
        game.add_commands(['convert 1 grain to 1 straw; build i09 at 30f and place prior', 'pass'], executor=active_seat)
        game.build_gamestate()

        self.assertEqual(game.action_seat, game.seats[1])

    def test_play_game(self):
        """
        Play an entire game
        """
        options = GameOptions()
        options.add('randomize-seats')
        game, users = create_and_start_game(3, Variant.Ireland, options)

        commands = [
            # Round 1
            'fell-trees at 30e to choose joker; pass',
            'fell-trees at 30e to choose wood; pass',
            'cut-peat at 31c to choose peat; pass',
            'build g02 at 31f and place prior to spend 1 coin 1 clay 1 peat to gain 6 livestock; pass',

            # Round 2
            'place lay-brother to use h03 to choose coin; buy plot as side1 at 30; pass',
            'place lay-brother to use h02 to choose grain; pass',
            'place lay-brother to use h02 to choose livestock; pass',
            'build i08 at 31b and place prior to gain 1 beer; pass',

            # Round 3
            'place lay-brother to use h01 to choose clay; pass',
            'place lay-brother to use h01 to choose joker; pass',
            'fell-trees at 30d to choose wood; pass',
            'build i04 at 31c and place prior to spend 4 grain; pass',

            # Round 4
            'place lay-brother to use h02 to choose grain; pass',
            'cut-peat at 30c to choose peat; pass',
            'fell-trees at 30d to choose joker; pass',
            'convert 1 grain to 1 straw; build i09 at 30e and place prior; pass',

            # Round 5
            'pay 1 coin to red to use g02 to spend 1 grain 1 wood 1 coin to gain 6 grain; pass',
            'place lay-brother to use h02 to choose livestock; pass',
            # Interaction requiring the other player to choose which clergyman to use
            'pay 1 coin to blue to use i04',
            'place lay-brother',
            'use i04 to spend 3 grain; pass',
            'fell-trees at 31d to choose wood; pass',

            # Round 6 -- Settlement
            'buy district as side2 at 32; build s01 at 32e with 1 wood 1 livestock; pass',
            'buy plot as side2 at 30; build s03 at 30f with 4 livestock; pass',
            'build s01 at 30f with 1 wood 1 coin; pass',
            # Round 6 -- Action
            'build g19 at 30f and place prior to spend 4 livestock 4 straw; pass',
            'build g16 at 31h and place prior; pass',
            'place lay-brother to use h01 to choose clay; pass',
            'fell-trees at 32c to choose joker; pass',

            # Round 7
            'place lay-brother to use h03 to choose coin; pass',
            'pay 1 coin to blue to use i04',
            'place lay-brother',
            'use i04 to spend 5 grain; pass',
            'build g12 at 31f and place prior to spend 2 meat 2 peat 1 wood; pass',
            'place lay-brother to use h02 to choose grain; pass',

            # Round 8
            'cut-peat at 31c to choose peat; pass',
            'build i14 at 32d; pass',
            'pay 1 coin to blue to use i14 to gain 2 malt gain 1 whiskey; pass',
            'build g07 at 30d and place prior to spend 5 peat; pass',

            # Round 9
            'fell-trees at 31d to choose wood; pass',
            'pay 1 coin to blue to use i04',
            'place lay-brother',
            'use i04 to spend 4 grain; pass',
            'place lay-brother to use h02 to choose livestock; pass',
            'place prior to use h02 to choose joker to gain 4 grain; pass',

            # Round 10
            'buy district as side1 at 32; build i17 at 32g and place prior to spend 1 coin; pass',
            'place lay-brother to use i08 to gain 1 beer; pass',
            'place lay-brother to use h01 to choose clay; pass',
            'place lay-brother to use g16; pass',

            # Round 11 -- Settlement
            'build s04 at 30b with 1 peat-coal 1 beer 1 livestock 1 coin; pass',
            'build s05 at 31d with 1 wood 1 meat; pass',
            'build s05 at 32f with 1 wood 1 meat; pass',
            # Round 11
            'build i21 at 30e and place prior to spend 5 malt 5 wood 5 peat; pass',
            'convert 1 grain to 1 straw; build i05 at 32f and place prior to spend 3 grain 3 malt and spend 1 beer; pass',
            'place lay-brother to use h02 to choose grain; pass',
            'place lay-brother to use h03 to choose coin; buy district as side1 at 29; pass',

            # Round 12
            'cut-peat at 30c to choose peat; pass',
            'fell-trees at 32e to choose wood; pass',
            'pay 1 whiskey to blue to use g12 to spend 5 livestock 2 peat-coal; pass',
            'place lay-brother to use i14 to gain 2 grain gain 1 whiskey; pass',

            # Round 13
            'pay 1 whiskey to blue to use i05',
            'place lay-brother',
            'use i05 to spend 7 grain 7 malt and spend 1 beer; pass',
            'place lay-brother to use h02 to choose joker to gain 5 livestock; pass',
            'buy plot as side1 at 31; build i20 at 32b and place prior to spend 1 beer and spend 1 whiskey; pass',
            'buy district as side2 at 33; build g01 at 33g and place prior to use i21 to spend 2 malt 2 wood 2 peat; pass',

            # Round 14
            'place lay-brother to use h01 to choose clay; pass',
            'pay 2 coin to green to use g07',
            'place lay-brother',
            'use g07 to spend 6 peat; pass',
            'place lay-brother to use h02 to choose livestock; pass',
            'build i24 at 31f and place prior to spend 1 coin and spend 1 beer 1 whiskey; pass',

            # Round 15 -- Settlement
            'build s06 at 32c with 2 peat-coal 1 meat; pass',
            'buy plot as side2 at 32; build s01 at 32h with 1 wood 1 livestock; pass',
            'buy district as side1 at 32; build s06 at 32f with 2 peat-coal 2 livestock 1 grain; pass',
            # Round 15
            'fell-trees at 30e to choose wood; pass',
            'place lay-brother to use i09; pass',
            'build i29 at 29f and place prior to remove forest at 32e; pass',
            'place lay-brother to use h03 to choose coin; pass',

            # Round 16
            'build g22 at 30i and place prior to choose joker; pass',
            'cut-peat at 32c to choose peat; pass',
            'build g26 at 31b and place prior to spend 2 wood; pass',
            'place lay-brother to use h02 to choose grain; pass',

            # Round 17
            'pay 1 whiskey to red to use g01 to use g22 to choose stone; pass',
            'buy district as side2 at 33; place lay-brother to use h01 to choose clay; pass',
            'convert 3 grain to 3 straw; pay 1 whiskey to blue to use g19 to spend 8 straw 8 livestock; pass',
            'fell-trees at 32d to choose wood; pass',

            # Round 18
            'convert 1 grain to 1 straw; build i33 at 30d and place prior to spend 3 wood to choose joker to gain 3 beer; pass',
            'pay 1 whiskey to green to use i24 to spend 1 coin and spend 3 whiskey 3 beer; pass',
            'pay 1 whiskey to red to use g02',
            'place lay-brother',
            'use g02 to spend 1 stone 1 clay 1 peat to gain 6 wood; pass',
            'place lay-brother to use g26 to spend 2 wood; pass',

            # Round 19
            'cut-peat at 32c to choose peat; pass',
            'place lay-brother to use g07 to spend 3 peat; pass',
            'place lay-brother to use h02 to choose livestock; pass',
            'place lay-brother to use h03 to choose coin; pass',

            # Round 20 -- Settlement
            'build s05 at 29g with 1 wood 3 livestock; pass',
            'build s07 at 33f with 3 peat-coal 3 beer; pass',
            'build s06 at 33f with 1 meat 3 peat; pass',
            # Round 20
            'build g18 at 32g and place prior to spend 1 clay 1 peat-coal and spend 1 stone; pass',
            'place lay-brother to use i14 to gain 2 grain gain 1 whiskey; pass',
            'build i35 at 33h and place prior to spend 5 coin 1 whiskey 1 reliquary 3 book; pass',
            'pay 1 whiskey to blue to use i20',
            'place lay-brother',
            'use i20 to spend 1 whiskey; buy plot as side2 at 31; pass',

            # Round 21
            'fell-trees at 33c to choose wood; pass',
            'fell-trees at 32d to choose joker; pass',
            'build g34 at 32h; pass',
            'convert 1 grain to 1 straw; build i40 at 33e and place prior to use g28 to build s02 at 32g with 1 peat-coal 1 malt 1 livestock; pass',

            # Round 22
            'place lay-brother to use i09; pass',
            'pay 1 whiskey to red to use g22',
            'place lay-brother',
            'use g22 to choose stone; pass',
            'place lay-brother to use i40 to use i30; pass',
            'pay 2 coin to green to use i29 to remove forest at 31d; pass',

            # Round 23
            'build g28 at 31i; pass',
            'pay 2 coin to green to use g28 to build s03 at 33d with 1 livestock 1 meat; pass',
            'build g41 at 30h and place prior to spend 5 coin to gain 1 book 2 ceramic 1 ornament; pass',
            'build i11 at 30a; pass',

            # Round 24
            'buy plot as side2 at 31; build i30 at 31h and place prior to spend 1 meat; pass',
            'place lay-brother to use h03 to choose coin; buy district as side1 at 34; pass',
            'convert 2 whiskey to 4 coin; build i38 at 32e; pass',
            'build i27 at 33c; pass',

            # Round 25
            'place prior to use g28 to build s02 at 34g with 1 meat 3 wood; pass',
            'place prior to use g34 to spend 1 book 1 ceramic 1 ornament 1 reliquary; pass',
            'place prior to use g26 to spend 2 wood; pass',

            # Round 20 -- Settlement
            'build s08 at 34f with 6 meat 1 peat 1 wood; pass',
            'build s03 at 31h with 2 livestock 1 whiskey 1 coin; pass',
            'build s08 at 33g with 3 beer 4 livestock 2 grain 3 coin 1 whiskey 1 peat-coal; pass',
        ]
        for command in commands:
            try:
                print("Age: {0}, Round: {1}, Phase: {2}, Turn: {3}, ActionSeat: {4}".format(
                    game.age, game.round, game.phase, game.turn, game.action_seat_index
                ))
                print(game.action_seat.pk, game.action_seat.player.username, command)
                for seat in game.seats:
                    print(seat.pk, seat.player.username, {g for g in seat.goods.values() if g.count}, seat.clergy_pool)
                game.add_command(command, executor=game.action_seat)
                game.build_gamestate()
            except:
                raise

        print("Age: {0}, Round: {1}, Phase: {2}, Turn: {3}, ActionSeat: {4}".format(
            game.age, game.round, game.phase, game.turn, game.action_seat_index
        ))
        for seat in game.seats:
            print(seat.pk, seat.player.username, {g for g in seat.goods.values() if g.count}, seat.clergy_pool)
        active_seat = game.action_seat
        if active_seat:
            print(active_seat.pk, game.phase, game.round, game.turn)

        for item in game.ledger:
            print(' '.join(filter(None, [(item.executor.player.username if item.executor else ''), item.text])))

        print(game.gameboard.items())

        for seat in game.seats:
            print(seat.pk, seat.player.username, seat.score)
