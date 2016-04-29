from __future__ import unicode_literals
import hashlib
import random

from django.contrib.auth.models import User
from django.db import models, transaction

from .commands import Command
from .cards import buildings, settlements
from .enums import (Age, Phase, Variant, Gameboard, ProductionWheel, ResourceToken, BuildingPlayerCount, LandscapeType,
                    CardType, PlotSide)
from .exceptions import UnappliedCommandsError, OeLException, OeLSyntaxError, OeLValueError, InvalidActor
from .landscapes import Heartland, District, Plot
from .objects import ModX, GameOptions, GameLedger, LedgerEntry, GameBoard, Prior, LayBrother
from .goods import *


def seed_generator():
    sha1 = hashlib.sha1()
    # Multiple calls to random() for generating a seed is probably overkill, but... y'know...
    hash_key = '{0}:{1}'.format(random.random(), random.random()).encode('utf-8')
    sha1.update(hash_key)
    return sha1.hexdigest()


class GameManager(models.Manager):
    def create_game(self, number_of_players, variant, options, **kwargs):
        if 4 < number_of_players < 1:
            raise ValueError("number_of_players must be between 1 and 4")
        game = self.create(**kwargs)

        commands = ['# Game initialization', 'setup variant {0}'.format(variant)]

        seats = []
        for i in range(number_of_players):
            seat = Seat.objects.create(game=game)
            seats.append(seat)
        if number_of_players == 1:
            seat = Seat.objects.create(game=game, is_neutral=True)
            seats.append(seat)

            commands.append('option one-player')

        for option in ('short-game', 'long-game', 'remove-c-quarry', 'loamy-landscape', 'randomize-seats'):
            if option in options:
                commands.append('option {0}'.format(option))

        game.add_commands(commands)
        game.build_gamestate()
        return game


