import abc
from ..econ import Dollar


class HydrogenRefuelingStation(object):
    def __init__(self, **params):
        pass


class CostItem(abc.ABC):
    """
    A base class for all classes that involve costs.
    Do not instantiate this class.
    """
    @abc.abstractmethod
    @property
    def init_cap_cost(self) -> Dollar:
        pass

    @abc.abstractmethod
    @property
    def op_cost_per_yr(self) -> Dollar:
        pass

    @abc.abstractmethod
    @property
    def op_cost_per_product(self) -> Dollar:
        """
        Operating cost per unit of product (e.g. kg of H2).
        """
        pass