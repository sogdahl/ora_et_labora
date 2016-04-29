__author__ = 'Jurek'
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Game, Seat, GameLog
from .cards.card import Card
from .cards.building import Building
from .commands import Command
from .goods import Goods, GoodsSet
from .landscapes import Landscape, LandscapeColumn
from .objects import Gameboard, LedgerEntry


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name')


class GoodsSerializer(serializers.BaseSerializer):
    abbreviation_map = {
        'wood': 'w',
        'clay': 'c',
        'stone': 't',
        'straw': 's',
        'coin': '$',
        'energy': 'e',
        'food': 'f'
    }

    def __init__(self, *args, **kwargs):
        super(GoodsSerializer, self).__init__(*args, read_only=True, **kwargs)

    def to_representation(self, obj):
        return {
            'name': obj.name,
            'count': obj.count,
            #'is_temporary': obj.is_temporary,
            #'energy_value': obj.energy_value,
            #'food_value': obj.food_value,
            #'money_value': obj.money_value,
            #'points_value': obj.points_value,
            'abbreviation': GoodsSerializer.abbreviation_map.get(obj.name, obj.name[0])
        }


class GoodsSetSerializer(serializers.ListSerializer):
    def __init__(self, *args, **kwargs):
        super(GoodsSetSerializer, self).__init__(*args, child=GoodsSerializer(), **kwargs)

    class Meta:
        model = GoodsSet


class CardSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    id = serializers.CharField(read_only=True)
    card_type = serializers.CharField(read_only=True)
    age = serializers.CharField(read_only=True)
    landscapes = serializers.ListField(read_only=True)
    cost = GoodsSetSerializer(read_only=True)
    economic_value = serializers.IntegerField(read_only=True)
    dwelling_value = serializers.IntegerField(read_only=True)
    variant = serializers.CharField(read_only=True)
    can_be_removed = serializers.BooleanField(read_only=True)
    can_be_overbuilt = serializers.BooleanField(read_only=True)

    class Meta:
        model = Card


class BuildingSerializer(CardSerializer):
    is_cloister = serializers.BooleanField(read_only=True)
    #assigned_clergy = serializers.ListSerializer(read_only=True)

    class Meta:
        model = Building


class LandscapeSpaceSerializer(serializers.Serializer):
    landscape_plot = serializers.CharField(read_only=True)
    all_cards = CardSerializer(many=True, read_only=True)


class LandscapeColumnSerializer(serializers.ListSerializer):
    offset = serializers.IntegerField(read_only=True)

    def __init__(self, *args, **kwargs):
        super(LandscapeColumnSerializer, self).__init__(*args, child=LandscapeSpaceSerializer(read_only=True), **kwargs)

    class Meta:
        model = LandscapeColumn


class LandscapeSerializer(serializers.Serializer):
    landscape_type = serializers.CharField(read_only=True)
    horizontal_size = serializers.IntegerField(read_only=True)
    vertical_size = serializers.IntegerField(read_only=True)
    row = serializers.IntegerField(read_only=True)
    column = serializers.IntegerField(read_only=True)
    landscape_spaces = LandscapeColumnSerializer(read_only=True, many=True)

    class Meta:
        model = Landscape


class LandscapeGridSerializer(serializers.BaseSerializer):
    def __init__(self, *args, **kwargs):
        super(LandscapeGridSerializer, self).__init__(*args, read_only=True, **kwargs)

    def to_representation(self, obj):
        return {
            'start': obj['start'],
            'end': obj['end'],
            'column_0': [LandscapeSerializer().to_representation(l) for l in obj['column_0']],
            'column_1': [LandscapeSerializer().to_representation(l) for l in obj['column_1']],
            'column_2': [LandscapeSerializer().to_representation(l) for l in obj['column_2']]
        }


class SeatSerializer(serializers.ModelSerializer):
    player = UserSerializer(required=False)
    goods = serializers.DictField(child=GoodsSerializer())
    score = serializers.ReadOnlyField()
    landscape_grid = LandscapeGridSerializer()

    class Meta:
        model = Seat
        fields = ('id', 'player', 'is_neutral', 'goods', 'score', 'landscape_grid')
        depth = 1


class CommandSerializer(serializers.BaseSerializer):
    def __init__(self, *args, **kwargs):
        super(CommandSerializer, self).__init__(*args, read_only=True, **kwargs)

    def to_representation(self, obj):
        return {
            'command_string': obj.command_string,
            'is_partial': obj.is_partial
        }


class GameLogSerializer(serializers.ModelSerializer):
    parsed_commands = CommandSerializer(many=True)

    class Meta:
        model = GameLog
        fields = ('id', 'executor_id', 'command', 'parsed_commands')
        depth = 1


class GameboardSerializer(serializers.Serializer):
    gameboard_type = serializers.CharField(read_only=True)
    wheel_type = serializers.CharField(read_only=True)

    class Meta:
        model = Gameboard


class LedgerEntrySerializer(serializers.Serializer):
    executor_index = serializers.IntegerField(read_only=True)
    text = serializers.CharField(read_only=True)

    class Meta:
        model = LedgerEntry


class GameSerializer(serializers.ModelSerializer):
    #owner = UserSerializer(read_only=True)
    seats = SeatSerializer(many=True, read_only=True)
    gamelogs = GameLogSerializer(many=True, read_only=True)

    variant = serializers.ReadOnlyField()
    options = serializers.ReadOnlyField()
    gameboard = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    phase = serializers.ReadOnlyField()
    message = serializers.ReadOnlyField()
    round = serializers.ReadOnlyField()
    turn = serializers.ReadOnlyField()
    last_applied_gamelog = serializers.ReadOnlyField()
    action_seat_index = serializers.ReadOnlyField()
    #round_start_seat = serializers.ReadOnlyField()
    round_grapes_enter = serializers.ReadOnlyField()
    round_stone_enters = serializers.ReadOnlyField()
    available_buildings = serializers.ListField(child=BuildingSerializer(), read_only=True)
    available_landscapes = serializers.DictField(child=serializers.ListField(child=LandscapeSerializer(), read_only=True), read_only=True)
    work_contract_price = GoodsSerializer()
    ledger = serializers.ListField(child=LedgerEntrySerializer(), read_only=True)

    class Meta:
        model = Game
        depth = 1
        read_only_fields = ('name', )
        exclude = ('owner', )