import pandas as pd
import networkx as nx
import gurobipy as grb
from itertools import count, product
from collections import defaultdict

class RoadwayNetworkGraph(object):
    def __init__(self, nodes, arcs, routes, paths=None):
        self.nodes = nodes
            # pd.DataFrame. Columns: node_id, lon, lat, name, ...
            # This table is actualy not useful since a graph can be constructed solely 
        self.arcs = arcs
        self.routes = routes
        self.paths = paths
        self.graph = None
        self.paths_nodes = None
        self.isReady = False

        if self.isDataComplete(): self.setup()

    def constructGraph(self):
        assert self.arcs is not None
        self.graph = nx.from_pandas_edgelist(
            df=self.arcs,
            source='from_node_id',
            target='to_node_id',
            edge_attr=['arc_id','drive_dist_km']
        )
    
    def constructPaths(self, force=False):
        """
        Generate paths betwen ODs using NetworkX's shortest path algorithm,
        and store it in `self._paths` as a pandas.DataFrame object.
        """
        if (self.paths is not None) and (not force): return
        assert self.routes is not None
        assert self.arcs is not None

        self.routes['path_length_km'] = \
            self.routes.apply(
                lambda row: nx.shortest_path_length(
                    self.graph,
                    source=row['orig_node_id'], 
                    target=row['dest_node_id'], 
                    weight='drive_dist_km'), 
                axis=1)
        paths_od = self.routes.loc[:, ['path_id', 'orig_node_id', 'dest_node_id']]
        paths_od['node_list'] = paths_od.apply(lambda row: nx.shortest_path(self.graph, 
                                                                            source=row['orig_node_id'], 
                                                                            target=row['dest_node_id'], 
                                                                            weight='drive_dist_km'), 
                                                axis=1)
        nodes_seq = paths_od\
            .set_index('path_id')\
            .apply(lambda row: pd.Series(row['node_list']), axis=1)\
            .stack()\
            .apply(int)\
            .to_frame(name='node_id')\
            .rename_axis(['path_id', 'node_seq'], axis='index')\
            .reset_index(level='node_seq')

        self.paths = paths_od\
            .merge(nodes_seq, left_on='path_id', right_index=True)\
            .drop('node_list', axis=1)\
            .reset_index(drop=True)
        
        self.paths_nodes = self.paths\
                .sort_values(by=['path_id', 'node_seq'])\
                [['path_id', 'node_id']]\
                .groupby('path_id')\
                ['node_id']\
                .apply(list)\
                .to_dict()

    def measurePaths(self):
        """
        For each node on each path, get its distance from path origin node.
        Store the distance in a `dist_from_orig_km` column in `self._paths` DataFrame.
        Distance unit is km.
        """
        assert self.arcs is not None
        assert self.paths is not None
        
        arcs_fwd = self.arcs.copy()
        arcs_rev = self.arcs.copy()
        arcs_rev[['from_node_id', 'to_node_id']] = arcs_rev.loc[:, ['to_node_id', 'from_node_id']]
        arcs_bothdir = pd.concat([arcs_fwd, arcs_rev]).drop_duplicates()
        self.paths['prev_node_id'] = self.paths['node_id']\
            .groupby(self.paths['path_id'])\
            .shift(1)\
            .fillna(-1)\
            .apply(int)
        self.paths['dist_from_orig_km'] = \
            self.paths.reset_index()\
            .merge(arcs_bothdir, how='left', left_on=['prev_node_id', 'node_id'], right_on=['from_node_id', 'to_node_id'])\
            .loc[:, ['path_id', 'node_id', 'prev_node_id', 'drive_dist_km']]\
            .fillna(0)\
            .groupby('path_id')\
            .cumsum()\
            ['drive_dist_km']
        self.paths = self.paths[['path_id', 'orig_node_id', 'dest_node_id', 'node_seq', 'node_id', 'dist_from_orig_km']]

    def setup(self):
        if self.isReady: return
        self.constructGraph()
        self.constructPaths()
        self.measurePaths()
        self.isReady = True
    
    def isDataComplete(self):
        return (self.arcs is not None) and (self.routes is not None)


