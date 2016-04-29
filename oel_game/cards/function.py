__author__ = 'Jurek'
from abc import ABCMeta, abstractmethod
import copy
from decimal import Decimal
import re

from ..enums import CardType, ResourceToken, FunctionJoiner, LandscapeType, DistrictSide, PlotSide
from ..exceptions import InvalidArguments, SpaceNotFound, BuildingPresent, BuildingNotFound, InvalidLandscapePlot, \
    NotEnoughGoods, NoLandscapeAvailable
from ..goods import GoodsSet, Goods, Wood, Peat, Coin, Energy, Food, Money, Points, goods_map


class Validation(object):
    def __init__(self, success=True, remaining_arguments=None, leftover_goods=None):
        self.success = success
        self.remaining_arguments = remaining_arguments
        self.leftover_goods = {g.name: g for g in [Energy(), Food(), Money(), Points()]}
        #self.leftover_goods = dict({(g.name, g) for g in {Energy(), Food(), Money(), Points()}})
        if leftover_goods is not None:
            for good in leftover_goods.values():
                self.leftover_goods[good.name] += good
        self.step = None
        self._exception = None

    @property
    def exception(self):
        return self._exception

    @exception.setter
    def exception(self, value):
        self._exception = value
        if value is not None:
            self.success = False

    def update(self, validation):
        self.success = validation.success
        self.remaining_arguments = validation.remaining_arguments
        if validation.leftover_goods:
            for good in validation.leftover_goods.values():
                self.leftover_goods[good.name] = good
        self.step = validation.step
        if validation.exception and not self.exception:
            self.exception = validation.exception


class Function(object):
    def __init__(self):
        self._steps = []
        self._joiner = FunctionJoiner.And

    def add(self, step, joiner=None):
        self._steps.append(step)
        if joiner:
            self._joiner = joiner
        else:
            if not joiner and not self._joiner and joiner != self._joiner:
                raise TypeError("Joiner must match existing joiner: {0} / {1}".format(self._joiner, joiner))

    @property
    def steps(self):
        return self._steps

    @property
    def joiner(self):
        return self._joiner

    def execute(self, seat, arguments):
        # Validate the parameters passed in to ensure that they're sane
        validation = Validation(remaining_arguments=arguments)
        successes = []
        for index in range(len(self._steps)):
            step = self._steps[index]
            validation = step.execute(seat, validation)
            successes.append(validation.success)

            if self._joiner == FunctionJoiner.Or:
                # If this step failed, restore the arguments for the next attempt
                if not validation.success:
                    # Let's try again
                    validation = Validation(remaining_arguments=arguments)
                else:
                    # "Or" must be exactly 1 success
                    if successes.count(True) > 1:
                        if validation.exception:
                            raise validation.exception
                        raise InvalidArguments(arguments)

            elif self._joiner == FunctionJoiner.AndOr:
                # If this step failed, restore the arguments for the next attempt
                if not validation.success:
                    # Let's try again
                    validation = Validation(remaining_arguments=arguments)

            elif self._joiner == FunctionJoiner.AndThenOr:
                if not validation.success:
                    # This might be the "Or" without the first step being executed
                    validation = Validation(remaining_arguments=arguments)

            # All steps must be parsed and valid for "And"
            elif self._joiner == FunctionJoiner.And:
                if not validation.success:
                    if validation.exception:
                        raise validation.exception
                    raise InvalidArguments(arguments)

        if self._joiner in (FunctionJoiner.Additionally, FunctionJoiner.AndOr):
            if not any(successes):
                if validation.exception:
                    raise validation.exception
                raise InvalidArguments(arguments)

        # "AndThenOr" must have either all successes or the first failure and the rest success
        elif self._joiner == FunctionJoiner.AndThenOr:
            if all(successes) or not successes[0] and all(successes[1:]):
                pass
            else:
                if validation.exception:
                    raise validation.exception
                raise InvalidArguments(arguments)

        elif self._joiner == FunctionJoiner.Or:
            if any(successes):
                validation.remaining_arguments = None

        if validation.remaining_arguments:
            if validation.exception:
                raise validation.exception
            raise InvalidArguments(validation.remaining_arguments)
        return validation


class FunctionStepBase(object):
    __metaclass__ = ABCMeta
    goods_regex = re.compile(
        r'\b(?P<amount>(0|[1-9][0-9]*))\s+(?P<good>[-a-z]+)\b'
    )
    coordinate_regex = re.compile(
        r'\b(?P<row>[1-9][0-9])(?P<col>[a-i])\b'
    )

    def __init__(self):
        self.validation = Validation()

    @abstractmethod
    def task(self, seat):
        pass

    @abstractmethod
    def execute(self, seat, validation, parameters=None):
        self.validation.update(validation)
        self.validation.step = self


class SpendBase(FunctionStepBase):
    __metaclass__ = ABCMeta
    match_regex = re.compile(
        r'^spend\s+(?P<goods>(\b(0|[1-9][0-9]*)\s+[-a-z]+\b)(\s+\b(0|[1-9][0-9]*)\s+[-a-z]+\b)*)'
        r'(\s+to\s+(?P<next_step>.+))?'
        r'(\s+and\s+(?P<after_step>.+))?$'
    )

    def task(self, seat):
        raise NotImplementedError()

    @abstractmethod
    def execute(self, seat, validation, parameters=None):
        super(SpendBase, self).execute(seat, validation, parameters=parameters)


class GainBase(FunctionStepBase):
    __metaclass__ = ABCMeta
    match_regex = re.compile(
        r'^gain\s+(?P<goods>(\b(0|[1-9][0-9]*)\s+[-a-z]+\b)(\s+\b(0|[1-9][0-9]*)\s+[-a-z]+\b)*)(\s+(?P<rest>.+))?$'
    )

    def task(self, seat):
        raise NotImplementedError()

    @abstractmethod
    def execute(self, seat, validation, parameters=None):
        super(GainBase, self).execute(seat, validation, parameters=parameters)


