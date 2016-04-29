__author__ = 'Jurek'
from abc import ABCMeta, abstractmethod, abstractproperty
import random
import re

from .enums import Age, Phase, Variant, Gameboard, ProductionWheel, ResourceToken, LandscapeType, DistrictSide, \
    PlotSide, CardType
from .exceptions import UnknownOpCode, InvalidOpCode, InvalidArguments, NotEnoughGoods, NoLandscapeAvailable, \
    LandscapeAlreadyPurchased, BuildingNotFound, BuildingPresent, SpaceNotFound, InvalidLandscapePlot, \
    ClergyNotAvailable, ActionRequired, InvalidToken, InvalidGoodsConversion, PaymentRequired, PaymentNotNeeded, \
    InvalidPayment, OeLException, OeLSyntaxError, OeLValueError
from .cards import BuildersMarket
from .cards.function import BuildBuilding as fnBuildBuilding, FellTrees as fnFellTrees, CutPeat as fnCutPeat, \
    UseBuilding as fnUseBuilding, BuildSettlement as fnBuildSettlement, Validation
from .objects import LedgerEntry
from .goods import Wine, Whiskey, Malt, Beer, Grapes, Flour, Bread, goods_map


class Command(object):
    __metaclass__ = ABCMeta
    match_regex = re.compile(r'^.*$')

    def __init__(self, game, executor_id, command_string):
        super(Command, self).__init__()
        self._is_partial = False
        self.parent_command = None
        self.game = game
        self._executor_id = executor_id
        self.command_string = command_string
        self.match = self.match_regex.match(self.command_string)

    @property
    def is_partial(self):
        return self._is_partial

    @abstractproperty
    def allowed_phases(self):
        pass

    @abstractproperty
    def needs_executor(self):
        pass

    @property
    def executor_index(self):
        if self._executor_id:
            for index in range(len(self.game.seats)):
                if self.game.seats[index].pk == self._executor_id:
                    return index
        return None

    @property
    def executor(self):
        index = self.executor_index
        if index is not None:
            return self.game.seats[index]
        return None

    @abstractmethod
    def validate(self):
        if self.allowed_phases and self.game.phase not in self.allowed_phases:
            raise InvalidOpCode("'{0}' not valid in {1}".format(self.command_string, self.game.phase))
        if not self.needs_executor and self.executor:
            raise InvalidOpCode("executor invalid for {0}".format(self.command_string))
        if self.needs_executor and not self.executor:
            raise InvalidOpCode("{0} requires executor".format(self.command_string))
        if not self.match:
            raise InvalidArguments(self.command_string)

    @abstractmethod
    def apply(self, previous_command=None):
        self.parent_command = previous_command
        self.validate()
        self.game.ledger.append(LedgerEntry(self.command_string, executor_index=self.executor_index))

    def finalize_apply(self):
        pass

    @classmethod
    def command_factory(cls, game, executor_id, command_string):
        for (match_string, command_class) in command_map:
            if re.match(match_string, command_string):
                return command_class(game, executor_id, command_string)
        else:
            raise InvalidArguments(command_string)


class ExecutorCommand(Command):
    @property
    def allowed_phases(self):
        raise NotImplementedError()

    @property
    def needs_executor(self):
        return True

    def validate(self):
        super(ExecutorCommand, self).validate()

    def apply(self, previous_command=None):
        super(ExecutorCommand, self).apply(previous_command)


class Action(ExecutorCommand):
    @property
    def allowed_phases(self):
        return {Phase.Action, Phase.FinalAction, Phase.BonusRound}

    def apply(self, previous_command=None):
        super(Action, self).apply(previous_command)
        self.executor.actions_taken += 1


class Comment(Command):
    match_regex = re.compile(r'^.*$')

    @property
    def allowed_phases(self):
        return set()

    @property
    def needs_executor(self):
        return False

    def validate(self):
        pass

    def apply(self, previous_command=None):
        pass