class LongHaulScenario(object):
    _lh_scenario_counter = count(1)

    def __init__(self, name=None, roadnetwork=None, params={}):
        # internal variables (intended to be private)
        self._scenario_id = next(self._lh_scenario_counter)
        self._scenario_name = name or f'LongHaulScenario_{self._scenario_id}'
        self._roadnet = roadnetwork
        self._grb_model = None
        self._hrs_at = None
        
        # public variables
        self.params = params
        self.on_path_refuel_at = defaultdict(list)
            # {path_id: [refuel_at_node_id, refuel_at_node_id, ...]}
            # For each path_id, list all nodes it needs to refuel at
        self.path_refuel_km = {}
            # {(path_id, hrs_node_id): fuel_km}
            # On path `path_id` and at node `node_id`, how much fuel (as equivalent range) is put onto vehicle
        self.path_end_remaining_range = {}
            # {path_id: remaining_fuel_km }
            # On path `path_id`, how much fuel (as equivalent range) is left on board at end of trip
        self.path_startend_remaining_range = None
            # pd.DataFrame with columns: | path_id | path_start_remaining_range | path_end_remaining_range |
        self.allveh_start_remaining_range = None
            # float, unit: km
        self.allveh_end_remaining_range = None
            # float, unit: km
        self.dispensed_fuel = None
            # pd.DataFrame. Columns: | path_id | refuel_at | refuel_km | refuel_kg | volume |
        self.chosen_hrs_node_id = None
            # list of int.
    
    @property
    def allveh_start_fuel(self):
        assert 'LH_FCEV_KMPKGH2' in self.params
        return self.allveh_start_remaining_range / self.params.get('LH_FCEV_KMPKGH2')

    @property
    def allveh_end_fuel(self):
        assert 'LH_FCEV_KMPKGH2' in self.params
        return self.allveh_end_remaining_range / self.params.get('LH_FCEV_KMPKGH2')
    
    @property
    def dispensed_fuel_by_hrs(self):
        fuel = self.dispensed_fuel.loc[:, ['refuel_at', 'refuel_kg', 'volume']]
        fuel['dispensed_fuel_kg'] = fuel['refuel_kg'] * fuel['volume']
        fuel = fuel.rename(columns={'refuel_at':'hrs_node_id'})[['hrs_node_id', 'dispensed_fuel_kg']]
        return fuel.groupby('hrs_node_id').sum().reset_index()
    
    @property
    def allhrs_dispensed_fuel(self):
        return self.dispensed_fuel['volume'].dot(self.dispensed_fuel['refuel_kg'])

    def _hasParams(self, paramslist):
        return all(map(lambda paramname: paramname in self.params, paramslist)) 
        
    def _findOptimalRefuelingLocations(self, verbose=False):
        assert self._roadnet.arcs is not None
        assert self._roadnet.paths is not None
        assert self._roadnet.paths_nodes is not None
        assert self._hasParams(['VEH_START_RANGE', 'VEH_FULL_RANGE'])

        arcs = self._roadnet.arcs
        paths = self._roadnet.paths
        paths_nodes = self._roadnet.paths_nodes

        all_node_ids = arcs[['from_node_id', 'to_node_id']].stack().unique().tolist()
        
        on_path_node_dist_from_orig_km = paths\
                                            .set_index(['path_id', 'node_id'])\
                                            ['dist_from_orig_km']\
                                            .to_dict()
        
        self._grb_model = grb.Model(self._scenario_name)
        self._hrs_at = self._grb_model.addVars(all_node_ids, vtype=grb.GRB.BINARY, name='hrs_at')
        path_node_need_refuel_at = defaultdict(list)
        
        for path_id, path_nodes in paths_nodes.items():
            n_nodes = len(path_nodes)
            for refuel_node_idx, refuel_node_id in enumerate(path_nodes):
                for dest_node_idx in range(refuel_node_idx, n_nodes):
                    dest_node_id = path_nodes[dest_node_idx]
                    if dest_node_idx <= refuel_node_idx: continue
                    if on_path_node_dist_from_orig_km[path_id, dest_node_id] <= self.params.get('VEH_START_RANGE'): 
                        continue
                    if on_path_node_dist_from_orig_km[path_id, dest_node_id] - on_path_node_dist_from_orig_km[path_id, refuel_node_id] >= self.params.get('VEH_FULL_RANGE'): 
                        break
                    path_node_need_refuel_at[path_id, dest_node_id].append(refuel_node_id)
        
        for (path_id, dest_node_id), refuel_node_ids in path_node_need_refuel_at.items():
            self._grb_model.addConstr(
                grb.quicksum(self._hrs_at[f] for f in refuel_node_ids)>=1, 
                name=f'On path {path_id} reach node {dest_node_id}'
            )
        
        self._grb_model.setObjective(grb.quicksum(self._hrs_at[node_id] for node_id in all_node_ids), sense=grb.GRB.MINIMIZE)
        self._grb_model.optimize()
        self.chosen_hrs_node_id = [node_id for node_id in all_node_ids if self._hrs_at[node_id].x>0 ]
        return self.chosen_hrs_node_id

    def _simulateTrips(self):
        assert self._hasParams(['VEH_START_RANGE', 'VEH_FULL_RANGE', 'LH_FCEV_KMPKGH2'])
        VEH_START_RANGE = self.params.get('VEH_START_RANGE')
        VEH_FULL_RANGE = self.params.get('VEH_FULL_RANGE')
        LH_FCEV_KMPKGH2 = self.params.get('LH_FCEV_KMPKGH2')

        arcs = self._roadnet.arcs
        paths = self._roadnet.paths
        paths_nodes = self._roadnet.paths_nodes
        routes = self._roadnet.routes

        on_path_node_dist_from_orig_km = paths\
                                             .set_index(['path_id', 'node_id'])\
                                             ['dist_from_orig_km']\
                                             .to_dict()
        
        # Simulate along every path
        for path_id, path_nodes in paths_nodes.items():
            prev_node = None
            for node in path_nodes:
                remaining_range = VEH_START_RANGE if prev_node is None \
                     else remaining_range - (on_path_node_dist_from_orig_km[path_id, node] - on_path_node_dist_from_orig_km[path_id, prev_node])
                assert remaining_range>=0, f"Error: remaining_range is {remaining_range}"
                if node in self.chosen_hrs_node_id:
                    self.on_path_refuel_at[path_id].append(node)
                    self.path_refuel_km[path_id, node] = VEH_FULL_RANGE - remaining_range
                    remaining_range = VEH_FULL_RANGE
                prev_node = node
            self.path_end_remaining_range[path_id] = remaining_range
            
        self.path_startend_remaining_range = pd.Series(self.path_end_remaining_range)\
                                                .to_frame(name='path_end_remaining_range')\
                                                .rename_axis(['path_id'], axis='index')\
                                                .assign(path_start_remaining_range=VEH_START_RANGE)\
                                                .reset_index()

        routes = routes.merge(self.path_startend_remaining_range, how='left', on='path_id')
        self.allveh_start_remaining_range = routes['volume'].dot(routes['path_start_remaining_range'])
        self.allveh_end_remaining_range = routes['volume'].dot(routes['path_end_remaining_range'])
        self.dispensed_fuel = pd.Series(self.path_refuel_km).to_frame(name='refuel_km').rename_axis(['path_id', 'refuel_at'], axis='index').reset_index()
        self.dispensed_fuel['refuel_kg'] = self.dispensed_fuel['refuel_km'] / LH_FCEV_KMPKGH2
        self.dispensed_fuel = self.dispensed_fuel.merge(routes[['path_id', 'volume']], how='left', on='path_id')

    def run(self):
        self._roadnet.setup()
        self._findOptimalRefuelingLocations()
        self._simulateTrips()
    
    