class AndConditional(FunctionStepBase):
    match_regex = re.compile(
        r'^(?P<option1>.+?)(\s+and\s+(?P<option2>.+))?$'
    )

    def __init__(self, next_step1, next_step2):
        super(AndConditional, self).__init__()
        self.next_step1 = next_step1
        self.next_step2 = next_step2

    def task(self, seat):
        return {'and': {
            'next_steps': [
                None if not self.next_step1 else self.next_step1.task(seat),
                None if not self.next_step2 else self.next_step2.task(seat)
            ]
        }}

    def execute(self, seat, validation, parameters=None):
        super(AndConditional, self).execute(seat, validation, parameters=parameters)

        match = AndConditional.match_regex.match(validation.remaining_arguments or '')
        if not match:
            self.validation.success = False
            return self.validation

        option1 = match.group('option1')
        option2 = match.group('option2')

        if option1 and option2:
            self.validation.remaining_arguments = option1
            self.validation.update(self.next_step1.execute(
                seat, self.validation, parameters
            ))
            if self.validation.success:
                self.validation.remaining_arguments = option2
                self.validation.update(self.next_step2.execute(
                    seat, self.validation, parameters
                ))
        else:
            self.validation.remaining_arguments = option1
            next_step1 = self.next_step1.execute(
                seat, self.validation, parameters
            )

            self.validation.exception = None
            self.validation.remaining_arguments = None
            next_step2 = self.next_step2.execute(
                seat, self.validation, parameters
            )

            if next_step1.success and not next_step2.success:
                self.validation.update(next_step2)
                return self.validation
            elif not next_step1.success and not next_step2.success:
                self.validation.remaining_arguments = None
                self.next_step1.validation.exception = None
                next_step1 = self.next_step1.execute(
                    seat, self.validation, parameters
                )

                self.validation.remaining_arguments = option1
                self.next_step2.validation.exception = None
                next_step2 = self.next_step2.execute(
                    seat, self.validation, parameters
                )

                if next_step2.success and not next_step1.success:
                    self.validation.update(next_step1)
                    return self.validation
                elif not next_step1.success and not next_step2.success:
                    self.validation.update(next_step1)
                    return self.validation
                else:
                    self.validation.update(next_step1)
                    self.validation.update(next_step2)
            else:
                self.validation.update(next_step1)
                self.validation.update(next_step2)

        return self.validation


class AndOr(FunctionStepBase):
    match_regex = re.compile(
        r'^(?P<option1>.+?)(\s+and\s+(?P<option2>.+))?$'
    )

    def __init__(self, next_step1, next_step2):
        super(AndOr, self).__init__()
        self.next_step1 = next_step1
        self.next_step2 = next_step2

    def task(self, seat):
        return {'and_or': {
            'next_steps': [
                None if not self.next_step1 else self.next_step1.task(seat),
                None if not self.next_step2 else self.next_step2.task(seat)
            ]
        }}

    def execute(self, seat, validation, parameters=None):
        super(AndOr, self).execute(seat, validation, parameters=parameters)

        match = AndOr.match_regex.match(validation.remaining_arguments or '')
        if not match:
            self.validation.success = False
            return self.validation

        option1 = match.group('option1')
        option2 = match.group('option2')

        if option1 and option2:
            self.validation.remaining_arguments = option1
            self.validation.update(self.next_step1.execute(
                seat, self.validation, parameters
            ))
            if self.validation.success:
                self.validation.remaining_arguments = option2
                self.validation.update(self.next_step2.execute(
                    seat, self.validation, parameters
                ))
        else:
            self.validation.remaining_arguments = option1
            next_step1 = self.next_step1.execute(
                seat, self.validation, parameters
            )
            if next_step1.success:
                self.validation.update(next_step1)
            else:
                self.validation.remaining_arguments = option1
                self.validation.update(self.next_step2.execute(
                    seat, self.validation, parameters
                ))

        return self.validation


class UseProductionWheel(FunctionStepBase):
    match_regex = re.compile(
        r'^choose\s+(?P<token>\w+)(\s+to\s+(?P<rest>.+))?$'
    )

    def __init__(self, resource_tokens, next_step=None):
        super(UseProductionWheel, self).__init__()
        if isinstance(resource_tokens, ResourceToken):
            resource_tokens = {resource_tokens}
        self.resource_tokens = resource_tokens
        self.next_step = next_step

        self.resource_token = None

    def task(self, seat):
        return {'production_wheel': {
            'tokens': self.resource_tokens,
            'next_step': None if not self.next_step else self.next_step.task(seat)
        }}

    def execute(self, seat, validation, parameters=None):
        super(UseProductionWheel, self).execute(seat, validation, parameters=parameters)
        self.resource_token = None

        match = UseProductionWheel.match_regex.match(validation.remaining_arguments or '')
        if not match:
            self.validation.success = False
            return self.validation

        if match.group('token') not in self.resource_tokens:
            self.validation.success = False
            return self.validation
        self.resource_token = match.group('token')

        count = seat.game.production_value(self.resource_token)

        self.validation.remaining_arguments = match.group('rest')
        if self.next_step:
            self.validation.update(self.next_step.execute(
                seat, self.validation, {'count': count, 'token': self.resource_token}
            ))

        if self.validation.success:
            seat.game.produce(self.resource_token)

        return self.validation


class UseBuilding(FunctionStepBase):
    match_regex = re.compile(
        r'^use\s+(?P<building_id>\b[a-z][0-9a-z][0-9]\b)(\s+to\s+(?P<rest>.+))?$'
    )

    def __init__(self, criteria, next_step=None):
        super(UseBuilding, self).__init__()
        self.criteria = criteria
        self.next_step = next_step

        self.building = None

    def task(self, seat):
        return {'use_building': {
            'buildings': self.criteria(seat),
            'next_step': None if not self.next_step else self.next_step.task(seat)
        }}

    def execute(self, seat, validation, parameters=None):
        super(UseBuilding, self).execute(seat, validation, parameters=parameters)
        self.building = None

        match = UseBuilding.match_regex.match(validation.remaining_arguments or '')
        if not match:
            self.validation.success = False
            return self.validation

        buildings = self.criteria(seat)
        matching_buildings = {b for b in buildings if match.group('building_id') in (b.id, b.name.lower())}
        if not matching_buildings:
            self.validation.success = False
            return self.validation
        self.building = matching_buildings.pop()

        self.validation.remaining_arguments = match.group('rest')
        self.validation.update(self.building.use(seat, self.validation.remaining_arguments))

        if self.next_step:
            self.validation.update(self.next_step.execute(seat, self.validation, {}))

        return self.validation


