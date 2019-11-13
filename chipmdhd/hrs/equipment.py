import abc
from . import CostItem, HydrogenRefuelingSite
from ..econ import Dollar
from .. import physics
from .. import DEFAULT_MODELING_YEAR
from . import DEFAULT_Cp_Cv_RATIO


class Equipment(CostItem):
    """
    A base class for all equipments. Avoid instantiating this class.
    """
    def __init__(self, site:HydrogenRefuelingSite=None, **params):
        self.site = site    # a pointer to a refueling station site
        self.params = {k: v for k, v in params.items()}     # a dict of all parameters relavent to this equipment
    
    def get_param(self, param_name):
        """
        First attempt to get equipment parameter, 
        if fail then attempt to get site parameter.
        """
        return self.params.get(param_name) or self.site.get_param(param_name)


class HydrogenCompressor(Equipment):
    """
    A hydrogen compressor takes in low-pressure GH2 (e.g. 20 bar), 
    and compresses it to a higher pressure (e.g. 900 bar or 500 bar).
    """
    def __init__(self, in_pressure=1, out_pressure=1, throughput=0.0, hrs=None, **params):
        super().__init__(**params)
        self.in_pressure = in_pressure      # unit: bar
        self.out_pressure = out_pressure    # unit: bar
        self.throughput = throughput        # unit: kg/min
        self.hrs = hrs
    
    def _calc(self):
        self.compressibility_factor = 1.0   # TODO
        self.theory_power_required = 0.0    # unit: kW. TODO
        cp_cv_ratio = self.hrs.params.get('cp_cv_ratio') or DEFAULT_Cp_Cv_RATIO if self.hrs else DEFAULT_Cp_Cv_RATIO
        
    
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