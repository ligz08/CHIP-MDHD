import pandas as pd


class FleetVehicleInventory(object):
    required_tables = {
        'fleets': ['fleet_name', 'base_hub', 'veh_type', 'seed_year', 'fleet_size_cap'], 
        'hubs': ['hub_name', 'hub_type', 'full_address', 'lon', 'lat'],
        'new_pop': ['MY', 'veh_type', 'veh_new_pop'],
        'fleet_vmt': ['fleet_name', 'CY', 'daily_VMT_per_veh'],
        'fuel_economy': ['veh_type', 'MY', 'age', 'miles_per_kg'],
        'hub2hub_dist': ['from_hub', 'to_hub', 'drive_meters', 'drive_minutes'],
        'survival': ['age', 'survival']
    }
    
    def __init__(self, **params):
        for tablename in self.required_tables:
            setattr(self, tablename, params.get(tablename))
    
    def _validate(self, verbose=False):
        """
        Verify if all required tables exist, and expected columns are present in the respective tables.
        Returns True if all tables are good, otherwise False.
        """
        for tablename in self.required_tables:
            if verbose: print('Validating table:', tablename, '...', end=' ')
            df = getattr(self, tablename)
            if not isinstance(df, pd.DataFrame): 
                if verbose: print('Fail:', tablename, 'is not a Pandas DataFrame.')
                return False
            if not all([col in df.columns for col in self.required_tables[tablename]]): 
                if verbose: print('Fail: columns', self.required_tables[tablename], 'expected in table', tablename, 'but', list(df.columns), 'found.')
                return False   # verify every required column is found in df
            if verbose: print('OK.')
        return True
    
    def simulate(self, *, verbose=False):
        if not self._validate(verbose=verbose): return
        veh_types = self.new_pop['veh_type'].unique()
        year_range = sorted(self.new_pop['MY'].unique())




class LocalScenario(object):
    def __init__(self):
        pass

    def run(self):
        pass


class LocalScenarioSet(object):
    pass