class HaveBreaks(FunctionStepBase):
    def __init__(self, goods_breaks, next_step=None):
        super(HaveBreaks, self).__init__()
        self.goods_breaks = []
        for goods in goods_breaks:
            if isinstance(goods, Goods):
                goods = GoodsSet({goods})
            self.goods_breaks.append(goods)
        self.next_step = next_step

        self.index = None

    def task(self, seat):
        return {'have': {
            'goods_breaks': self.goods_breaks,
            'next_step': None if not self.next_step else self.next_step.task(seat)
        }}

    def execute(self, seat, validation, parameters=None):
        super(HaveBreaks, self).execute(seat, validation, parameters=parameters)
        self.index = None

        # This Function doesn't consume any of the argument string
        for index in range(len(self.goods_breaks)):
            break_met = True
            for good in self.goods_breaks[index]:
                if seat.goods[good.name] < good:
                    break_met = False
            if break_met:
                self.index = index

        if self.next_step:
            self.validation.update(self.next_step.execute(seat, self.validation, {'index': self.index}))

        return self.validation


class SpendExact(SpendBase):
    def __init__(self, goods, max_count=1, next_step=None):
        super(SpendExact, self).__init__()
        if isinstance(goods, Goods):
            goods = GoodsSet({goods})
        self.goods = dict((g.name, g) for g in goods)
        self.min = 0
        self.max = max_count
        self.next_step = next_step

        self.count = None
        self.spend_goods = None

    def task(self, seat):
        return {'spend': {
            'goods': self.goods,
            'max': self.max,
            'next_step': None if not self.next_step else self.next_step.task(seat)
        }}

    def execute(self, seat, validation, parameters=None):
        super(SpendExact, self).execute(seat, validation, parameters=parameters)
        self.count = self.spend_goods = None

        if not validation.remaining_arguments:
            self.count = 0
            self.spend_goods = GoodsSet()
            next_step = after_step = ''
        else:
            match = SpendExact.match_regex.match(validation.remaining_arguments or '')
            if not match:
                self.validation.success = False
                return self.validation
            goods = {}
            counts = copy.deepcopy(self.validation.leftover_goods)
            for goods_match in SpendExact.goods_regex.finditer(match.group('goods')):
                good = goods_map[goods_match.group('good')](int(goods_match.group('amount')))
                goods[good.name] = good + goods.get(good.name, 0)
            self.spend_goods = GoodsSet()
            for good in goods.values():
                self.spend_goods.add(good)
            for good in self.goods.values():
                # Check to see if any transitionary (Energy, Food, etc) goods are in the goods set
                if good.is_temporary:
                    value_attr = 'total_{0}_value'.format(good.name)
                    if good.name not in counts:
                        counts[good.name] = goods_map[good.name]()
                    for spend_good in goods.values():
                        counts[good.name] += Decimal(getattr(spend_good, value_attr)) / getattr(good, value_attr)
                    continue
                if good.name not in goods:
                    self.validation.success = False
                    return self.validation
                counts[good.name] = goods_map[good.name](Decimal(goods[good.name].count) / good.count)

            # Check normal goods first -- they take priority
            for good_name, good in counts.items():
                if good.is_temporary:
                    continue
                if self.max and good > self.max:
                    self.validation.exception = ValueError("too many goods specified: {0} x {1} > {2}".format(good.count, self.goods[good.name], self.max))
                    return self.validation
                if int(good.count) != good.count:
                    self.validation.exception = ValueError("fractional amounts of goods specified: {0}".format(good.count))
                    return self.validation
                count = int(good.count)
                if self.count is not None and self.count != count:
                    self.validation.success = False
                    return self.validation
                self.count = count

            # Temporary goods are checked after normal goods
            for good_name, good in counts.items():
                if good_name not in self.goods or not good.is_temporary:
                    continue
                # Temporary goods can be over-paid for (e.g. using 4 Bread for Stone Merchant)
                if self.max is not None:
                    count = min(self.max, good.count)
                else:
                    count = good.count
                if self.count is None:
                    self.count = count
                else:
                    self.count = min(self.count, count)
            for good_name, good in counts.items():
                if good_name not in self.goods or not good.is_temporary:
                    continue
                if self.count < good.count:
                    self.validation.leftover_goods[good.name] += (good.count - self.count)

            if self.max and self.count > self.max:
                self.validation.exception = ValueError("'count' of {0} must be at most {1}".format(self.count, self.max))
                return self.validation

            next_step = match.group('next_step')
            after_step = match.group('after_step')

        if self.count is not None:
            # Spend the goods
            seat.spend(self.spend_goods)

            if self.next_step:
                self.validation.remaining_arguments = next_step
                self.validation.update(self.next_step.execute(seat, self.validation, {'count': self.count}))
                if self.validation.remaining_arguments:
                    self.validation.success = False

            self.validation.remaining_arguments = after_step
        return self.validation


