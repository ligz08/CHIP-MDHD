import abc
from . import CostItem


class Equipment(CostItem):
    """
    A base class for all equipments. Avoid instantiating this class.
    """
    def __init__(self):
        self.upstream_equips = []   # list of upstream equipments
    
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
    def __init__(self, volume=0, max_pressure=1, min_pressure=1, n_vessels=1):
        self.volume = volume                # unit: m^3
        self.max_pressure = max_pressure    # unit: bar (1e5 Pa)
        self.min_pressure = min_pressure    # unit: bar (1e5 Pa)
        self.n_vessels = n_vessels          # unit: 1


class HydrogenDispenser(Equipment):
    pass


class Refigerator(Equipment):
    pass


class ElectricalControler(Equipment):
    pass


class Electrolyzer(Equipment):
    pass


class SteamMethaneReformer(Equipment):
    pass