class Option(Command):
    match_regex = re.compile(
        r'^option\s+(?P<option>\S+)$'
    )

    def __init__(self, *args, **kwargs):
        super(Option, self).__init__(*args, **kwargs)
        self.option = False

    @property
    def allowed_phases(self):
        return {Phase.Setup}

    @property
    def needs_executor(self):
        return False

    def validate(self):
        super(Option, self).validate()

        self.option = self.match.group('option')

        if self.option == 'one-player':
            if self.game.number_of_players in (1, ):
                return
        elif self.option == 'short-game':
            if self.game.number_of_players in (3, 4):
                return
        elif self.option == 'long-game':
            if self.game.number_of_players == 2:
                return
        elif self.option == 'remove-c-quarry':
            if self.game.number_of_players == 4:
                return
            if 'short-game' in self.game.options:
                return
        elif self.option == 'loamy-landscape':
            if self.game.variant == Variant.France:
                return
        elif self.option == 'randomize-seats':
            if self.game.number_of_players in (2, 3, 4):
                return

        raise InvalidArguments(self.command_string)

    def apply(self, previous_command=None):
        super(Option, self).apply(previous_command)
        self.game.options.add(self.option)
        if self.option == 'one-player':
            self.game.available_landscapes[LandscapeType.District].reverse()
            self.game.available_landscapes[LandscapeType.Plot].reverse()

            neutral_seat = [s for s in self.game.seats if s.is_neutral][0]
            neutral_seat.heartland.landscape_spaces[0][0].remove_card()
            neutral_seat.heartland.landscape_spaces[0][1].remove_card()
            neutral_seat.heartland.landscape_spaces[1][0].remove_card()
            neutral_seat.heartland.landscape_spaces[1][1].remove_card()
            neutral_seat.heartland.landscape_spaces[2][0].remove_card()
            neutral_seat.heartland.landscape_spaces[0][0].add_card(BuildersMarket(owner=neutral_seat))

        if self.option == 'short-game':
            self.game.gameboard.gameboard_type = Gameboard.ShortThreeFourPlayer

            for seat in self.game.seats:
                # Remove a Moor, a Forest, and a LayBrother from each player in the short game
                seat.heartland.landscape_spaces[0][0].remove_card()
                seat.heartland.landscape_spaces[1][0].remove_card()
                seat.clergy_pool.pop()

        elif self.option == 'long-game':
            self.game.gameboard.production_wheel = ProductionWheel.Standard

        elif self.option == 'remove-c-quarry':
            # Nothing special needs to be done here.  The method that grabs the available buildings will look for this
            # option and remove the C Quarry if necessary
            pass

        elif self.option == 'loamy-landscape':
            # Nothing special needs to be done here.  The method that grabs the available buildings will look for this
            # option and use Loamy Landscape if necessary
            pass

        elif self.option == 'randomize-seats':
            # Nothing special needs to be done here.  This will be used by the game's start() method to do the final
            # setup
            pass


class Setup(Command):
    match_regex = re.compile(
        r'^setup\s+(?P<keyword>\S+)(\s+(?P<parameter>\S+))?$'
    )

    def __init__(self, *args, **kwargs):
        super(Setup, self).__init__(*args, **kwargs)
        self.keyword = False
        self.parameter = False

    @property
    def allowed_phases(self):
        return {Phase.Setup}

    @property
    def needs_executor(self):
        return False

    def validate(self):
        super(Setup, self).validate()

        self.keyword = self.match.group('keyword')
        self.parameter = self.match.group('parameter')

        if self.keyword == 'variant':
            if self.parameter in ('france', 'ireland'):
                return
        elif self.keyword == 'finalize':
            if not self.parameter:
                return
        elif self.keyword == 'start':
            if not self.parameter:
                return
        raise InvalidArguments(self.command_string)

    def apply(self, previous_command=None):
        super(Setup, self).apply(previous_command)
        if self.keyword == 'variant':
            if self.parameter == 'france':
                self.game.variant = Variant.France
                for seat in self.game.seats:
                    seat.goods['grapes'] = Grapes()
                    seat.goods['wine'] = Wine()
                    seat.goods['flour'] = Flour()
                    seat.goods['bread'] = Bread()
            elif self.parameter == 'ireland':
                self.game.variant = Variant.Ireland
                for seat in self.game.seats:
                    seat.goods['malt'] = Malt()
                    seat.goods['beer'] = Beer()
                    seat.goods['whiskey'] = Whiskey()

        elif self.keyword == 'finalize':
            if 'randomize-seats' in self.game.options:
                rand = random.Random(self.game.seed)
                new_seating_order = list(range(1, self.game.number_of_players + 1))
                rand.shuffle(new_seating_order)
                seats = self.game.seats
                for i in range(len(seats)):
                    seats[i].seat_order = new_seating_order[i]

            house_index = 0
            if self.game.number_of_players == 1:
                house_index = 12
            else:
                if self.game.number_of_players == 2:
                    house_index = 7
                elif 'short-game' in self.game.options:
                    house_index = 3
                elif self.game.number_of_players == 3:
                    house_index = 6
                elif self.game.number_of_players == 4:
                    house_index = 7
                for seat in self.game.seats:
                    seat.goods['clay'] += 1
                    seat.goods['wood'] += 1
                    seat.goods['peat'] += 1
                    seat.goods['coin'] += 1
                    seat.goods['grain'] += 1
                    seat.goods['livestock'] += 1
            self.game.gameboard[ResourceToken.House] += house_index

            self.game.age = Age.Start
            self.game.available_buildings = []
            self.game.add_new_age_buildings()

        elif self.keyword == 'start':
            self.game.round = 0
            self.game.phase = Phase.RoundStart
            return


