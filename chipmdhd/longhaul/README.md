# Class `LongHaulScenario` 

## Scenario control parameters

### LongHaulScenario.`params`

Type: dictionary.
All scenario control parameters are stored in this property variable.
It includes the following key-value pairs:

| key               | sample value | meaning                                                      |
| ----------------- | ------------ | ------------------------------------------------------------ |
| `VEH_FULL_RANGE`  | 240          | maximum range of a vehicle after full refuel. Unit: km.      |
| `VEH_START_RANGE` | 120          | range available in every vehicle at the start of its trip. Unit: km. |
| `LH_FCEV_KMPKGH2` | 15           | fuel efficiency of FCEVs. Unit: km/kgH2.                     |



## Scenario operations methods

### LongHaulScenario.`run()`

Run Run scenario with its current parameters. This includes constructing the roadway network graph and finding optimal refueling facility locations.
Modeling results will be stored in the "reporting variables" described below.


## Modeling results reporting variables

### LongHaulScenario.`on_path_refuel_at`

A dictionary of format `{path_id: [refuel_at_node_id, refuel_at_node_id, ...]}`. For each path and its `path_id` as key, the value is a list of node IDs that vehicles refuel on this path.

### LongHaulScenario.`path_startend_remaining_range`

A `pandas.DataFrame` that records for each path, a vehicle's remaining ranges (unit: km) at the start ane end of a path.  
This table below shows its columns and a row of sample values.

| path_id 	| path_end_remaining_range 	| path_start_remaining_range 	|
|-----------|---------------------------|-------------------------------|
| 1       	| 215.0                    	| 120.0                      	|

### LongHaulScenario.`dispensed_fuel`

A `pandas.DataFrame` that records for a vehicle on each path and at each refueling location, how much fuel is refueled (unit: kg).  
This table below shows its columns and a row of sample values.

| path_id | refuel_at | refuel_km | refuel_kg | volume  |
|---------|-----------|-----------|-----------|---------|
| 0       | 18        | 145.0     | 9.67      | 40940.5 |

### LongHaulScenario.`allveh_start_fuel`  and  LongHaulScenario.`allveh_end_fuel`

These are two numbers  reporting how much fuel (unit: kg) are onboard the vehicles (all vehicles combined) at the start and end of a simulation period (which depends on how `volume` is definded in `routes`, typically 1 day).


## Internal modeling variables/objects:

- LongHaulScenario.`_arcs`
- LongHaulScenario.`_network_graph`
- LongHaulScenario.`_routes`
- LongHaulScenario.`_paths`
- LongHaulScenario.`_paths_nodes`
- LongHaulScenario.`_grb_model`
- LongHaulScenario.`_scenario_id`
- LongHaulScenario.`_scenario_name`
- LongHaulScenario.`_hrs_at`


# Long-haul Module workflow:

1. Find (or read) paths. Use shortest paths if not otherwise specified.
2. Find optimal refueling locations with Gurobi.
3. Simulate trips & refueling, to estimate fuel demand at refueling locations.