class SpendBreaks(SpendBase):
    def __init__(self, goods_breaks, next_step=None):
        super(SpendBreaks, self).__init__()
        self.goods_breaks = []
        for goods in goods_breaks:
            if isinstance(goods, Goods):
                goods = GoodsSet({goods})
            self.goods_breaks.append(goods)
        self.next_step = next_step

        self.index = None
        self.spend_goods = {}

    def task(self, seat):
        return {'spend': {
            'goods_breaks': self.goods_breaks,
            'next_step': None if not self.next_step else self.next_step.task(seat)
        }}

    def execute(self, seat, validation, parameters=None):
        super(SpendBreaks, self).execute(seat, validation, parameters=parameters)
        self.index = None
        self.spend_goods = {}

        if not validation.remaining_arguments:
            next_step = after_step = ''
        else:
            match = SpendBreaks.match_regex.match(validation.remaining_arguments or '')
            if not match:
                self.validation.success = False
                return self.validation
            self.spend_goods = {}
            for goods_match in SpendBreaks.goods_regex.finditer(match.group('goods')):
                good = goods_map[goods_match.group('good')](int(goods_match.group('amount')))
                self.spend_goods[good.name] = good + self.spend_goods.get(good.name, 0)

            for index in range(len(self.goods_breaks)):
                break_met = True
                goods_break = dict([(g.name, g) for g in copy.deepcopy(self.goods_breaks[index])])
                spend_goods = copy.deepcopy(self.spend_goods)
                for good in {g for g in goods_break.values() if not g.is_temporary}:
                    if good.name in spend_goods and spend_goods[good.name] >= good:
                        spend_goods[good.name] -= good
                        goods_break[good.name] -= good
                    else:
                        break_met = False
                        break
                if not break_met:
                    continue
                for good in {g for g in goods_break.values() if g.is_temporary}:
                    value_attr = 'total_{0}_value'.format(good.name)
                    for sg_name, sg in spend_goods.items():
                        sg_value = getattr(sg, value_attr)
                        if sg_value > 0:
                            goods_break[good.name] -= min(goods_break[good.name].count, sg_value)
                            sg -= sg
                for good in goods_break.values():
                    if good.count > 0:
                        break_met = False
                        break
                if break_met:
                    self.index = index

            seat.spend(self.spend_goods.values())

            next_step = match.group('next_step')
            after_step = match.group('after_step')

        if self.index is not None:
            if self.next_step:
                self.validation.remaining_arguments = next_step
                self.validation.update(self.next_step.execute(seat, self.validation, {'index': self.index}))
                if self.validation.remaining_arguments:
                    self.validation.success = False

        self.validation.remaining_arguments = after_step
        return self.validation


class SpendChoices(SpendBase):
    def __init__(self, goods_choices, max_count=1, count_scales=None, next_step=None):
        super(SpendChoices, self).__init__()
        self.goods_choices = []
        for goods in goods_choices:
            if isinstance(goods, Goods):
                goods = GoodsSet({goods})
            self.goods_choices.append(goods)
        self.max = max_count
        self.count_scales = count_scales
        self.next_step = next_step

        self.spend_goods = {}
        self.choice_indicies = []

    def task(self, seat):
        return {'spend': {
            'goods_choices': self.goods_choices,
            'max': self.max,
            'count_scales': self.count_scales,
            'next_step': None if not self.next_step else self.next_step.task(seat)
        }}

    def execute(self, seat, validation, parameters=None):
        super(SpendChoices, self).execute(seat, validation, parameters=parameters)
        self.spend_goods = {}
        self.choice_indicies = []

        match = SpendBreaks.match_regex.match(validation.remaining_arguments or '')
        if not match:
            self.validation.success = False
            return self.validation
        self.spend_goods = {}
        for goods_match in SpendBreaks.goods_regex.finditer(match.group('goods')):
            good = goods_map[goods_match.group('good')](int(goods_match.group('amount')))
            self.spend_goods[good.name] = good + self.spend_goods.get(good.name, 0)

        spend_goods = copy.deepcopy(self.spend_goods)
        for index in range(len(self.goods_choices)):
            choice_met = None
            goods_choice = dict([(g.name, g) for g in copy.deepcopy(self.goods_choices[index])])
            for good in {g for g in goods_choice.values() if not g.is_temporary}:
                choice_met = True
                if good.name in spend_goods and spend_goods[good.name] >= good:
                    spend_goods[good.name] -= good
                    goods_choice[good.name] -= good
                else:
                    choice_met = False
                    break
            if choice_met is False:
                continue
            elif choice_met is True:
                self.choice_indicies.append(index)

            maxes = {}
            for good in {g for g in goods_choice.values() if g.is_temporary}:
                spent_sum = good.__class__()
                value_attr = 'total_{0}_value'.format(good.name)
                for sg_name in spend_goods:
                    sg_value = getattr(spend_goods[sg_name], value_attr)
                    spent_sum += sg_value
                    if sg_value > 0:
                        goods_choice[good.name] -= min(goods_choice[good.name].count, sg_value)
                        spend_goods[sg_name].clear()
                maxes[good.name] = spent_sum.count / good.count
            if maxes:
                self.choice_indicies.extend([index] * int(min([v for v in maxes.values()])))

        if any(g for g in spend_goods.values() if g.count):
            self.validation.exception = ValueError("Unspent resources: {0}".format({g for g in spend_goods.values() if g.count}))
            return self.validation

        count = len(self.choice_indicies)
        if self.count_scales:
            count = sum(self.count_scales[i] for i in self.choice_indicies)
        if count > self.max:
            self.validation.exception = ValueError("'count' of {0} must be at most {1}".format(count, self.max))
            return self.validation

        if self.spend_goods:
            seat.spend(self.spend_goods.values())

            if self.next_step:
                self.validation.remaining_arguments = match.group('next_step')
                self.validation.update(
                    self.next_step.execute(
                        seat, self.validation, {'indicies': self.choice_indicies, 'count': len(self.choice_indicies)}
                    )
                )
                if self.validation.remaining_arguments:
                    self.validation.success = False

            self.validation.remaining_arguments = match.group('after_step')
        return self.validation


class SpendUnique(SpendBase):
    def __init__(self, goods, count, next_step=None):
        super(SpendUnique, self).__init__()
        if isinstance(goods, Goods):
            goods = GoodsSet({goods})
        self.goods = goods
        self.count = count
        self.next_step = next_step

        self.spend_goods = None

    def task(self, seat):
        return {'spend': {
            'goods_unique': self.goods,
            'count': self.count,
            'next_step': None if not self.next_step else self.next_step.task(seat)
        }}

    def execute(self, seat, validation, parameters=None):
        super(SpendUnique, self).execute(seat, validation, parameters=parameters)
        self.spend_goods = None

        match = SpendExact.match_regex.match(validation.remaining_arguments or '')
        if not match:
            self.validation.success = False
            return self.validation
        self.spend_goods = GoodsSet()
        for goods_match in SpendUnique.goods_regex.finditer(match.group('goods')):
            amount = int(goods_match.group('amount'))
            good = goods_map[goods_match.group('good')](amount)
            if amount != 1 and good != Coin(5):
                self.validation.exception = ValueError("{0}: only individual goods are required".format(good.name))
                return self.validation
            # Each good should only be specified once
            if good in self.spend_goods:
                self.validation.exception = ValueError("{0} being spent more than once".format(good.name))
                return self.validation
            self.spend_goods.add(good)
        # We must have exactly as many unique goods tiles as required by 'self.count'
        if len(self.spend_goods) != self.count:
            self.validation.exception = ValueError(
                "incorrect number of goods: expected {0}, got {1}".format(self.count, len(self.spend_goods))
            )
            self.validation.success = False
            return self.validation
        # Verify that all the goods specified are allowed
        for good in self.spend_goods:
            if not {g for g in self.goods if g == good}:
                self.validation.exception = ValueError("{0} not allowed to be spent".format(good.name))
                return self.validation

        if self.spend_goods is not None:
            seat.spend(self.spend_goods)

            if self.next_step:
                self.validation.remaining_arguments = match.group('next_step')
                self.validation.update(self.next_step.execute(seat, self.validation, {'count': 1}))
                if self.validation.remaining_arguments:
                    self.validation.success = False

            self.validation.remaining_arguments = match.group('after_step')
        return self.validation