# TODO -- This command needs to be rewritten to explicitly take what the resources are getting converted into
# TODO -- Since a few things like Grain, Whiskey, and Wine can convert into multiple things
class Convert(ExecutorCommand):
    match_regex = re.compile(
        r'^convert\s+(?P<amount_from>\d+)\s+(?P<convert_from>\S+)\s+to\s+(?P<amount_to>\d+)\s+(?P<convert_to>\S+)?$'
    )

    def __init__(self, *args, **kwargs):
        super(Convert, self).__init__(*args, **kwargs)
        self.amount_from = 0
        self.convert_from = 0
        self.amount_to = 0
        self.convert_to = 0

    @property
    def allowed_phases(self):
        return {Phase.Action, Phase.FinalAction, Phase.BonusRound, Phase.Settlement}

    def validate(self):
        super(Convert, self).validate()

        self.amount_from = int(self.match.group('amount_from'))
        self.convert_from = self.match.group('convert_from')
        self.amount_to = int(self.match.group('amount_to'))
        self.convert_to = self.match.group('convert_to')

        if self.convert_from in self.executor.goods and self.convert_to in self.executor.goods:
            if self.executor.goods[self.convert_from] < self.amount_from:
                raise NotEnoughGoods(self.convert_from)

            if self.convert_from == 'grain' and self.convert_to == 'straw':
                return
            if self.convert_from in ('whiskey', 'wine') and self.convert_to == 'coin':
                return

            # Still not 100% sure that I want to allow these.  Perhaps it should be done with a keyword like:
            # Use f05, spend 3 wood as energy, convert 5 flour to 5 bread
            if self.executor.goods[self.convert_from].is_temporary:
                raise InvalidGoodsConversion(self.convert_from)

            if not self.executor.goods[self.convert_to].is_temporary:
                raise InvalidGoodsConversion(self.convert_from)

            return

        raise InvalidArguments(self.command_string)

    def apply(self, previous_command=None):
        super(Convert, self).apply(previous_command)
        self.executor.goods[self.convert_from] -= self.amount_from
        self.executor.goods[self.convert_to] += self.amount_to


class BuyLandscape(ExecutorCommand):
    """
    Syntax for command arguments is: '<type> as <side> at <row>' or 'buy <type> at <row> as <side>'
    <type> is District or Plot
    <side> is Side1 or Side2
    <row> is an integer indicating which row it should be on
    """
    match_regex = re.compile(
        r'^buy\s+(?P<landscape_type>(district|plot))\s+as\s+(?P<side>(side1|side2))\s+at\s+(?P<row>\d{1,2})$'
    )

    def __init__(self, *args, **kwargs):
        super(BuyLandscape, self).__init__(*args, **kwargs)
        self.landscape_type = None
        self.side = None
        self.row = 0

    landscape_map = {
        LandscapeType.District: {
            'side1': DistrictSide.MoorForestForestHillsideHillside,
            'side2': DistrictSide.ForestPlainsPlainsPlainsHillside
        },
        LandscapeType.Plot: {
            'side1': PlotSide.Coastal,
            'side2': PlotSide.Mountain
        }
    }

    @property
    def allowed_phases(self):
        return {Phase.Action, Phase.BonusRound, Phase.FinalAction, Phase.Settlement}

    def validate(self):
        super(BuyLandscape, self).validate()

        self.landscape_type = self.match.group('landscape_type').capitalize()
        self.side = self.landscape_map.get(self.landscape_type, {}).get(self.match.group('side'), None)
        self.row = int(self.match.group('row'))

        if self.executor.landscape_purchased_this_turn:
            raise LandscapeAlreadyPurchased()

        if self.landscape_type and self.side and self.row:
            # Check to see if this is a valid landscape
            if not self.game.available_landscapes[self.landscape_type]:
                raise NoLandscapeAvailable(self.landscape_type)

            topmost_landscape = self.game.available_landscapes[self.landscape_type][0]
            # Check to see that we have enough money for this landscape
            if topmost_landscape.cost > self.executor.goods['coin'].total_money_value:
                raise NotEnoughGoods()

            topmost_landscape.landscape_side = self.side
            available_coordinates = self.executor.available_landscape_coordinates(topmost_landscape)

            if (self.row, topmost_landscape.column) in available_coordinates:
                # We've finally validated that this is a correct thing
                return

        raise InvalidArguments(self.command_string)

    def apply(self, previous_command=None):
        super(BuyLandscape, self).apply(previous_command)

        landscape = self.game.available_landscapes[self.landscape_type].pop(0)
        landscape.landscape_side = self.side
        landscape.row = self.row
        self.executor.goods['coin'] -= landscape.cost
        self.executor.landscapes.append(landscape)
        self.executor.landscape_purchased_this_turn = True


