import abc
from . import CostItem
from ..econ import Dollar
from .. import DEFAULT_MODELING_YEAR


class Equipment(CostItem):
    """
    A base class for all equipments. Avoid instantiating this class.
    """
    def __init__(self, **params):
        self.upstream_equips = []   # list of upstream equipments
        self.purchase_year = params.get('purchase_year') or DEFAULT_MODELING_YEAR
        self.purchase_cost = params.get('purchase_cost') or Dollar(0, self.purchase_year)
    
    @property
    def mass_efficiency(self):
        """
        Mass of product output / mass of product input.
        Not always applicable to every equipment.
        """
        pass


class Compressor(Equipment):
    pass


class HydrogenStorage(Equipment):
    def __init__(self, volume=0, max_pressure=1, min_pressure=1, n_vessels=1, **params):
        super().__init__(**params)
        self.volume = volume                # unit: m^3
        self.max_pressure = max_pressure    # unit: bar (1e5 Pa)
        self.min_pressure = min_pressure    # unit: bar (1e5 Pa)
        self.n_vessels = n_vessels          # unit: 1


class HydrogenDispenser(Equipment):
    def __init__(self, **params):
        super().__init__(**params)
        self.inflow_kgpm = params.get('inflow_kgpm') or 0.0     # unit: kg/min
        self.outflow_kgpm = params.get('outflow_kgpm') or 0.0   # unit: kg/min


class Refigerator(Equipment):
    pass


class ElectricalControler(Equipment):
    pass


class Electrolyzer(Equipment):
    pass


class SteamMethaneReformer(Equipment):
    pass