class RemoveForest(FunctionStepBase):
    match_regex = re.compile(
        r'^remove\s+forest'
        r'\s+at\s+(?P<coordinates>\b[1-9][0-9][a-i]\b(\s+\b[1-9][0-9][a-z]\b)*)'
        r'(\s+to\s+(?P<rest>.+))?'
        r'$'
    )

    def __init__(self, max_count=1, next_step=None):
        super(RemoveForest, self).__init__()
        self.max = max_count
        self.next_step = next_step

        self.spaces = None

    def task(self, seat):
        return {'remove_forest': {
            'max': self.max,
            'next_step': None if not self.next_step else self.next_step.task(seat)
        }}

    def execute(self, seat, validation, parameters=None):
        super(RemoveForest, self).execute(seat, validation, parameters=parameters)
        self.spaces = None

        match = RemoveForest.match_regex.match(validation.remaining_arguments or '')
        if not match:
            self.validation.success = False
            return self.validation

        self.spaces = set()
        for coordinate_match in RemoveForest.coordinate_regex.finditer(match.group('coordinates')):
            coordinate = (coordinate_match.group('row'), coordinate_match.group('col'))
            space = seat.find_space(coordinate)
            if space and space.card and space.card.card_type == CardType.Forest:
                self.spaces.add(space)
            else:
                self.validation.exception = ValueError("Cannot find Forest at {0}{1}".format(*coordinate))
                return self.validation

        if len(self.spaces) > self.max:
            self.validation.exception = ValueError("too many Forests specified: expected at most {0}, got {1}".format(self.max, len(self.spaces)))
            return self.validation

        if self.spaces is not None:
            for space in self.spaces:
                space.remove_card()

            self.validation.remaining_arguments = match.group('rest')
            if self.next_step:
                self.validation.update(self.next_step.execute(seat, self.validation, {'count': len(self.spaces)}))

        return self.validation


class RemoveMoor(FunctionStepBase):
    match_regex = re.compile(
        r'^remove\s+moor'
        r'\s+at\s+(?P<coordinates>\b[1-9][0-9][a-i]\b(\s+\b[1-9][0-9][a-z]\b)*)'
        r'(\s+to\s+(?P<rest>.+))?'
        r'$'
    )

    def __init__(self, max_count=1, next_step=None):
        super(RemoveMoor, self).__init__()
        self.max = max_count
        self.next_step = next_step

        self.spaces = None

    def task(self, seat):
        return {'remove_moor': {
            'max': self.max,
            'next_step': None if not self.next_step else self.next_step.task(seat)
        }}

    def execute(self, seat, validation, parameters=None):
        super(RemoveMoor, self).execute(seat, validation, parameters=parameters)
        self.spaces = None

        match = RemoveMoor.match_regex.match(validation.remaining_arguments or '')
        if not match:
            self.validation.success = False
            return self.validation

        self.spaces = set()
        for coordinate_match in RemoveMoor.coordinate_regex.finditer(match.group('coordinates')):
            coordinate = (coordinate_match.group('row'), coordinate_match.group('col'))
            space = seat.find_space(coordinate)
            if space and space.card and space.card.card_type == CardType.Moor:
                self.spaces.add(space)
            else:
                self.validation.exception = ValueError("Cannot find Moor at {0}{1}".format(*coordinate))
                return self.validation

        if len(self.spaces) > self.max:
            self.validation.exception = ValueError("too many Moors specified: expected at most {0}, got {1}".format(self.max, len(self.spaces)))
            return self.validation

        if self.spaces is not None:
            for space in self.spaces:
                space.remove_card()

            self.validation.remaining_arguments = match.group('rest')
            if self.next_step:
                self.validation.update(self.next_step.execute(seat, self.validation, {'count': len(self.spaces)}))

        return self.validation


