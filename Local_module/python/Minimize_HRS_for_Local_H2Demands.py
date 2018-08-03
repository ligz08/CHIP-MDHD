import os
import sys
import zipfile
import arcpy
from datetime import datetime
import pandas as pd
import json

SHAPEFILE_EXT = ['.shp', '.shx', '.dbf', '.prj', '.xml', '.sbn', '.sbx', '.cpg']

try:
    print datetime.now().time(), "- program start"
    
    # Set working env
    ## Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    module_dir = os.path.normpath(os.path.join(script_dir, '..'))
    with open(os.path.join(module_dir, 'active_scenario.txt')) as f:
        scenario = f.readline().strip()
    print 'Active scenario:', scenario
    scenario_dir = os.path.join(module_dir, scenario)
    input_dir = os.path.join(scenario_dir, 'input')
    output_dir = os.path.join(scenario_dir, 'output')
    out_shapefile_dir = os.path.join(output_dir, 'shapefile')
    with open(os.path.join(input_dir, 'control_parameters.json')) as f:
        coverageMinutesRange = json.load(f).get('coverage_minutes_range')
    
    ## ArcPy env
    arcpy.CheckOutExtension("Network")
    arcpy.env.workspace = scenario_dir
    arcpy.env.overwriteOutput = True
    if not os.path.exists(out_shapefile_dir):
        os.makedirs(out_shapefile_dir)

    # Set ranges for iterators
    cyRange = pd.read_csv(
        os.path.join(input_dir, "FCET_new_pop.csv"), usecols=["MY"]) \
        ["MY"] \
        .unique() \
        .tolist()
    cyRange.sort(reverse=False)
    print 'Calender year range: [{} - {}]'.format(cyRange[0], cyRange[-1])

    for cy in cyRange:
        print '[Year {}]'.format(cy)
        # Set input & output files
        H2_demand_csv = os.path.join(output_dir, "out_H2_Demand_By_Hub_{:4d}_Snapshot.csv".format(cy))
        Candidate_sites_csv = os.path.join(input_dir, "Hubs_list.csv")
        demand_points_layer = "H2_Demand_By_Hub"
        candidate_sites_layer = "Candidate_Sites"

        if not os.path.exists(os.path.join(scenario_dir, H2_demand_csv)): # when we don't have a snapshot for this cy, simply pass
            print '\t(pass)'
            continue

        # Import points from csv file, store in memory as layers
        # Demand points
        print "\tImport Demand Points from {} ...".format(H2_demand_csv)
        arcpy.MakeXYEventLayer_management(table = H2_demand_csv,
                                          in_x_field = "lon",
                                          in_y_field = "lat",
                                          out_layer  = demand_points_layer
                                          )
        print '\t{} pionts imported.'.format(arcpy.GetCount_management(demand_points_layer))

        # Candidate sites
        print "\tImport Candidate Sites from {}".format(Candidate_sites_csv)
        arcpy.MakeXYEventLayer_management(table = Candidate_sites_csv,
                                          in_x_field = "lon",
                                          in_y_field = "lat",
                                          out_layer = candidate_sites_layer
                                          )
        print '\t{} sites imported.'.format(arcpy.GetCount_management(candidate_sites_layer))
        print datetime.now().time(), "- Completed reading demand points and candidate sites."

        # Set network dataset
        network_dataset_path = os.path.join(module_dir, "TIGER_ND.gdb", "ITN_TIGER_2017", "ITN_TIGER_2017_ND")

        for coverageMinutes in coverageMinutesRange:
            # Create Location Allocation layer
            NA_layer_name = "Local_Min_Facilities_{}_{:02d}min_coverage".format(cy, coverageMinutes)
            print "\tCreate Location-Allocation Layer named {0} ...".format(NA_layer_name)
            NA_layer = arcpy.MakeLocationAllocationLayer_na(
                in_network_dataset = network_dataset_path,
                out_network_analysis_layer = NA_layer_name,
                impedance_attribute = "Minutes",
                loc_alloc_from_to = "DEMAND_TO_FACILITY",
                loc_alloc_problem_type = "MINIMIZE_FACILITIES",
                impedance_cutoff = coverageMinutes
            ).getOutput(0)

            #Get the names of all the sublayers within the location-allocation layer.
            subLayerNames = arcpy.na.GetNAClassNames(NA_layer)
            print datetime.now().time(), "- Completed creating Location-Allocation layer."

            # Load the candidate station locations as "Facilities" 
            # using default search tolerance and field mappings.
            candidateFieldMappings = arcpy.na.NAClassFieldMappings(NA_layer, subLayerNames["Facilities"])
            candidateFieldMappings["Name"].mappedFieldName = "hub.name"
            arcpy.na.AddLocations(
                in_network_analysis_layer = NA_layer,
                sub_layer = subLayerNames["Facilities"],
                in_table = candidate_sites_layer,
                field_mappings = candidateFieldMappings,
                search_tolerance = "",
                exclude_restricted_elements = "EXCLUDE")

            # Load the demand points using default search tolerance
            # Use Daily.kgH2 field to map to the Weight property.
            demandFieldMappings = arcpy.na.NAClassFieldMappings(NA_layer,
                                                                subLayerNames["DemandPoints"])
            demandFieldMappings["Weight"].mappedFieldName = "Daily.kgH2"
            demandFieldMappings["Name"].mappedFieldName = "Hub"
            print "\tAdd facility and demand locations to the Location-Allocatin Layer..."
            arcpy.na.AddLocations(
                in_network_analysis_layer = NA_layer,
                sub_layer = subLayerNames["DemandPoints"],
                in_table = demand_points_layer,
                field_mappings = demandFieldMappings,
                search_tolerance = "",
                exclude_restricted_elements = "EXCLUDE")
            print datetime.now().time(), "- Complete adding locations to Location-Allocation layer."


            # Solve the location-allocation layer
            print "\tNetwork Analyst is solving..."
            arcpy.Solve_na(NA_layer)
            print datetime.now().time(), "- Completed solving."

            # Save the solved "Facilities" layer, as shapefile
            facilitiesLayer = arcpy.mapping.ListLayers(NA_layer, "Facilities")[0]
            out_shapefile_path = os.path.join(out_shapefile_dir, NA_layer_name)
            print 'Saving solved Facilities layer to {}.'.format(out_shapefile_path) 
            # print 'Description:', arcpy.Describe(facilitiesLayer)
            arcpy.MakeFeatureLayer_management(in_features = facilitiesLayer,
                                              out_layer = "chosen_facilities_lyr",
                                              where_clause = "FacilityType=3")  # FacilityType=3 means selected facilities
            arcpy.CopyFeatures_management("chosen_facilities_lyr",  out_shapefile_path)

            # Zip the shapefile into a zip file
            os.chdir(out_shapefile_dir)
            files_to_zip = [f for f in os.listdir(out_shapefile_dir) if f.startswith(NA_layer_name) and os.path.splitext(f)[1] in SHAPEFILE_EXT]
            with zipfile.ZipFile(file=os.path.join(NA_layer_name+'.zip'), mode='w') as z:
                for f in files_to_zip:
                    z.write(f)



except Exception as e:
    # If an error occurred, print line number and error message
    import traceback, sys
    tb = sys.exc_info()[2]
    print "An error occurred on line %i" % tb.tb_lineno
    print str(e)