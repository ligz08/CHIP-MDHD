####################
# This script is replaced by Jpyter Notebook `04 Select Optimal HRS Locations with Gurobi.ipynb`
####################

import csv
import os, sys
from collections import defaultdict
# import gurobipy as grb
from gurobipy import *

# CONFIGURATION PARAMETERS
from LH_MODULE_CONFIG import SCRATCH_FOLDER, INPUT_FOLDER, OUTPUT_FOLDER, SCENARIO_ROOT
sys.path.insert(0, SCENARIO_ROOT)
from SCENARIO_CONFIG import VEH_FULL_RANGE, VEH_START_RANGE
nodenode_dist = {}  # a dictionary describing distances between nodes {(from_node, to_node): dist_km}


# LOAD DATA & CONSTRUCT THE NETWORK
## Load distances between node pairs
with open(os.path.join(SCRATCH_FOLDER, 'NodeNode_Dists.csv'), newline='') as csvfile:
    distreader = csv.reader(csvfile)
    next(distreader, None)  # skip the header line
    for row in distreader:
        from_node_id, to_node_id, dist_km = row[0], row[1], int(row[2])
        nodenode_dist[(from_node_id, to_node_id)] = dist_km


## Load trips as sequences of node ids
trips_nodes = {}    # a dict of lists {trip_id: [(node_seq, node_id), (node_seq, node_id), ...]}. Describes which nodes are on which trips, and in what sequence
all_node_ids = set()
all_trip_ids = set()
with open(os.path.join(SCRATCH_FOLDER, 'Trips_nodes.csv'), newline='') as csvfile:
    tripreader = csv.reader(csvfile)
    next(tripreader, None)  # skip header line
    for row in tripreader:
        trip_id, node_id, node_seq = row[0], row[1], int(row[2])
        all_trip_ids.add(trip_id)
        all_node_ids.add(node_id)
        if trip_id in trips_nodes:
            trips_nodes[trip_id].append((node_seq, node_id))
        else:
            trips_nodes[trip_id] = [(node_seq, node_id)]
for trip in trips_nodes.values():   # sort every trip by node_seq
    trip.sort(key=lambda seq_node: seq_node[0])

print('Read input files... Found {} trips, involving {} nodes.'.format(len(all_trip_ids), len(all_node_ids)))


on_trip_covered_by_station = defaultdict(list)     
    # { (trip_id, dest_node_id): [refuel_node_id, refuel_node_id, ...] }
    # This dict describes on trip <trip_id>, which refueling locations can enable travel to node <dest_node_id>
    # Criteria for 'cover':
    # 1) dest_node is downstream of refuel_node, i.e. on a particular trip, the sequence index of dest_node is after refuel_node
    # 2) Distance from refuel_node to dest_node is no more than full_veh_range

for trip_id, trip_nodes in trips_nodes.items():
    n_nodes = len(trip_nodes)
    for refuel_index in range(n_nodes):
        for dest_index in range(refuel_index, n_nodes):
            if dest_index > refuel_index: # a station can only enable travels to its downstream
                refuel_node_id = trip_nodes[refuel_index][1]
                dest_node_id = trip_nodes[dest_index][1]
                if nodenode_dist[(refuel_node_id, dest_node_id)] >= VEH_FULL_RANGE:
                    break
                else:
                    on_trip_covered_by_station[(trip_id, dest_node_id)].append(refuel_node_id)




# OPTIMIZE
# Now we use Gurobi to build a BIP model and optimize it
## Create a Model
m = Model('LH_FCV_FRLM')  # FRLM = Flow Refueling Location Model

## Add variables
HRS_At = m.addVars(all_node_ids, vtype=GRB.BINARY, name='HRS_At')
    # Each node is associated with a 0-1 variable that denotes whether to place an HRS (1) or not (0)

## Add constraints
for trip_id, trip_nodes in trips_nodes.items():
    orig_node_id = trip_nodes[0][1]
    for node_index in range(1, len(trip_nodes)):
        node_id = trip_nodes[node_index][1]
        need_refuel = [f for f in on_trip_covered_by_station[trip_id, node_id] if (nodenode_dist[(orig_node_id, node_id)] >= VEH_START_RANGE)]
        # print('On trip {}, node {} need at least one station among nodes'.format(trip_id, node_id), need_refuel_at_least)
        if need_refuel:
            m.addConstr(quicksum(HRS_At[f] for f in need_refuel) >= 1)  # at least one refuel point needed to reach a node

## Set objective function
m.setObjective(quicksum(HRS_At[node_id] for node_id in all_node_ids), sense=GRB.MINIMIZE)

