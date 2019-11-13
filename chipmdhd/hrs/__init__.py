import abc
from ..econ import Dollar


# Default HRS design parameters
DEFAULT_Cp_Cv_RATIO = 1.42



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


class HydrogenRefuelingSite(CostItem):
    def __init__(self, equipment_list=[], **params):
        self.equipment_list = equipment_list
        self.params = {k: v for k, v in params.items()}
    
    def get_param(self, param_name):
        return self.params.get(param_name)