class LongHaulScenarioSet(object):
    _lh_scenarioset_counter = count(1)
    def __init__(self, name=None, roadnetwork=None, paramtable=None):
        self._scenarioset_id = next(self._lh_scenarioset_counter)
        self._scenarioset_name = name or f'LongHaulScenarioSet_{self._scenarioset_id}'
        self._roadnet = roadnetwork
        self._scenarios = None
        self.paramtable = paramtable
    
    @property
    def paramdicts(self):
        """
        Lis of dictionaries. Example:
        [
            {'param1': value1, 'param2': value2, 'param3': value3},
            {'param1': value4, 'param2': value5, 'param3': value6},
        ]
        """
        return self.paramtable.to_dict('records')


    def _createScenarios(self):
        self._scenarios = {tuple(paramdict.values()): LongHaulScenario(name=str(tuple(paramdict.values())), roadnetwork=self._roadnet, params=paramdict) for paramdict in self.paramdicts}
    
    def run(self):
        if not self._scenarios: self._createScenarios()
        for scenario in self._scenarios.values():
            scenario.run()
    
    @property
    def stats_by_scenario(self):
        """
        Returns a pandas.DataFrame
        | VEH_FULL_RANGE | VEH_START_RANGE | LH_FCEV_KMPKGH2 | n_hrs | all_hrs_dispensed_fuel | start_onboard_fuel | end_onboard_fuel |
        """
        stats = self.paramtable.copy()
        scenarios = [self._scenarios.get(tuple(paramdict.values())) for paramdict in self.paramdicts]
        stats['n_hrs'] = [len(scenario.chosen_hrs_node_id) for scenario in scenarios]
            # how many refueling locations needed in each scenario
        stats['all_hrs_dispensed_fuel'] = [scenario.allhrs_dispensed_fuel for scenario in scenarios]
            # how much fuel is dispensed across the whole system
        stats['start_onboard_fuel'] = [scenario.allveh_start_fuel for scenario in scenarios]
            # how much fuel is onboard (all) vehicles at the start of simulation period (typically 1 day)
        stats['end_onboard_fuel'] = [scenario.allveh_end_fuel for scenario in scenarios]
            # how much fuel is onboard (all) vehicles at the end of simulation period (typically 1 day)
        stats['enroute_consumed_fuel'] = stats['start_onboard_fuel'] + stats['all_hrs_dispensed_fuel'] - stats['end_onboard_fuel']
        return stats
    
    @property
    def stats_by_hrs(self):
        """
        Returns a pandas.DataFrame
        | VEH_FULL_RANGE | VEH_START_RANGE | LH_FCEV_KMPKGH2 | hrs_node_id | dispensed_fuel |
        """
        stats = self.paramtable.copy()
        stats['param_vals'] = stats.apply(lambda row: tuple(val for val in row), axis=1)
        dflist = []
        for paramdict in self.paramdicts:
            # paramdict e.g. {'VEH_FULL_RANGE': 240, 'VEH_START_RANGE': 120, 'LH_FCEV_KMPKGH2': 15}
            param_vals = tuple(paramdict.values())    # e.g. (240, 120, 15). Used as scenario identifier.
            df = self._scenarios.get(param_vals).dispensed_fuel_by_hrs
            dflist.append(df.assign(param_vals=[param_vals]*len(df.index)))
        return stats.merge(pd.concat(dflist), how='left', on='param_vals')