class GainExact(GainBase):
    def __init__(self, goods=None, goods_lookup=None, goods_pool=None, count=None, per_lookup=None, next_step=None):
        super(GainExact, self).__init__()
        if isinstance(goods, Goods):
            goods = GoodsSet({goods})
        self.goods = goods
        self.goods_lookup = goods_lookup
        if isinstance(goods_pool, Goods):
            goods_pool = GoodsSet({goods_pool})
        self.goods_pool = goods_pool
        self.count = count
        self.per_lookup = per_lookup
        self.next_step = next_step

        self.parameters = {}

    def task(self, seat):
        return {'gain': {
            'goods': self.goods_lookup(seat) if self.goods_lookup else self.goods,
            'goods_pool': self.goods_pool,
            'count': self.count,
            'per': self.per_lookup(seat) if self.per_lookup else None,
            'next_step': None if not self.next_step else self.next_step.task(seat)
        }}

    def execute(self, seat, validation, parameters=None):
        super(GainExact, self).execute(seat, validation, parameters=parameters)
        self.parameters = {}

        if parameters is None:
            parameters = {}
        self.parameters = {'goods': {}, 'gain': {}}

        if self.per_lookup:
            count = self.per_lookup(seat)
        elif isinstance(self.count, int):
            count = self.count
        else:
            count = parameters.get('count', 1)

        match = None
        declared_goods = self.goods_lookup(seat) if self.goods_lookup else self.goods

        # If count is an integer, then this is a static gain and doesn't consume any of the arguments string
        if isinstance(self.count, int):
            pass
        # Otherwise, lots of checking needs to be done
        else:
            if 'count' in parameters and not validation.remaining_arguments:
                for good in declared_goods:
                    self.parameters['goods'][good.name] = good * parameters['count']
                self.validation.remaining_arguments = None
            else:
                match = GainExact.match_regex.match(validation.remaining_arguments or '')
                if not match:
                    self.validation.success = False
                    return self.validation
                for goods_match in GainExact.goods_regex.finditer(match.group('goods')):
                    good = goods_map[goods_match.group('good')](int(goods_match.group('amount')))
                    self.parameters['goods'][good.name] = good + self.parameters['goods'].get(good.name, 0)
                self.validation.remaining_arguments = match.group('rest')

            # Now that we've obtained the list of goods, we have to verify that they make sense
            for good in declared_goods:
                if self.goods_pool:
                    for gain_name, gain_good in self.parameters['goods'].items():
                        if gain_good.name not in {g.name for g in self.goods_pool}:
                            self.validation.exception = ValueError("{0} not available to be gained; must be in {1}".format(gain_good.name, self.goods_pool))
                            return self.validation
                        self.parameters['gain'][gain_name] = gain_good + self.parameters['gain'].get(gain_name, 0)
                else:
                    if good.name not in self.parameters['goods']:
                        self.validation.exception = ValueError("attempting to gain {0} but don't know how much".format(good.name))
                        return self.validation

            if self.goods_pool and self.per_lookup:
                count = self.per_lookup(seat)
                for good in {g for g in declared_goods if g.is_temporary}:
                    value_attr = 'total_{0}_value'.format(good.name)
                    good_sum = 0
                    for gain_name, gain_good in self.parameters['gain'].items():
                        good_sum += getattr(gain_good, value_attr)
                    if good_sum > good * count:
                        self.validation.exception = ValueError("attempting to gain too many goods: can gain at most {0} {1}".format((good * count).count, good.name))
                        return self.validation
            else:
                for good_name in self.parameters['goods']:
                    if not any({g for g in declared_goods if g.name == good_name}):
                        self.validation.exception = ValueError("{0} is not in the list of gainable goods {1}".format(good_name, declared_goods))
                        return self.validation

        if self.parameters['gain']:
            seat.gain(self.parameters['gain'].values())
        else:
            seat.gain(declared_goods * count)

        if match:
            self.validation.remaining_arguments = match.group('rest')
            if self.next_step:
                self.validation.update(self.next_step.execute(seat, self.validation, {}))

        return self.validation


class GainBreaks(GainBase):
    def __init__(self, goods_breaks, next_step=None):
        super(GainBreaks, self).__init__()
        self.goods_breaks = []
        for goods in goods_breaks:
            if isinstance(goods, Goods):
                goods = GoodsSet({goods})
            self.goods_breaks.append(goods)
        self.next_step = next_step

        self.index = None

    def task(self, seat):
        return {'gain': {
            'goods_breaks': self.goods_breaks,
            'next_step': None if not self.next_step else self.next_step.task(seat)
        }}

    def execute(self, seat, validation, parameters=None):
        super(GainBreaks, self).execute(seat, validation, parameters=parameters)
        self.index = None

        if parameters is None:
            parameters = {}

        self.index = parameters.get('index', -1)

        if self.index is not None:
            if self.index >= len(self.goods_breaks) or self.index < 0:
                self.validation.exception = ValueError("invalid index specified: {0}".format(parameters.get('index')))
                return self.validation

            seat.gain(self.goods_breaks[self.index])

            if self.next_step:
                self.validation.update(self.next_step.execute(seat, validation, {'index': self.index}))

        return self.validation


class GainChoices(GainBase):
    def __init__(self, goods_choices, distinct=False, next_step=None):
        super(GainChoices, self).__init__()
        self.goods_choices = []
        for goods in goods_choices:
            if isinstance(goods, Goods):
                goods = GoodsSet({goods})
            self.goods_choices.append(goods)
        self.distinct = distinct
        self.next_step = next_step

        self.parameters = {}

    def task(self, seat):
        return {'gain': {
            'goods_choices': self.goods_choices,
            'distinct': self.distinct,
            'next_step': None if not self.next_step else self.next_step.task(seat)
        }}

    def execute(self, seat, validation, parameters=None):
        super(GainChoices, self).execute(seat, validation, parameters=parameters)
        self.parameters = {}

        if parameters is None:
            parameters = {}

        indicies = parameters.get('indicies', None)
        match = None

        # If count is an integer, then this is a static gain and doesn't consume any of the arguments string
        if isinstance(indicies, list) and all(isinstance(i, int) for i in indicies):
            self.parameters['indicies'] = indicies
        # Otherwise, lots of checking needs to be done
        else:
            match = GainChoices.match_regex.match(validation.remaining_arguments or '')
            if not match:
                self.validation.success = False
                return self.validation
            self.parameters['goods'] = {}
            for goods_match in GainChoices.goods_regex.finditer(match.group('goods')):
                good = goods_map[goods_match.group('good')](int(goods_match.group('amount')))
                self.parameters['goods'][good.name] = good + self.parameters['goods'].get(good.name, 0)

            self.parameters['goods'] = GoodsSet(self.parameters['goods'].values())

            # Now that we've obtained the list of goods, we have to verify that they make sense
            self.parameters['index'] = None
            for index in range(len(self.goods_choices)):
                if self.goods_choices[index] * parameters.get('count', 1) == self.parameters['goods']:
                    # If 'token' is present in the parameters, make sure that the token can be used to gain the index
                    if 'token' in parameters:
                        if parameters['token'] == ResourceToken.Joker or \
                                any(g for g in self.goods_choices[index] if g.name == parameters['token']):
                            self.parameters['indicies'] = [index]
                            break
                    else:
                        self.parameters['indicies'] = [index]
                        break

        if 'indicies' not in self.parameters:
            self.validation.success = False
            return self.validation

        for index in self.parameters['indicies']:
            if self.distinct and index == parameters.get('index', None):
                raise ValueError("choices must be distinct")

            seat.gain(self.goods_choices[index] * parameters.get('count', 1))

            self.validation.remaining_arguments = match.group('rest') if match else None
            if self.next_step:
                self.validation.update(self.next_step.execute(seat, self.validation, {'index': index}))

        return self.validation


