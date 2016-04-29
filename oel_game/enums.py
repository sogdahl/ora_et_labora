__author__ = 'Jurek'

from .exceptions import InvalidToken


class Phase(object):
    Lobby = 'Lobby'
    Setup = 'Setup'
    RoundStart = 'Round Start'
    ReturnClergy = 'Return Clergy'
    RotateProductionWheel = 'Rotate Production Wheel'
    Settlement = 'Settlement'
    Action = 'Action'
    PassStartPlayer = 'Pass Start Player'
    Endgame = 'Endgame'
    BonusRound = 'Bonus Round'
    FinalAction = 'Final Action'
    NeutralBuild = 'Neutral Build'
    Broken = 'Broken'


class Age(object):
    Basic = 'Basic'
    Start = 'Start'
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'


class Variant(object):
    All = 'All'
    France = 'France'
    Ireland = 'Ireland'

    @staticmethod
    def choices_game():
        return Variant.France, Variant.Ireland

    @staticmethod
    def choices_card():
        return Variant.All, Variant.France, Variant.Ireland


class LandscapePlot(object):
    Water = 'Water'
    Coast = 'Coast'
    Plains = 'Plains'
    Hillside = 'Hillside'
    Mountain = 'Mountain'
    ClayMound = 'ClayMound'


class CardType(object):
    Forest = 'Forest'
    Moor = 'Moor'
    Settlement = 'Settlement'
    Building = 'Building'
    Water = 'Water'


class Gameboard(object):
    FourPlayer = '4 Player'
    ThreePlayer = '3 Player'
    ShortThreeFourPlayer = '3/4 Player Short'
    OneTwoPlayer = '1/2 Player'


class ProductionWheel(object):
    Standard = 'Standard'
    TwoPlayer = '2 Player'


class LandscapeType(object):
    Heartland = 'Heartland'
    District = 'District'
    Plot = 'Plot'


class DistrictSide(object):
    MoorForestForestHillsideHillside = 'Moor/Forest/Forest/Hillside/Hillside'
    ForestPlainsPlainsPlainsHillside = 'Forest/Plains/Plains/Plains/Hillside'


class PlotSide(object):
    Coastal = 'Coastal'
    Mountain = 'Mountain'


class GoodsTile(object):
    Wood = 'wood'
    Peat = 'peat'
    Grain = 'grain'
    Livestock = 'livestock'
    Clay = 'clay'
    Coin = '1 coin'
    Grapes = 'grapes'
    Stone = 'stone'
    PeatCoal = 'peat coal'
    Meat = 'meat'
    Wine = 'wine'
    Flour = 'flour'
    Bread = 'bread'
    Whiskey = 'whiskey'
    Ceramic = 'ceramic'
    Ornament = 'ornament'
    Straw = 'straw'
    Wonder = 'wonder'
    Book = 'book'
    Reliquary = 'reliquary'
    Malt = 'malt'
    Beer = 'beer'
    Coins5 = '5 coins'


class ResourceToken(object):
    Wheel = 'wheel'  # Wheel strictly isn't a wooden token (or a resource), but we can treat it as such
    Wood = 'wood'
    Peat = 'peat'
    Grain = 'grain'
    Livestock = 'livestock'
    Clay = 'clay'
    Coin = 'coin'
    Joker = 'joker'
    Grapes = 'grapes'
    Stone = 'stone'
    House = 'house'  # House isn't a resource, but we can treat it as such here

    Resources = {Wood, Peat, Grain, Livestock, Clay, Coin, Joker, Grapes, Stone}


class BuildingPlayerCount(object):
    One = '1'
    Two = '2'
    Three = '3'
    Four = '4'
    TwoLong = '2 Long'
    ThreeShort = '3 Short'
    FourShort = '4 Short'

    Count_ThreePlus = {One, TwoLong, Three, Four, FourShort}
    Count_Four = {One, TwoLong, Four}

    _map = {1: One, 2: Two, 3: Three, 4: Four}

    @staticmethod
    def map(count, is_short=False, is_long=False):
        if is_short:
            if count == 3:
                return BuildingPlayerCount.ThreeShort
            elif count == 4:
                return BuildingPlayerCount.FourShort
        if is_long:
            if count == 2:
                return BuildingPlayerCount.TwoLong
        return BuildingPlayerCount._map[count]


class FunctionJoiner(object):
    Additionally = 'Additionally'
    AndOr = 'And/Or'
    AndThenOr = 'And Then/Or'
    And = 'And'
    AndThen = 'And Then'
    Or = 'Or'
