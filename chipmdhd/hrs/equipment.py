import abc
from . import CostItem
from ..econ import Dollar
from .. import physics
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
        return 1.0


class HydrogenCompressor(Equipment):
    """
    A hydrogen compressor takes in low-pressure GH2 (e.g. 20 bar), 
    and compresses it to a higher pressure (e.g. 900 bar or 500 bar).
    """
    def __init__(self, in_pressure=1, out_pressure=1, throughput=0.0, **params):
        super().__init__(**params)
        self.in_pressure = in_pressure      # unit: bar
        self.out_pressure = out_pressure    # unit: bar
        self.throughput = throughput        # unit: kg/min
    
    def _calc(self):
        self.compressibility_factor = 1.0   # TODO
        self.theory_power_required = 0.0    # unit: kW. TODO
    
    def init_cap_cost(self):
        return 0    # TODO



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


class Refrigerator(Equipment):
    pass


class ElectricalController(Equipment):
    pass


class Electrolyzer(Equipment):
    pass


class SteamMethaneReformer(Equipment):
    pass