class BuildSettlement(FunctionStepBase):
    match_regex = re.compile(
        r'^build\s+(?P<settlement_id>s[0-9]{2})'
        r'\s+at\s+\b(?P<row>[1-9][0-9])(?P<col>[a-i])\b'
        r'\s+with\s+(?P<goods>(\b(0|[1-9][0-9]*)\s+[-a-z]+\b)(\s+\b(0|[1-9][0-9]*)\s+[-a-z]+\b)*)'
        r'(\s+(?P<rest>.+))?$'
    )

    def __init__(self, next_step=None):
        super(BuildSettlement, self).__init__()
        self.next_step = next_step

        self.settlement = None
        self.space = None
        self.spend_goods = None

    def task(self, seat):
        return {'build_settlement': {
            'next_step': None if not self.next_step else self.next_step.task(seat)
        }}

    def execute(self, seat, validation, parameters=None):
        super(BuildSettlement, self).execute(seat, validation, parameters=parameters)
        self.settlement = None
        self.space = None
        self.spend_goods = None

        match = BuildSettlement.match_regex.match(validation.remaining_arguments or '')
        if not match:
            self.validation.success = False
            return self.validation

        matching_settlements = {s for s in seat.settlements if match.group('settlement_id') in (s.id, s.name.lower())}
        if not matching_settlements:
            self.validation.exception = ValueError("no settlement found matching {0}".format(match.group('settlement_id')))
            return self.validation
        self.settlement = matching_settlements.pop()

        row, column = match.group('row'), match.group('col')
        self.space = seat.find_space((row, column))
        if not self.space or self.space.card:
            self.validation.exception = ValueError("invalid location for settlement: {0}{1}".format(row, column))
            return self.validation

        goods = {}
        for goods_match in BuildSettlement.goods_regex.finditer(match.group('goods')):
            good = goods_map[goods_match.group('good')](int(goods_match.group('amount')))
            goods[good.name] = good + goods.get(good.name, 0)
        self.spend_goods = GoodsSet()
        for good in goods.values():
            self.spend_goods.add(good)

        goods_required = self.settlement.cost.copy()
        for good in goods_required:
            if good.is_temporary:
                value_attr = 'total_{0}_value'.format(good.name)
                for spend_good in self.spend_goods:
                    good -= min(good.count, getattr(spend_good, value_attr))

            if good.count > 0:
                cost = {c for c in self.settlement.cost if c.name == good.name}.pop()
                self.validation.exception = ValueError("not enough goods spent for {0}: {1} payed, {2} needed".format(good.name, (cost - good).count, cost.count))
                return self.validation

        seat.build_settlement(self.space, self.settlement, self.spend_goods)

        self.validation.remaining_arguments = match.group('rest')
        if self.next_step:
            self.validation.update(self.next_step.execute(seat, self.validation, {}))

        return self.validation


class BuildBuilding(FunctionStepBase):
    match_regex = re.compile(
        r'^build\s+(?P<building_id>[gfi][a-z0-9][0-9])'
        r'\s+at\s+\b(?P<row>[1-9][0-9])(?P<col>[a-i])\b'
        r'((?P<use_prior>\s+and\s+place\s+prior)'
        r'(\s+to\s+(?P<rest>.+))?)?$'
    )

    def __init__(self, return_prior=False, next_step=None):
        super(BuildBuilding, self).__init__()
        self.return_prior = return_prior
        self.next_step = next_step

        self.building = None
        self.space = None
        self.use_prior = False

    def task(self, seat):
        return {'build_building': {
            'return_prior': self.return_prior,
            'next_step': None if not self.next_step else self.next_step.task(seat)
        }}

    def execute(self, seat, validation, parameters=None):
        super(BuildBuilding, self).execute(seat, validation, parameters=parameters)
        self.building = None
        self.space = None
        self.use_prior = False

        match = BuildBuilding.match_regex.match(validation.remaining_arguments or '')
        if not match:
            self.validation.success = False
            return self.validation

        if self.return_prior:
            seat.return_clergy('prior')

        matching_buildings = {b for b in seat.game.available_buildings if match.group('building_id') in (b.id, b.name.lower())}
        if not matching_buildings:
            self.validation.exception = BuildingNotFound("no building found matching {0}".format(match.group('building_id')))
            return self.validation
        self.building = matching_buildings.pop()

        row, column = match.group('row'), match.group('col')
        self.space = seat.find_space((row, column))
        if not self.space:
            self.validation.exception = SpaceNotFound("invalid location for building: {0}{1}".format(row, column))
            return self.validation
        if self.space.card and not self.space.card.can_be_overbuilt:
            self.validation.exception = BuildingPresent("building present at location: {0}{1}".format(row, column))
            return self.validation
        if self.space.landscape_plot not in self.building.landscapes and \
                self.space.card not in self.building.landscapes:
            self.validation.exception = InvalidLandscapePlot(self.space, self.building.landscapes)
            return self.validation
        if self.building.is_cloister:
            numeric_coordinate = (int(row), ord(column) - 97)
            adjacent_spaces = seat.find_spaces_adjacent(numeric_coordinate)
            adjacent_cloisters = [s for s in adjacent_spaces
                                  if s.card and s.card.card_type == CardType.Building and s.card.is_cloister
                                  ]
            if not adjacent_cloisters:
                self.validation.exception = InvalidLandscapePlot(self.space, "Cloister")
                return self.validation

        for cost in self.building.cost:
            if seat.goods[cost.name] < cost:
                self.validation.exception = NotEnoughGoods(self.building.cost)
                return self.validation

        self.validation.remaining_arguments = match.group('rest')
        if match.group('use_prior'):
            self.use_prior = True

        seat.build_building(self.space, self.building)
        # Use the building if the Prior is being placed in it
        if self.use_prior:
            # Remove the prior from the clergy pool
            prior = [p for p in seat.clergy_pool if p.name == 'prior'][0]
            seat.clergy_pool.remove(prior)
            # Assign it to the building
            self.building.assign_clergy(seat, prior)
            # Use the building
            self.validation.update(self.building.use(seat, self.validation.remaining_arguments))

        if self.next_step:
            self.validation.update(self.next_step.execute(seat, self.validation, {}))

        return self.validation