class BuildBuilding(Action):
    """
    Syntax for command arguments is: '<building_id> at <coordinate>[(,| and) place prior]'
    <building_id> is the id for the building
    <coordinate> is <row><column_alpha>
    <row> is an integer indicating which row it should be in
    <column_alpha> is a letter a-i indicating which column it should be in
    optionally, ' and place prior' will instruct the action to place and use the prior at the building
    """
    match_regex = re.compile(
        r'^build\s+(?P<building_id>[gfi][a-z0-9][0-9])'
        r'\s+at\s+\b(?P<row>[1-9][0-9])(?P<col>[a-i])\b'
        r'((?P<use_prior>\s+and\s+place\s+prior)'
        r'(\s+to\s+(?P<rest>.+))?)?$'
    )

    def __init__(self, *args, **kwargs):
        super(BuildBuilding, self).__init__(*args, **kwargs)

    @property
    def argument_minimum(self):
        return 3

    @property
    def argument_maximum(self):
        return 8

    def apply(self, previous_command=None):
        super(BuildBuilding, self).apply(previous_command)

        function = fnBuildBuilding()
        validation = Validation(remaining_arguments=self.command_string)
        validation.update(function.execute(self.executor, validation))

        if not validation.success:
            raise validation.exception or InvalidArguments(self.command_string)

        return


class BuildSettlement(Action):
    """
    Syntax for command arguments is: '<settlement_id> at <coordinate> with <goods_list>'
    <settlement_id> is the id for the settlement
    <coordinate> is <row><column_alpha>
    <row> is an integer indicating which row it should be in
    <column_alpha> is a letter a-i indicating which column it should be in
    <goods_list> is a list of space-separated '<good_amount> <good>' items
    """
    match_regex = re.compile(
        r'^build\s+(?P<settlement_id>s[0-9]{2})'
        r'\s+at\s+\b(?P<row>[1-9][0-9])(?P<col>[a-i])\b'
        r'\s+with\s+(?P<goods>(\b(0|[1-9][0-9]*)\s+[-a-z]+\b)(\s+\b(0|[1-9][0-9]*)\s+[-a-z]+\b)*)'
        r'(\s+(?P<rest>.+))?$'
    )

    def __init__(self, *args, **kwargs):
        super(BuildSettlement, self).__init__(*args, **kwargs)

    @property
    def allowed_phases(self):
        return {Phase.Settlement}

    @property
    def argument_minimum(self):
        return 6

    def apply(self, previous_command=None):
        super(BuildSettlement, self).apply(previous_command)

        function = fnBuildSettlement()
        validation = Validation(remaining_arguments=self.command_string)
        validation.update(function.execute(self.executor, validation))

        if not validation.success:
            raise validation.exception or InvalidArguments(self.command_string)

        return


