import pandas as pd
import itertools

INF = float('inf')


class FleetVehicleInventory(object):
    _required_tables = {
        'fleets': ['fleet_name', 'base_hub', 'veh_type', 'seed_year', 'fleet_size_cap'], 
        'hubs': ['hub_name', 'hub_type', 'full_address', 'lon', 'lat'],
        'new_pop': ['MY', 'veh_type', 'veh_new_pop'],
        'fleet_vmt': ['fleet_name', 'CY', 'daily_VMT_per_veh'],
        'fuel_economy': ['veh_type', 'MY', 'age', 'miles_per_kg'],
        'hub2hub_dist': ['from_hub', 'to_hub', 'drive_meters', 'drive_minutes'],
        'survival': ['age', 'survival']
    }
    
    def __init__(self, **params):
        for tablename in self._required_tables:
            setattr(self, tablename, params.get(tablename))
    
    def _validate(self, verbose=False):
        """
        Verify if all required tables exist, and expected columns are present in the respective tables.
        Returns True if all tables are good, otherwise False.
        """
        for tablename in self._required_tables:
            if verbose: print('Validating table:', tablename, '...', end=' ')
            df = getattr(self, tablename)
            if not isinstance(df, pd.DataFrame): 
                if verbose: print('Fail:', tablename, 'is not a Pandas DataFrame.')
                return False
            if not all([col in df.columns for col in self._required_tables[tablename]]): 
                if verbose: print('Fail: columns', self._required_tables[tablename], 'expected in table', tablename, 'but', list(df.columns), 'found.')
                return False   # verify every required column is found in df
            if verbose: print('OK.')
        return True
    
    def simulate(self, *, verbose=False):
        # verify that all required tables are in good form
        if not self._validate(verbose=verbose): return
        
        # prepare data containers
        self.veh_types = self.new_pop['veh_type'].unique()
        self.year_range = sorted(self.new_pop['MY'].unique())
        self.veh_stock = pd.DataFrame()
        self.veh_alloc_log = pd.DataFrame()

        # simulate year-by-year, type-by-type
        for year, veh_type in itertools.product(self.year_range, self.veh_types):
            quota = this.new_pop.query('MY==@year and veh_type==@veh_type')['veh_new_pop'].iloc[0]
            fleet_candidates = self.fleets.query('veh_type==@veh_type')[:]\
                .assign(pre_existing_veh_pop=0)\
                .assign(seed_year_score=0)\
                .assign(already_operating_score=0)\
                .assign(near_other_score=0)\
                .assign(minutes_to_nearest_operator_score=INF)\
                .assign(new_veh_wanted=0)\
                .assign(new_veh_pop=0)





class LocalScenario(object):
    def __init__(self):
        pass

    def run(self):
        pass


class LocalScenarioSet(object):
    pass