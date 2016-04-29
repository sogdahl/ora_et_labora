__author__ = 'Jurek'


class OeLException(Exception):
    pass


class OeLSyntaxError(SyntaxError):
    pass


class OeLValueError(ValueError):
    pass


class UnknownOpCode(NotImplementedError):
    pass


class InvalidActor(OeLException):
    pass


class InvalidOpCode(OeLSyntaxError):
    pass


class InvalidArguments(OeLSyntaxError):
    pass


class CardAlreadyExists(OeLException):
    pass


class NoCardToRemove(OeLException):
    pass


class CardCantBeRemoved(OeLException):
    pass


class InvalidCardSpace(OeLException):
    pass


class NotEnoughGoods(OeLValueError):
    pass


class UnappliedCommandsError(OeLException):
    pass


class NoLandscapeAvailable(OeLException):
    pass


class LandscapeAlreadyPurchased(OeLException):
    pass


class BuildingNotFound(OeLException):
    pass


class BuildingPresent(OeLException):
    pass


class SpaceNotFound(OeLException):
    pass


class InvalidLandscapePlot(OeLException):
    pass


class ClergyNotAvailable(OeLException):
    pass


class ActionRequired(OeLException):
    pass


class InvalidToken(OeLException):
    pass


class InvalidGoodsConversion(OeLException):
    pass


class PaymentRequired(OeLException):
    pass


class PaymentNotNeeded(OeLException):
    pass


class InvalidPayment(OeLException):
    pass