class Pass(ExecutorCommand):
    """
    Syntax for command arguments is: ''
    This command passes the current action and instructs the game to go to the next turn
    """
    match_regex = re.compile(r'^pass$')

    def __init__(self, *args, **kwargs):
        super(Pass, self).__init__(*args, **kwargs)

    @property
    def allowed_phases(self):
        return {Phase.Action, Phase.FinalAction, Phase.BonusRound, Phase.Settlement}

    def validate(self):
        super(Pass, self).validate()

        # Actions are a MUST in these Action phases but the player is not required to build a settlement during the
        # Settlement phase
        if self.game.phase in {Phase.Action, Phase.FinalAction, Phase.BonusRound}:
            if self.game.number_of_players in {3, 4}:
                if self.executor.actions_taken < 1:
                    raise ActionRequired()
            elif self.game.number_of_players == 2:
                if 'long-game' in self.game.options:
                    if self.game.round_start_seat == self.executor:
                        if self.executor.actions_taken < 2:
                            raise ActionRequired()
                    else:
                        if self.executor.actions_taken < 1:
                            raise ActionRequired()
                else:
                    if self.executor.actions_taken < 2:
                        raise ActionRequired()
            elif self.game.number_of_players == 1:
                if self.executor.actions_taken < 2:
                    raise ActionRequired()

    def apply(self, previous_command=None):
        super(Pass, self).apply(previous_command)
        self.game.pass_turn(self.executor)


class FellTrees(Action):
    """
    Syntax for command arguments is: 'at <coordinate> choose <token>'
    <coordinate> is <row><column_alpha>
    <row> is an integer indicating which row it should be in
    <column_alpha> is a letter a-i indicating which column it should be in
    <token> is either wood or joker
    This command removes a wood card from the designated coordinate and gives the player the number of resources at the
    token's wheel location
    """
    match_regex = re.compile(
        r'^fell-trees\s+(at\s+(?P<row>\d{1,2})(?P<col>[a-i])\s+to\s+choose\s+(?P<token>\S+))?$'
    )

    def __init__(self, *args, **kwargs):
        super(FellTrees, self).__init__(*args, **kwargs)
        self.space = None
        self.token = None

    @property
    def allowed_phases(self):
        return {Phase.Action, Phase.FinalAction}

    @property
    def argument_counts(self):
        return {0, 4}

    def apply(self, previous_command=None):
        super(FellTrees, self).apply(previous_command)

        function = fnFellTrees()
        validation = Validation(remaining_arguments=self.command_string)
        validation.update(function.execute(self.executor, validation))

        if not validation.success:
            raise validation.exception or InvalidArguments(self.command_string)

        return


class CutPeat(Action):
    """
    Syntax for command arguments is: 'at <coordinate> choose <token>'
    <coordinate> is <row><column_alpha>
    <row> is an integer indicating which row it should be in
    <column_alpha> is a letter a-i indicating which column it should be in
    <token> is either peat or joker
    This command removes a wood card from the designated coordinate and gives the player the number of resources at the
    token's wheel location
    """

    match_regex = re.compile(
        r'^cut-peat\s+(at\s+(?P<row>\d{1,2})(?P<col>[a-i])\s+to\s+choose\s+(?P<token>\S+))?$'
    )

    def __init__(self, *args, **kwargs):
        super(CutPeat, self).__init__(*args, **kwargs)
        self.space = None
        self.token = None

    @property
    def allowed_phases(self):
        return {Phase.Action, Phase.FinalAction}

    @property
    def argument_counts(self):
        return {0, 4}

    def apply(self, previous_command=None):
        super(CutPeat, self).apply(previous_command)

        function = fnCutPeat()
        validation = Validation(remaining_arguments=self.command_string)
        validation.update(function.execute(self.executor, validation))

        if not validation.success:
            raise validation.exception or InvalidArguments(self.command_string)

        return


