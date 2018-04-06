import csv
import os
from gurobipy import *

# CONFIGURATION PARAMETERS
from .config import *
nodenode_dist = {}  # a dictionary describing distances between nodes {(from_node, to_node): dist_km}



# LOAD DATA & CONSTRUCT THE NETWORK
with open(os.path.join(scratch_folder, 'NodeNode_Dists.csv'), newline='') as csvfile:
    distreader = csv.reader(csvfile)
    next(distreader, None)  # skip the header line
    for row in distreader:
        from_node_id = row[0]
        to_node_id = row[1]
        dist_km = int(row[2])
        # if from_node_id==to_node_id: # skip the arc from one node to itself
        #     continue
        nodenode_dist[(from_node_id, to_node_id)] = dist_km


# on_trip_can_make_it = {}    # {(on_trip_id, refuel_at_node, dest_node): True/False}
                            # describes on a specific trip, whether a vehicle can make it to dest_node when refueled at refuel_at_node
                            # which requires two criteria: 1) dest_node is no farther than the veh_full_range from refuel_at_node
                            # and 2) dest_node is after refuel_at_node in the sequence of nodes for this specific trip
trips_nodes = {}    # a dict of lists {trip_id: [node_id, node_id, ...]}. Describes which nodes are on which trips, and in what sequence
all_node_ids = set()
all_trip_ids = set()

with open(os.path.join(scratch_folder, 'Trips_nodes.csv'), newline='') as csvfile:
    tripreader = csv.reader(csvfile)
    next(tripreader, None)  # skip header line
    for row in tripreader:
        trip_id = row[0]
        node_id = row[1]
        node_seq = int(row[2])
        all_trip_ids.add(trip_id)
        all_node_ids.add(node_id)
        if trip_id in trips_nodes:
            trips_nodes[trip_id].append(node_id)
        else:
            trips_nodes[trip_id] = [node_id]

print('Read input files... Found {} trips, involving {} nodes.'.format(len(all_trip_ids), len(all_node_ids)))




on_trip_covered_by_station = {}     # { (trip_id, dest_node_id): [refuel_node_id, refuel_node_id, ...] }
                                    # This dict describes on trip <trip_id>, which refueling locations can enable travel to node <node_id>
                                    # Criteria for 'cover':
                                    # 1) dest_node is downstream of refuel_node, i.e. on a particular trip, the index of dest_node is after refuel_node
                                    # 2) Distance from refuel_node to dest_node is no more than full_veh_range

for trip_id in trips_nodes:
    trip_nodes = trips_nodes[trip_id]
    n_nodes = len(trip_nodes)
    orig_node_id = trip_nodes[0]
    for refuel_index in range(n_nodes):
        for dest_index in range(refuel_index, n_nodes):
            if dest_index > refuel_index: # a station can only enable travels to its downstream
                refuel_node_id = trip_nodes[refuel_index]
                dest_node_id = trip_nodes[dest_index]
                if nodenode_dist[(refuel_node_id, dest_node_id)] >= veh_full_range:
                    break

                if ((trip_id,refuel_node_id) in on_trip_covered_by_station):
                    on_trip_covered_by_station[(trip_id,refuel_node_id)].append(dest_node_id)
                else:
                    on_trip_covered_by_station[(trip_id,refuel_node_id)] = [dest_node_id]











# OPTIMIZE
# Now we use Gurobi to build a BIP model and optimize it
## Create a Model
m = Model('CA_Truck_FRLM')  # FRLM = Flow Refueling Location Model

## Add variables
HRS_At = m.addVars(all_node_ids, vtype=GRB.BINARY, name='HRS_At')

## Add constraints
for trip_id in trips_nodes:
    orig_node_id = trips_nodes[trip_id][0]
    for node_index in range(1, len(trips_nodes[trip_id])):
        node_id = trips_nodes[trip_id][node_index]
        need_refuel = [f for f in trips_nodes[trip_id][:-1] if \
                       (node_id in on_trip_covered_by_station[(trip_id, f)]) and \
                       (nodenode_dist[(orig_node_id, node_id)] >= veh_start_range)]
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
output_filename = 'Chosen_HRS_' + str(veh_full_range) + 'kmVehRange.csv'
# with open(output_filename, 'w', newline='') as csvfile:
#     hrswriter = csv.writer(csvfile, delimiter=',')
#     hrswriter.writerow(['hrs_node_id'])
#     for id in chosen_hrs_node_id:
#         hrswriter.writerow([id])









# Find which stations refuel which trips
on_trip_refuel_at = {}
trip_refuel_km = {}
for trip_id in trips_nodes:
    trip_nodes = trips_nodes[trip_id]
    first_refuel = True
    print('Trip:', trip_id)
    print('\t{} nodes:'.format(len(trip_nodes)), trip_nodes)

    for node in trip_nodes:
        if node in chosen_hrs_node_id:
            if first_refuel:
                # print('\tRefuel at:', node, '(first refuel)')
                on_trip_refuel_at[trip_id] = [node]
                trip_refuel_km[(trip_id, node)] = veh_full_range - veh_start_range + nodenode_dist[trip_nodes[0], node]
                first_refuel = False
            else:
                prev_refuel_node = on_trip_refuel_at[trip_id][-1]
                # print('\tRefuel at:', node, 'prev refuel:', prev_refuel_node)

                on_trip_refuel_at[trip_id].append(node)
                trip_refuel_km[(trip_id, node)] = nodenode_dist[prev_refuel_node, node]

    if trip_id not in on_trip_refuel_at:
        # print('\tTrip', trip_id, 'needs no refuel')
        on_trip_refuel_at[trip_id] = []

    # on_trip_refuel_at[trip_id] = [node for node in trip_nodes if node in chosen_hrs_node_id]


    print('\t{} refuels:'.format(len(on_trip_refuel_at[trip_id])),
          list(zip(on_trip_refuel_at[trip_id], [ trip_refuel_km[trip_id, refuel_at] for refuel_at in on_trip_refuel_at[trip_id]])))



import pandas as pd
km = pd.DataFrame.from_dict(trip_refuel_km, orient='index')
trip_id = km.index.map(lambda x: int(x[0]))
refuel_at = km.index.map(lambda x: int(x[1]))
trip_refuel = pd.DataFrame({
    'trip_id': trip_id,
    'refuel_at': refuel_at,
    'fuel_km': km.loc[:,0]
})[['trip_id', 'refuel_at', 'fuel_km']]
trips_info = pd.read_csv('Trips_info.csv', usecols=['trip_id', 'ktons'])
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
hrs_kgH2.to_csv(output_filename, index=False)