class Game(models.Model):
    owner = models.ForeignKey(User)
    seed = models.CharField(max_length=50, default=seed_generator, blank=False, null=False, editable=False)
    name = models.CharField(max_length=256, default='New Game', blank=False, null=False)

    objects = GameManager()

    def __init__(self, *args, **kwargs):
        super(Game, self).__init__(*args, **kwargs)
        # These are the "Default values".  The actual game values get built/resolved using the build_gamestate() method.
        self.variant = Variant.All
        self.options = GameOptions()
        self.gameboard = GameBoard(Gameboard.FourPlayer, ProductionWheel.Standard)
        self._seats = []
        self.age = Age.Start
        self._phase = Phase.Setup
        self.round = None
        self.turn = None
        self.available_buildings = []
        self.available_landscapes = {
            LandscapeType.District: [District(1, 2), District(2, 3), District(3, 4), District(4, 4), District(5, 5),
                                     District(6, 5), District(7, 6), District(8, 7), District(9, 8)],
            LandscapeType.Plot: [Plot(1, 3), Plot(2, 4), Plot(3, 4), Plot(4, 5), Plot(5, 5), Plot(6, 5), Plot(7, 6),
                                 Plot(8, 6), Plot(9, 7)]
        }
        self.work_contract_price = Coin(1)
        self._gamelogs = []
        self._last_applied_gamelog = 0
        self._message = ''
        self.ledger = GameLedger()
        try:
            self.build_gamestate()
        except (OeLException, OeLSyntaxError, OeLValueError) as error:
            print(error)
            self.phase = Phase.Broken
            self._message = '{}: {}'.format(type(error), error)

    @property
    def message(self):
        return self._message

    @property
    def last_applied_gamelog(self):
        return self._last_applied_gamelog

    @property
    def phase(self):
        return self._phase

    @phase.setter
    def phase(self, new_phase):
        if new_phase == Phase.BonusRound:
            for index in range(len(self.seats)):
                if not any(c for c in self.seats[index].clergy_pool if c.name == 'prior'):
                    self.seats[index].return_clergy('prior')
                    self.ledger.append(LedgerEntry('return prior', index))

        self._phase = new_phase

        if new_phase == Phase.RoundStart:
            self.round += 1
            self.phase = Phase.ReturnClergy

        if new_phase == Phase.ReturnClergy:
            # ReturnClergy is a fairly simple step.  Everything is automatic and shouldn't need any player interaction
            self.ledger.append(LedgerEntry('starting round {0}'.format(self.round)))
            for seat_index in range(len(self.seats)):
                if not self.seats[seat_index].clergy_pool:
                    self.seats[seat_index].return_clergy()
                    self.ledger.append(LedgerEntry('return all clergy', seat_index))
            self.phase = Phase.RotateProductionWheel

        elif new_phase == Phase.RotateProductionWheel:
            # RotateProductionWheel is an automatic phase and shouldn't need any player interactions
            self.gameboard[ResourceToken.Wheel] += 1
            self.ledger.append(LedgerEntry('rotate production wheel'))
            for resource_tile in (ResourceToken.Wood, ResourceToken.Peat, ResourceToken.Grain, ResourceToken.Livestock,
                                  ResourceToken.Clay, ResourceToken.Coin, ResourceToken.Joker, ResourceToken.Grapes,
                                  ResourceToken.Stone):
                if resource_tile in self.gameboard and \
                        self.gameboard[resource_tile] == self.gameboard[ResourceToken.Wheel]:
                    if self.number_of_players == 1:
                        del self.gameboard[resource_tile]
                        self.ledger.append(LedgerEntry('remove {0} from game board'.format(resource_tile)))
                    else:
                        self.gameboard[resource_tile] += 1
                        self.ledger.append(LedgerEntry('shift {0} ahead of production wheel'.format(resource_tile)))
            if self.round == self.round_grapes_enter:
                self.gameboard.add_token(ResourceToken.Grapes, self.gameboard[ResourceToken.Wheel])
                self.ledger.append(LedgerEntry('add grapes to game board'))
            if self.round == self.round_stone_enters:
                self.gameboard.add_token(ResourceToken.Stone, self.gameboard[ResourceToken.Wheel])
                self.ledger.append(LedgerEntry('add stone to game board'))

            if self.gameboard[ResourceToken.House] == self.gameboard[ResourceToken.Wheel]:
                # Advance the Age
                if self.age == Age.Start:
                    self.age = Age.A
                    self.phase = Phase.Settlement
                elif self.age == Age.A:
                    self.age = Age.B
                    self.phase = Phase.Settlement
                elif self.age == Age.B:
                    self.age = Age.C
                    self.phase = Phase.Settlement
                elif self.age == Age.C:
                    self.age = Age.D
                    self.phase = Phase.Settlement
                elif self.age == Age.D:
                    self.age = Age.E
                    if self.number_of_players in (3, 4):
                        self.phase = Phase.BonusRound
            elif False:  # TODO -- logic for end-of-game needed
                pass
            else:
                self.phase = Phase.Action

        elif new_phase == Phase.Settlement:
            self.turn = 1
            diff = 0
            if 'short-game' in self.options and self.number_of_players in (3, 4):
                if self.age == Age.A:
                    diff = 2
                elif self.age == Age.B:
                    diff = 2
                elif self.age == Age.C:
                    diff = 2
                elif self.age == Age.D:
                    diff = 4
            elif self.number_of_players == 3:
                if self.age == Age.A:
                    diff = 5
                elif self.age == Age.B:
                    diff = 4
                elif self.age == Age.C:
                    diff = 5
                elif self.age == Age.D:
                    diff = 5
            elif self.number_of_players == 4:
                if self.age == Age.A:
                    diff = 3
                elif self.age == Age.B:
                    diff = 6
                elif self.age == Age.C:
                    diff = 3
                elif self.age == Age.D:
                    diff = 6
            elif self.number_of_players == 2:
                if self.age == Age.A:
                    diff = 7
                elif self.age == Age.B:
                    diff = 7
                elif self.age == Age.C:
                    diff = 7
            elif self.number_of_players == 1:
                if self.age == Age.A:
                    diff = 4
                elif self.age == Age.B:
                    diff = 6
                elif self.age == Age.C:
                    diff = 4
                elif self.age == Age.D:
                    diff = 6

            if diff:
                self.ledger.append(LedgerEntry('move building marker to round {0}'.format(self.round + diff)))
                self.gameboard[ResourceToken.House] += diff

        elif new_phase == Phase.Action:
            self.turn = 1

        elif new_phase == Phase.PassStartPlayer:
            if self.number_of_players in (2, 3, 4):
                self._round_start_seat_index += 1
            self.phase = Phase.RoundStart

        elif new_phase == Phase.BonusRound:
            self.turn = 1

        elif new_phase == Phase.Endgame:
            self.turn = None

    @property
    def round(self):
        return self._round

    @round.setter
    def round(self, value):
        self._round = value
        if value is not None:
            self._round_start_seat_index = (value - 1) % self.number_of_players
        else:
            self._round_start_seat_index = None

    @property
    def turn(self):
        return self._turn

    @turn.setter
    def turn(self, value):
        self._turn = value
        if value is None:
            self.action_seat_index = None
        else:
            self.action_seat_index = (self._round_start_seat_index + value - 1) % self.number_of_players

    @property
    def action_seat_index(self):
        return self._action_seat_index

    @action_seat_index.setter
    def action_seat_index(self, value):
        self._action_seat_index = value
        #if value is not None:
        #    self._action_seat_index = ModX(value, self.number_of_players)
        #else:
        #    self._action_seat_index = None

    def pass_turn(self, seat):
        seat.actions_taken = 0
        seat.landscape_purchased_this_turn = False
        self.turn += 1
        if self.phase == Phase.Action:
            # In a standard game, each normal Action round consists of N + 1 turns.  The start player gets 2 turns
            if self.number_of_players in {3, 4}:
                if self.turn - 1 > self.number_of_players:
                    self.phase = Phase.PassStartPlayer
            elif self.number_of_players == 2:
                if 'long-game' in self.options:
                    if self.action_seat_index == self._round_start_seat_index:
                        self.phase = Phase.PassStartPlayer
                else:
                    self.phase = Phase.PassStartPlayer
            elif self.number_of_players == 1:
                pass
        elif self.phase == Phase.Settlement:
            # In these phases, a round consists of N turns.
            if self.turn > self.number_of_players:
                if self.age == Age.E:
                    self.phase = Phase.Endgame
                else:
                    self.add_new_age_buildings()
                    self.phase = Phase.Action
        elif self.phase == Phase.BonusRound:
            # In this phase, a round consists of N turns.
            if self.turn > self.number_of_players:
                self.phase = Phase.Settlement
        elif self.phase == Phase.FinalAction:
            # In this phase, a round consists of N turns.
            if self.turn > self.number_of_players:
                self.phase = Phase.Endgame

    @property
    def round_start_seat(self):
        if self._round_start_seat_index is None:
            return None
        return self.seats[self._round_start_seat_index]

    @property
    def action_seat(self):
        if self.action_seat_index is None:
            return None
        return self.seats[self.action_seat_index]

    @property
    def seats(self):
        if not self._seats:
            self._seats = list(self.seat_set.all())
        self._seats = sorted(self._seats, key=lambda s: (s.seat_order, s.id))
        return self._seats

    def seat_by_color(self, color):
        colors = ['red', 'green', 'blue', 'white']
        if color not in colors:
            return None
        index = colors.index(color)
        if index >= self.number_of_seats:
            return None
        return self.seats[index]

    @property
    def players(self):
        return [s for s in self.seats if not s.is_neutral]

    @property
    def number_of_seats(self):
        return len(self.seats)

    @property
    def number_of_players(self):
        return len(self.players)

    @property
    def can_start(self):
        return self.phase == Phase.Setup and not [s for s in self.players if not s.player]

    def start(self):
        if self.phase in (Phase.Settlement, Phase.BonusRound, Phase.FinalAction, Phase.Action, Phase.Endgame,
                          Phase.PassStartPlayer, Phase.ReturnClergy, Phase.RotateProductionWheel):
            raise Exception("Game is already running")
        if not self.can_start:
            raise Exception("Cannot start this game yet")
        self.add_commands(('setup finalize', 'setup start', '# Game actions'))
        self.build_gamestate()

    def can_join(self, player):
        return self.phase == Phase.Setup and \
               not [s for s in self.players if s.player == player] and \
               [s for s in self.players if not s.player]

    def join(self, player):
        if self.phase != Phase.Setup or [s for s in self.players if s.player == player]:
            raise Exception("{0} cannot join this game".format(player))
        open_seat = self.seat_set.players().select_for_update().filter(player__isnull=True).first()
        if not open_seat:
            raise Exception("{0} cannot join this game".format(player))
        open_seat.player = player
        open_seat.save()
        self._seats = []
        return open_seat

    @property
    def round_grapes_enter(self):
        if self.variant == Variant.France:
            if self.number_of_players == 2:
                return 11
            elif self.number_of_players in (3, 4):
                if 'short-game' in self.options:
                    return 4
                return 8
        return None

    @property
    def round_stone_enters(self):
        if self.number_of_players == 2:
            return 18
        elif self.number_of_players in (3, 4):
            if 'short-game' in self.options:
                return 6
            return 13
        return None

    def production_value(self, resource_token):
        return self.gameboard.production_value(self.number_of_players, 'long-game' in self.options, resource_token)

    def produce(self, resource_token):
        return self.gameboard.produce(self.number_of_players, 'long-game' in self.options, resource_token)

    def add_new_age_buildings(self):
        self.ledger.append(LedgerEntry('distribute age {0} buildings and settlements'.format(self.age)))
        player_count = BuildingPlayerCount.map(self.number_of_players, 'short-game' in self.options, 'long-game' in self.options)
        for building_class in buildings:
            building = building_class()
            if building.age != self.age:
                continue
            if building.variant not in (self.variant, Variant.All):
                continue
            if 'short-game' in self.options and \
                    self.variant == Variant.France and \
                    'remove-c-quarry' in self.options and \
                    building.id == 'f29':
                continue
            else:
                if player_count not in building.player_counts:
                    continue
            if building.id == 'fl1' and (self.variant != Variant.France or 'loamy-landscape' not in self.options):
                continue
            self.available_buildings.append(building)

        for settlement_class in settlements:
            for seat in self.seats:
                settlement = settlement_class(owner=seat)
                if settlement.age != self.age:
                    continue
                seat.settlements.add(settlement)

    def building_built(self, seat, building):
        if building.id in ('f21', 'i21'):
            self.work_contract_price = Coin(2)

    @property
    def gamelogs(self):
        if not self._gamelogs:
            self._gamelogs = list(self.gamelog_set.all())
        return self._gamelogs

    def add_command(self, command, executor=None):
        return self.add_commands([command], executor=executor)[-1]

    def add_commands(self, commands, executor=None):
        """
        Add a command to the game.  This method ensures that the command only gets added if the gamestate is what the
        game thinks it is.  This means that if another instance of this game adds a GameLog entry under its nose,
        this method will fail
        :param commands: iterable sequence of command strings to execute
        :param executor: optional executor that is executing the commands
        :return: GameLog instance created
        """
        new_commands = []
        # Make this process atomic so that things don't get janky
        with transaction.atomic():
            db_latest_gamelog = self.gamelog_set.all().last()
            if db_latest_gamelog and db_latest_gamelog.id > self._last_applied_gamelog:
                raise UnappliedCommandsError("There are new unapplied commands")

            actor_id = executor.id if executor else None
            for command in commands:
                new_commands.append(GameLog.objects.create(game=self, command=command, executor_id=actor_id))

            self.gamelogs.extend(new_commands)

        return new_commands

    def build_gamestate(self):
        """
        This method applies all of the game's commands to arrive at the current gamestate.
        :return:
        """
        previous_command = None
        for game_command in self.gamelogs:
            if game_command.id > self._last_applied_gamelog:
                game_command.apply(previous_command)
                self._last_applied_gamelog = game_command.id

            if game_command.parsed_commands:
                previous_command = game_command.parsed_commands[-1]

    def __str__(self):
        return 'Game[{}p/{}] {}'.format(self.number_of_players, self.variant[0], self.name if len(self.name) <= 20 else self.name[:17] + '...')