class UseBuilding(Action):
    """
    This command is quite varied in the allowed syntax and it should be left up to each individual building to validate
    its arguments.  This command can also chain into other commands (including itself if the building allows it).
    At a minimum, the matching pattern is:
    '<building_id> (with <clergy>|pay <payment_amount> <payment_good>)[ <rest>]' where:
    <building_id> is the id (lower left-hand corner) of the building to be used.
    <clergy> is either 'prior' or 'lay-brother'
    <payment_amount> <payment_good> is how much to pay for the work contract if the building isn't the executors.
        This can be 1 coin, 2 coin (if Winery or Whiskey Distillery have been build), 1 wine, or 1 whiskey.
    <rest> is arguments to be passed into the building to be processed.  This may be an empty string.
    If a work contract is to be paid and the payment receiver has a choice of prior or lay brother, then this command
        needs to be interrupted to handle the clergy selection before continuing.
    """
    match_regex = re.compile(
        r'^'
        r'('
        r'place\s+(?P<clergy>(prior|lay-brother))'
        r'\s+to\s+use\s+(?P<building_id>[a-z][a-z0-9][0-9])'
        r'(\s+to\s+(?P<arguments>.+))?'
        r'|'
        r'pay\s+(?P<payment_amount>\d+)\s+(?P<payment_good>\S+)\s+to\s+(?P<owner_color>\S+)'
        r'\s+to\s+use\s+(?P<contract_building_id>[a-z][a-z0-9][0-9])'
        r'(\s+to\s+(?P<contract_arguments>.+))?'
        r'|'
        r'place\s+(?P<contract_clergy>(prior|lay-brother))'
        r')'
        r'$'
    )

    def __init__(self, *args, **kwargs):
        super(UseBuilding, self).__init__(*args, **kwargs)
        self.building = None
        self.clergy = None
        self.owner = None
        self.payment = None
        self.arguments = None
        self._mode = None

    @property
    def allowed_phases(self):
        return {Phase.Action, Phase.FinalAction, Phase.BonusRound}

    def validate(self):
        super(UseBuilding, self).validate()

        clergy_name = self.match.group('clergy')
        building_id = self.match.group('building_id')
        arguments = self.match.group('arguments')

        payment_amount = self.match.group('payment_amount')
        payment_good = self.match.group('payment_good')
        owner_color = self.match.group('owner_color')
        contract_building_id = self.match.group('contract_building_id')
        contract_arguments = self.match.group('contract_arguments')

        contract_clergy = self.match.group('contract_clergy')

        # Mode #1 -- Using your own building & placing a clergyman there
        if clergy_name and building_id:
            self._mode = 1

            matching_spaces = set()
            if self.game.phase == Phase.BonusRound:
                self.owner = self.executor
                for seat in self.game.seats:
                    matching_spaces = seat.find_spaces_matching(lambda s: s.card and s.card.id == building_id)
                    if matching_spaces:
                        break
            else:
                self.owner = self.executor
                matching_spaces = self.owner.find_spaces_matching(lambda s: s.card and s.card.id == building_id)

            if not matching_spaces:
                raise BuildingNotFound(building_id)
            if len(matching_spaces) > 1:
                raise InvalidArguments("too many buildings found: {0}".format(building_id))
            self.building = matching_spaces.pop().card
            if not self.building:
                raise BuildingNotFound(building_id)

            available_clergy = [c for c in self.owner.clergy_pool if c.name == clergy_name]
            if not available_clergy:
                raise ClergyNotAvailable()
            self.clergy = available_clergy[0]

            self.arguments = arguments
            return

        # Mode #2 -- Paying to use an opponent's building
        elif payment_amount and payment_good and owner_color and contract_building_id:
            self._mode = 2
            payment_amount = int(payment_amount)

            self.owner = self.game.seat_by_color(owner_color)
            if not self.owner:
                raise InvalidArguments("no seat color {0}".format(owner_color))
            if self.owner == self.executor:
                raise PaymentNotNeeded("you can't pay yourself")

            matching_spaces = self.owner.find_spaces_matching(lambda s: s.card and s.card.id == contract_building_id)
            if not matching_spaces:
                raise BuildingNotFound(contract_building_id)
            if len(matching_spaces) > 1:
                raise InvalidArguments("too many buildings found: {0}".format(contract_building_id))
            self.building = matching_spaces.pop().card
            if not self.building:
                raise BuildingNotFound(contract_building_id)

            if not self.owner.clergy_pool:
                raise ClergyNotAvailable()
            if not payment_good:
                raise PaymentRequired()
            if payment_good not in {'coin', 'wine', 'whiskey'}:
                raise InvalidPayment()
            self.payment = goods_map[payment_good](payment_amount)
            if self.payment not in (self.game.work_contract_price, Wine(1), Whiskey(1)):
                raise InvalidPayment()
            if self.executor.goods[self.payment.name] < self.payment:
                raise NotEnoughGoods(self.payment)
            if len({c.name for c in self.owner.clergy_pool}) == 1:
                self.clergy = self.owner.clergy_pool[0]
            else:
                # If there is an option for the owner of the building about which clergy to use, then this command is
                # only partially resolved and needs to be resolved before continuing with the next step.
                self._is_partial = True
                if contract_arguments:
                    raise InvalidArguments(self.command_string)
                return

            self.arguments = contract_arguments
            return

        # Mode #3 -- Placing your clergyman into the building being contracted
        elif contract_clergy:
            self._mode = 3
            self.owner = self.executor
            # Mode #3 is always partial, since the player whose turn it is still needs to use the building
            self._is_partial = True
            self.game.action_seat_index = self.game.seats.index(self.parent_command.executor)

            matching_clergy = [c for c in self.executor.clergy_pool if c.name == contract_clergy]
            if not matching_clergy:
                raise ClergyNotAvailable(contract_clergy)

            self.clergy = matching_clergy[0]
            return

        raise NotImplementedError()

    def apply(self, previous_command=None):
        super(UseBuilding, self).apply(previous_command)

        # Make the work contract payment
        if self._mode == 1:
            # Assign the clergyman to the building
            self.owner.clergy_pool.remove(self.clergy)
            self.building.assign_clergy(self.clergy.owner, self.clergy)

            self.finalize_apply()

        elif self._mode == 2:
            self.executor.goods[self.payment.name] -= self.payment
            # If the contract is payed with coins, it goes to the building's owner instead of the bank
            if self.payment.name == 'coin':
                self.owner.goods[self.payment.name] += self.payment

            if self._is_partial:
                self.game.action_seat_index = self.game.seats.index(self.owner)
            else:
                # Assign the clergyman to the building
                self.owner.clergy_pool.remove(self.clergy)
                self.building.assign_clergy(self.owner, self.clergy)

                self.finalize_apply()

        elif self._mode == 3:
            self.executor.clergy_pool.remove(self.clergy)
            self.parent_command.building.assign_clergy(self.executor, self.clergy)

    def finalize_apply(self):
        super(UseBuilding, self).finalize_apply()

        if self._mode in (1, 2):
            # Use the building, with the extra parameters passed along
            function = fnUseBuilding(criteria=lambda x: {self.building})
            if self.arguments:
                arguments = 'use {0} to {1}'.format(self.building.id, self.arguments)
            else:
                arguments = 'use {0}'.format(self.building.id)
            validation = Validation(remaining_arguments=arguments)
            validation.update(function.execute(self.executor, validation))

            if not validation.success:
                raise validation.exception or InvalidArguments(self.arguments)

        elif self._mode == 3:
            self.parent_command.finalize_apply()