## Print model summary before optimizing
m.update()
grb_vars = m.getVars()
grb_cons = m.getConstrs()
print('Gurobi Model Summary:\nThere are {} variables in the model:'.format(len(grb_vars)))
print([v.VarName for v in grb_vars])
print('There are {} constraints:'.format(len(grb_cons)))
print([m.getRow(c) for c in grb_cons])

## Optimize it!
print('Optimizing...')
m.optimize()


## Show optimization results
print('We need stations at nodes:')
chosen_hrs_node_id = [node_id for node_id in all_node_ids if HRS_At[node_id].x>0 ]
print(chosen_hrs_node_id)

## Write optimization results to a CSV file
output_filename = 'Chosen_HRS_' + str(VEH_FULL_RANGE) + 'kmVehRange.csv'
# with open(output_filename, 'w', newline='') as csvfile:
#     hrswriter = csv.writer(csvfile, delimiter=',')
#     hrswriter.writerow(['hrs_node_id'])
#     for id in chosen_hrs_node_id:
#         hrswriter.writerow([id])


# Find which stations refuel which trips
on_trip_refuel_at = {}  # {trip_id: [node_id, node_id, ...]} on trip <trip_id>, refuel at nodes [node_id, node_id, ...]
trip_refuel_km = {}     # {(trip_id, refuel_at): refuel_km}  on trip <trip_id>, a vehicle refuels <refuel_km> range equivalent amount of fuel at node <refuel_at>
for trip_id, trip_nodes in trips_nodes.items():
    first_refuel = True
    print('trip_id:', trip_id)
    # print('\t{} nodes:'.format(len(trip_nodes)), trip_nodes)

    for node_seq, node_id in trip_nodes:    # visit every node on this trip
        if node_id in chosen_hrs_node_id:   # if this node has refueling, then refuel here
            if first_refuel:
                # print('\tRefuel at:', node_id, '(first refuel)')
                on_trip_refuel_at[trip_id] = [node_id]
                trip_refuel_km[(trip_id, node_id)] = VEH_FULL_RANGE - VEH_START_RANGE + nodenode_dist[trip_nodes[0][1], node_id]
                first_refuel = False
            else:
                prev_refuel_node = on_trip_refuel_at[trip_id][-1]
                # print('\tRefuel at:', node_id, 'prev refuel:', prev_refuel_node)
                on_trip_refuel_at[trip_id].append(node_id)
                trip_refuel_km[(trip_id, node_id)] = nodenode_dist[prev_refuel_node, node_id]

    if trip_id not in on_trip_refuel_at:    # if this trip does not need refuel (happens when it's shorter than VEH_START_RANGE)
        # print('\tTrip', trip_id, 'needs no refuel')
        on_trip_refuel_at[trip_id] = []

    print('\t{} refuels:'.format(len(on_trip_refuel_at[trip_id])),
          list(zip(on_trip_refuel_at[trip_id], [ trip_refuel_km[trip_id, refuel_at] for refuel_at in on_trip_refuel_at[trip_id]])))



import pandas as pd
# km = pd.DataFrame.from_dict(trip_refuel_km, orient='index')
trip_refuel = pd.Series(trip_refuel_km).rename_axis(['trip_id', 'refuel_at']).reset_index(name='fuel_km')
# trip_id = km.index.map(lambda x: int(x[0]))
# refuel_at = km.index.map(lambda x: int(x[1]))
# trip_refuel = pd.DataFrame({
#     'trip_id': trip_id,
#     'refuel_at': refuel_at,
#     'fuel_km': km.loc[:,0]
# })[['trip_id', 'refuel_at', 'fuel_km']]
trips_info = pd.read_csv(os.path.join(SCRATCH_FOLDER, 'Trips_info.csv'), usecols=['trip_id', 'ktons'], dtype={'trip_id': object})
trip_refuel_km_kton = trip_refuel.merge(trips_info, left_on='trip_id', right_on='trip_id', how='left')
trip_refuel_km_kton_kgH2 = trip_refuel_km_kton.assign(kgH2 = lambda r: r.fuel_km*0.621371*r.ktons*1000/150*135.8/120/365)
    # 0.621...: km -> miles
    # 1000: ktons -> tons
    # 150: truck fuel efficiency 150 ton-miles/gallon diesel
    # 135.8: diesel LHV 135.8 MJ/gallon
    # 120: hydrogen 120 MJ/kg
    # 365: year -> day
hrs_kgH2 = trip_refuel_km_kton_kgH2[['refuel_at', 'kgH2']].groupby('refuel_at', as_index=False).sum()
hrs_kgH2.rename(columns={'refuel_at': 'hrs_node_id'}, inplace=True)
hrs_kgH2.to_csv(os.path.join(OUTPUT_FOLDER, output_filename), index=False)