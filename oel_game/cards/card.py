__author__ = 'Jurek'
from abc import ABCMeta, abstractmethod, abstractproperty

from ..enums import LandscapePlot
from .function import Function


class Card(object):
    __metaclass__ = ABCMeta

    def __init__(self, owner=None):
        self._function = Function()
        self._owner = owner

    @staticmethod
    def name(self):
        pass

    @abstractproperty
    def id(self):
        pass

    @abstractproperty
    def card_type(self):
        pass

    @abstractproperty
    def age(self):
        pass

    @abstractproperty
    def landscapes(self):
        return {LandscapePlot.Coast, LandscapePlot.Plains, LandscapePlot.Hillside}

    @abstractproperty
    def cost(self):
        pass

    @abstractproperty
    def economic_value(self):
        pass

    @abstractproperty
    def dwelling_value(self):
        pass

    @abstractproperty
    def variant(self):
        pass

    @abstractproperty
    def can_be_removed(self):
        return False

    @property
    def can_be_overbuilt(self):
        return False

    @property
    def function(self):
        return self._function

    def use(self, seat, arguments):
        #print "Validating", self, arguments
        return self.function.execute(seat, arguments)

    @property
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, value):
        self._owner = value

    def reset(self):
        pass