class Continuation(Action):
    """
    Syntax for command arguments is: '<rest>'
    <rest> is anything, really
    This is a continuation command from the UseBuilding/PlaceClergy command chain.  This throws an exception if it's
    used anywhere outside that context.  It must have a valid parent_command which also must have a valid parent_command
    """

    match_regex = re.compile(
        r'^use\s+(?P<building_id>[a-z][a-z0-9][0-9])'
        r'(\s+to\s+(?P<arguments>.+))?'
        r'$'
    )

    def __init__(self, *args, **kwargs):
        super(Continuation, self).__init__(*args, **kwargs)
        self.arguments = None

    @property
    def allowed_phases(self):
        return {Phase.Action}

    @property
    def argument_counts(self):
        return {1}

    def apply(self, previous_command=None):
        super(Continuation, self).apply(previous_command)

        if not self.parent_command or not self.parent_command.parent_command or \
                self.match.group('building_id') != self.parent_command.parent_command.building.id:
            raise InvalidArguments()

        self.arguments = self.match.group('arguments')

        self.finalize_apply()

    def finalize_apply(self):
        super(Continuation, self).finalize_apply()
        self.parent_command.parent_command.arguments = self.arguments
        self.parent_command.finalize_apply()


command_map = [
    (r'^#.*$', Comment),
    (r'^//.*$', Comment),
    (r'^option\s+.+$',  Option),
    (r'^setup\s+.+$',  Setup),
    (r'^convert\s+.+$',  Convert),
    (r'^buy\s+.+$',  BuyLandscape),
    (r'^build\s+[gfi].+$',  BuildBuilding),
    (r'^build\s+s.+$',  BuildSettlement),
    (r'^pass$',  Pass),
    (r'^fell-trees\s+.+$',  FellTrees),
    (r'^cut-peat\s+.+$',  CutPeat),
    (r'^place|pay\s+.+$',  UseBuilding),
    (r'^use.+$', Continuation),
]