class SwapTokens(FunctionStepBase):
    match_regex = re.compile(
        r'^swap\s+(?P<token0>[a-z]+)\s+(?P<token1>[a-z]+)(\s+and\s+(?P<rest>.+))?$'
    )

    def __init__(self, next_step=None):
        super(SwapTokens, self).__init__()
        self.next_step = next_step

        self.resource_tokens = [None, None]

    def task(self, seat):
        return {'swap_tokens': {
            'next_step': None if not self.next_step else self.next_step.task(seat)
        }}

    def execute(self, seat, validation, parameters=None):
        super(SwapTokens, self).execute(seat, validation, parameters=parameters)
        self.resource_tokens = [None, None]

        match = SwapTokens.match_regex.match(validation.remaining_arguments or '')
        if not match:
            self.validation.success = False
            return self.validation

        for i in range(2):
            self.resource_tokens[i] = match.group('token{0}'.format(i))
            if self.resource_tokens[i] not in ResourceToken.Resources or \
                    self.resource_tokens[i] not in seat.game.gameboard:
                self.validation.exception = ValueError("resource token {0} not valid".format(self.resource_tokens[i]))
                return self.validation

        # Swap the two specified tokens
        temp = seat.game.gameboard[self.resource_tokens[0]]
        seat.game.gameboard[self.resource_tokens[0]] = seat.game.gameboard[self.resource_tokens[1]]
        seat.game.gameboard[self.resource_tokens[1]] = temp

        self.validation.remaining_arguments = match.group('rest')
        if self.next_step:
            self.validation.update(self.next_step.execute(seat, self.validation, {}))

        return self.validation


class StripEnvironment(FunctionStepBase):
    match_regex = re.compile(
        r'^(?P<name>\S+)'
        r'(\s+at\s+(?P<row>\b[1-9][0-9])(?P<col>[a-i]\b)'
        r'\s+to\s+choose\s+(?P<token>\w+))?'
        r'$'
    )

    def __init__(self, name, card_type, resource_token, gain_good):
        super(StripEnvironment, self).__init__()
        self.name = name
        self.card_type = card_type
        self.resource_token = resource_token
        self.next_step = GainExact(goods=GoodsSet({gain_good(1)}))

        self.space = None
        self.chosen_resource_token = None

    def task(self, seat):
        return {self.name: {
            'space': self.space,
            'resource_token': self.chosen_resource_token
        }}

    def execute(self, seat, validation, parameters=None):
        super(StripEnvironment, self).execute(seat, validation, parameters=parameters)
        self.space = None
        self.chosen_resource_token = None

        match = StripEnvironment.match_regex.match(validation.remaining_arguments or '')
        if not match or match.group('name') != self.name:
            self.validation.success = False
            return self.validation

        coordinate = (match.group('row'), match.group('col'))
        if coordinate[0] is not None and coordinate[1] is not None:
            self.space = seat.find_space(coordinate)
            if not self.space or not self.space.card or self.space.card.card_type != self.card_type:
                self.validation.exception = ValueError("Cannot find {0} at {1}{2}".format(
                    self.card_type, coordinate[0], coordinate[1]
                ))
                return self.validation

        if match.group('token') not in {self.resource_token, ResourceToken.Joker, None}:
            self.validation.success = False
            return self.validation
        self.chosen_resource_token = match.group('token')

        if self.space is not None and self.chosen_resource_token is not None:
            self.space.remove_card()

            count = seat.game.produce(self.chosen_resource_token)
            self.validation.remaining_arguments = None
            if self.next_step:
                self.validation.update(self.next_step.execute(seat, self.validation, {'count': count}))

        return self.validation


class FellTrees(StripEnvironment):
    def __init__(self):
        super(FellTrees, self).__init__('fell-trees', CardType.Forest, ResourceToken.Wood, Wood)


class CutPeat(StripEnvironment):
    def __init__(self):
        super(CutPeat, self).__init__('cut-peat', CardType.Moor, ResourceToken.Peat, Peat)


class PlaceLandscape(FunctionStepBase):
    match_regex = re.compile(
        r'^place\s+(?P<landscape_id>(district|plot)\d+)'
        r'\s+as\s+\b(?P<side>\S+)\b'
        r'\s+at\s+\b(?P<row>[1-9][0-9])\b'
        r'$'
    )

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

    def __init__(self, landscape_type):
        super(PlaceLandscape, self).__init__()
        self.landscape_type = landscape_type

        self.landscape = None
        self.side = None
        self.row = None

    def task(self, seat):
        return {'free_landscape': {
            'landscape_type': self.landscape_type,
            'landscape': self.landscape,
            'side': self.side,
            'row': self.row
        }}

    def execute(self, seat, validation, parameters=None):
        super(PlaceLandscape, self).execute(seat, validation, parameters=parameters)
        self.landscape = None
        self.side = None
        self.row = None

        match = PlaceLandscape.match_regex.match(validation.remaining_arguments or '')
        if not match:
            if seat.game.available_landscapes[self.landscape_type]:
                self.validation.success = False
                self.validation.exception = ValueError("a {0} is available and must be chosen".format(
                    self.landscape_type
                ))
            return self.validation

        matching_landscapes = [l for l in seat.game.available_landscapes[self.landscape_type] if match.group('landscape_id') == l.id]
        if not matching_landscapes:
            self.validation.exception = NoLandscapeAvailable("no {0} found matching {1}".format(
                self.landscape_type, match.group('landscape_id')
            ))
            return self.validation
        self.landscape = matching_landscapes[0]

        side = self.landscape_map.get(self.landscape_type, {}).get(match.group('side'), None)
        if side is None:
            self.validation.exception = NoLandscapeAvailable("{0} has no side {1}".format(self.landscape_type, side))
            return self.validation
        self.side = side

        # Set the side we want to use
        self.landscape.landscape_side = self.side

        self.row = int(match.group('row'))
        available_coordinates = seat.available_landscape_coordinates(self.landscape)

        if (self.row, self.landscape.column) not in available_coordinates:
            self.validation.exception = ValueError("{0} is not a legal placement for {1}".format(self.row, self.landscape_type))
            return self.validation

        self.landscape.row = self.row
        seat.landscapes.append(self.landscape)

        self.validation.remaining_arguments = None
        return self.validation