class SeatQuerySet(models.QuerySet):
    def players(self):
        return self.filter(is_neutral=False)

    def neutrals(self):
        return self.filter(is_neutral=True)


class SeatManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        return SeatQuerySet(self.model)

    def players(self):
        return self.get_queryset().players()

    def neutrals(self):
        return self.get_queryset().neutrals()


class Seat(models.Model):
    class Meta:
        ordering = ['id']

    game = models.ForeignKey(Game)
    player = models.ForeignKey(User, blank=True, null=True)
    is_neutral = models.BooleanField(default=False, null=False)

    objects = SeatManager()

    __original_data = {}

    def __init__(self, *args, **kwargs):
        super(Seat, self).__init__(*args, **kwargs)
        self.__original_data['game_id'] = self.game_id
        self.__original_data['player_id'] = self.player_id
        self.__original_data['is_neutral'] = self.is_neutral
        self.seat_order = None

        # These are the "Default values".  The actual seat values get built/resolved using the Game's build_gamestate()
        # method.
        self._goods = {
            'wood': Wood(),
            'peat': Peat(),
            'grain': Grain(),
            'livestock': Livestock(),
            'clay': Clay(),
            'coin': Coin(),
            'stone': Stone(),
            'peat-coal': PeatCoal(),
            'straw': Straw(),
            'meat': Meat(),
            'ceramic': Ceramic(),
            'book': Book(),
            'reliquary': Reliquary(),
            'ornament': Ornament(),
            'wonder': Wonder(),
            'energy': Energy(),
            'food': Food(),
            'points': Points(),
            'money': Money()
        }
        self.heartland = Heartland()
        self.clergy_pool = [Prior(self), LayBrother(self), LayBrother(self)]
        self.landscapes = []
        self.settlements = set()
        self.actions_taken = 0
        self.landscape_purchased_this_turn = False

    @property
    def is_instance_changed(self):
        return any([getattr(self, kv[0]) != kv[1] for kv in self.__original_data.items()])

    @property
    def goods(self):
        return self._goods

    def spend(self, goods):
        for good in goods:
            self.goods[good.name] -= good

    def gain(self, goods):
        for good in goods:
            self.goods[good.name] += good

    def save(self, force_insert=False, force_update=False, **kwargs):
        if ((not self.pk and not force_insert) or (self.pk and not force_update)) and not self.is_instance_changed:
            return

        super(Seat, self).save(force_insert, force_update, **kwargs)

        for key in self.__original_data:
            self.__original_data[key] = getattr(self, key)

    def max_available_goods(self, good_type=None):
        goods = self.goods.copy()
        goods['straw'] += self.goods['grain']
        goods_items = goods.values()
        for gt in goods:
            if gt == 'energy':
                goods[gt] += sum([g.total_energy_value for g in goods_items if g.name != gt])
            elif gt == 'food':
                goods[gt] += sum([g.total_food_value for g in goods_items if g.name != gt])
            elif gt == 'money':
                goods[gt] += sum([g.total_money_value for g in goods_items if g.name != gt])
            elif gt == 'points':
                goods[gt] += sum([g.total_points_value for g in goods_items if g.name != gt])

        if good_type:
            good = goods[good_type]
            goods.clear()
            goods[good_type] = good
        return goods

    def available_landscape_coordinates(self, landscape=None, landscape_type=None):
        """
        Generates a set of coordinate tuples containing all available coordinates for the optional landscape or
        landscape_type provided.  If only landscape_type is provided, all available coordinates for that type will be
        returned.  If no parameters are provided, this method will return *all* available coordinates for landscapes,
        regardless of type.
        :param landscape: Landscape to check -- optional
        :param landscape_type: LandscapeType to check -- optional
        :return: a set of (row, column) coordinates
        """
        # Always override landscape_type if landscape is provided
        if landscape:
            landscape_type = landscape.landscape_type

        available_coordinates = set()
        districts = [l for l in self.landscapes if l.landscape_type == LandscapeType.District]
        plots = [l for l in self.landscapes if l.landscape_type == LandscapeType.Plot]

        if not landscape_type or landscape_type == LandscapeType.District:
            column = 2
            # Add in all of the theoretical spaces, regardless if there's another board there or not
            available_coordinates.update({(self.heartland.row - 1, column), (self.heartland.row + 2, column)})
            for d in districts:
                available_coordinates.update({(d.row - 1, column), (d.row + 1, column)})
            # After re-reading the rules, it looks like Districts must always abut either the Heartland or another
            # District.  That means that the following code shouldn't be used.
            # for p in plots:
            #     available_coordinates.update({(p.row, column), (p.row + 1, column)})

            # Now remove any rows where there's already a Heartland or a District
            available_coordinates.difference_update({(self.heartland.row, column), (self.heartland.row + 1, column)})
            for d in districts:
                available_coordinates.discard(d.row)

        if not landscape_type or landscape_type == LandscapeType.Plot:
            if landscape:
                columns = (landscape.column, )
            else:
                columns = (0, 7)
            # Add in all of the theoretical spaces, regardless if there's another board there or not
            for column in columns:
                available_coordinates.update({
                    (self.heartland.row - 1, column), (self.heartland.row, column), (self.heartland.row + 1, column)
                })
                for d in districts:
                    available_coordinates.update({(d.row - 1, column), (d.row, column)})
                for p in plots:
                    available_coordinates.update({(p.row - 2, column), (p.row + 2, column)})

                # Now remove any (rows, columns) where there's already a Plot
                for p in plots:
                    available_coordinates.difference_update({
                        (p.row - 1, p.column), (p.row, p.column), (p.row + 1, p.column)
                    })

        return available_coordinates

    @staticmethod
    def _clean_coordinate(coordinate):
        fixed_coordinate = list(coordinate)
        if isinstance(coordinate[0], str):
            fixed_coordinate[0] = int(coordinate[0])
        if isinstance(coordinate[1], str):
            fixed_coordinate[1] = ord(coordinate[1]) - 97
        return fixed_coordinate

    def find_space(self, coordinate):
        fixed_coordinate = self._clean_coordinate(coordinate)

        if fixed_coordinate[1] in (0, 1, 7, 8):
            targets = [l for l in self.landscapes if l.landscape_type == LandscapeType.Plot]
        else:
            targets = [self.heartland] + [l for l in self.landscapes if l.landscape_type == LandscapeType.District]

        for target in targets:
            if target.row <= fixed_coordinate[0] <= (target.row + target.vertical_size - 1) and \
                    target.column <= fixed_coordinate[1] <= (target.column + target.horizontal_size - 1):
                return target.landscape_spaces[fixed_coordinate[1] - target.column][fixed_coordinate[0] - target.row]

        return None

    def find_spaces_matching(self, matching_function):
        matched_spaces = set()
        for landscape in [self.heartland] + self.landscapes:
            for row in range(landscape.vertical_size):
                for column in range(landscape.horizontal_size):
                    # If this is a Mountain Plot, the last coordinate doesn't exist
                    if landscape[column][row] and matching_function(landscape[column][row]):
                        matched_spaces.add(landscape[column][row])

        return matched_spaces

    def find_spaces_adjacent(self, coordinate):
        fixed_coordinate = self._clean_coordinate(coordinate)

        adjacent_spaces = []

        # If this is a Mountain space, then there are exactly 2 adjacent spaces
        if coordinate[1] == 8:
            space = self.find_space((fixed_coordinate[0], fixed_coordinate[1] - 1))
            if space:
                adjacent_spaces.append(space)
            space = self.find_space((fixed_coordinate[0] + 1, fixed_coordinate[1] - 1))
            if space:
                adjacent_spaces.append(space)

        # Otherwise, we've got some work to do
        else:
            if coordinate[1] == 7:
                adjacent_coordinates = [
                    (fixed_coordinate[0] - 1, fixed_coordinate[1]),
                    (fixed_coordinate[0] + 1, fixed_coordinate[1]),
                    (fixed_coordinate[0], fixed_coordinate[1] - 1)
                ]
                # The right neighbor for these spaces gets tricky, since for the first row on the Plot, the adjacency
                # is +0/+1 while for the second row, the adjacency is -1/+1.  So we need to find out which row our
                # coordinate is in first. Luckily, we can limit the search to just Mountain-sided Plots
                for landscape in self.landscapes:
                    if landscape.landscape_type != LandscapeType.Plot or landscape.landscape_side != PlotSide.Mountain:
                        continue
                    if landscape.row == coordinate[0]:
                        adjacent_coordinates.append((fixed_coordinate[0], fixed_coordinate[1] + 1))
                        break
                    elif landscape.row + 1 == coordinate[0]:
                        adjacent_coordinates.append((fixed_coordinate[0] - 1, fixed_coordinate[1] + 1))
                        break
            # All spaces other than the ones adjacent to Mountain are straightforward
            else:
                adjacent_coordinates = [
                    (fixed_coordinate[0] - 1, fixed_coordinate[1]),
                    (fixed_coordinate[0] + 1, fixed_coordinate[1]),
                    (fixed_coordinate[0], fixed_coordinate[1] - 1),
                    (fixed_coordinate[0], fixed_coordinate[1] + 1)
                ]

            for target in [self.heartland] + self.landscapes:
                for adjacent_coordinate in adjacent_coordinates:
                    if target.row <= adjacent_coordinate[0] <= (target.row + target.vertical_size - 1) and \
                            target.column <= adjacent_coordinate[1] <= (target.column + target.horizontal_size - 1):
                        col = adjacent_coordinate[1] - target.column
                        row = adjacent_coordinate[0] - target.row
                        if target.landscape_spaces[col][row]:
                            adjacent_spaces.append(target.landscape_spaces[col][row])

        return adjacent_spaces

    def return_clergy(self, clergy_names=None):
        if clergy_names and isinstance(clergy_names, str):
            clergy_names = {clergy_names}

        def _match_func(_space):
            if _space.card and _space.card.card_type == CardType.Building and _space.card.assigned_clergy:
                return True
            return False

        for space in self.find_spaces_matching(_match_func):
            for clergy in space.card.assigned_clergy[:]:
                if not clergy_names or clergy.name in clergy_names:
                    clergy.owner.clergy_pool.append(space.card.remove_clergy(clergy))

    def build_building(self, space, building):
        # Remove the building from the building pool
        self.game.available_buildings.remove(building)
        # Pay for the costs
        self.spend(building.cost)
        # Set the building's owner
        building.owner = self
        # Add it to the designated space
        space.add_card(building, force_overplay=True)
        self.game.building_built(self, building)

    def build_settlement(self, space, settlement, goods):
        # Pay goods for the settlement
        self.spend(goods)

        # Remove the settlement from the seat's pool
        self.settlements.discard(settlement)
        # Place the settlement into the space
        space.add_card(settlement)

    @property
    def score(self):
        _score = {
            'settlements': 0,
            'economic': 0,
            'goods': 0
        }
        for landscape in [self.heartland] + self.landscapes:
            for row in range(landscape.vertical_size):
                for column in range(landscape.horizontal_size):
                    if not landscape[column][row] or not landscape[column][row].card:
                        continue
                    if landscape[column][row].card.card_type == CardType.Settlement:
                        _score['economic'] += landscape[column][row].card.economic_value
                        _score[landscape[column][row].card.id] = landscape[column][row].card.dwelling_value
                        for adj_space in self.find_spaces_adjacent((landscape.row + row, landscape.column + column)):
                            if adj_space.card and adj_space.card.card_type in (CardType.Building, CardType.Settlement):
                                _score[landscape[column][row].card.id] += adj_space.card.dwelling_value

                        _score['settlements'] += _score[landscape[column][row].card.id]

                    elif landscape[column][row].card.card_type == CardType.Building:
                        _score['economic'] += landscape[column][row].card.economic_value

        for good in self.goods.values():
            _score['goods'] += int(good.total_points_value)

        _score['total'] = _score['settlements'] + _score['economic'] + _score['goods']

        return _score

    @property
    def landscape_grid(self):
        grid = {
            'start': self.heartland.row,
            'end': self.heartland.row + self.heartland.vertical_size,
            'column_0': [],
            'column_1': [self.heartland],
            'column_2': []
        }
        for landscape in self.landscapes:
            if landscape.landscape_type == LandscapeType.District:
                grid['column_1'].append(landscape)
            elif landscape.landscape_type == LandscapeType.Plot:
                if landscape.landscape_side == PlotSide.Coastal:
                    grid['column_0'].append(landscape)
                elif landscape.landscape_side == PlotSide.Mountain:
                    grid['column_2'].append(landscape)
        grid['column_0'] = sorted(grid['column_0'], key=lambda l: l.row)
        grid['column_1'] = sorted(grid['column_1'], key=lambda l: l.row)
        grid['column_2'] = sorted(grid['column_2'], key=lambda l: l.row)
        grid['start'] = grid['column_1'][0].row
        grid['end'] = grid['column_1'][-1].row + grid['column_1'][-1].vertical_size
        if grid['column_0']:
            if grid['column_0'][0].row < grid['start']:
                grid['start'] = grid['column_0'][0].row
            if grid['column_0'][-1].row + grid['column_0'][-1].vertical_size > grid['end']:
                grid['end'] = grid['column_0'][-1].row + grid['column_0'][-1].vertical_size
        if grid['column_2']:
            if grid['column_2'][0].row < grid['start']:
                grid['start'] = grid['column_2'][0].row
            if grid['column_2'][-1].row + grid['column_2'][-1].vertical_size > grid['end']:
                grid['end'] = grid['column_2'][-1].row + grid['column_2'][-1].vertical_size

        return grid

    def __str__(self):
        return 'Seat[{}/{}] {}'.format(self.pk, self.player, {g for g in self.goods.values() if g.count})


class GameLog(models.Model):
    class Meta:
        ordering = ['id']

    game = models.ForeignKey(Game)
    executor_id = models.PositiveIntegerField(blank=True, null=True)
    command = models.CharField(max_length=512, blank=True, null=False)

    def __init__(self, *args, **kwargs):
        super(GameLog, self).__init__(*args, **kwargs)
        self._parsed_commands = []

    @property
    def parsed_commands(self):
        return self._parsed_commands

    def apply(self, previous_command=None):
        for command_text in self.command.split(';'):
            if self.executor_id is None and self.game.action_seat is not None:
                raise InvalidActor('It\'s not your turn')
            if self.executor_id is not None and self.game.action_seat and self.executor_id != self.game.action_seat.id:
                raise InvalidActor('It is {}s turn'.format(self.game.action_seat_index))
            command = Command.command_factory(self.game, self.executor_id, command_text.strip().lower())
            command.apply(previous_command=previous_command)
            self.parsed_commands.append(command)
            previous_command = command

        return previous_command

    def __unicode__(self):
        if self.executor_id:
            return '({}) {}'.format(self.executor_id, self.command)
        return self.command
