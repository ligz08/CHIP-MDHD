# WORK ENV
## set working dir to script file location 
this.dir <- dirname(parent.frame(2)$ofile) # frame(3) also works.
setwd(this.dir)
## load needed libaries
library(readxl) # for reading Excel files
library(readr)  # for reading csv files
library(tidyr)  # for data frame manipulation
library(dplyr)  # for data frame manipulation
library(jsonlite) # for interpreting responses from Google Maps API
library(stringr)  # for string manipulation
library(igraph)   # for finding shortes paths in network


# LOAD DATA
# Read nodes and arcs (which are manually prepared with Excel)
nodes <- read_excel("../input/Nodes_manual_input.xlsx", 
                    col_types = c("text", "text", "numeric", "numeric", "numeric", "text", "numeric", "text"))
arcs <- read_excel("../input/Arcs_manual_input.xlsx",
                   col_types = c("text", "text", "text"))


# GOOGLE ARC LENGTHS
# Get arc lengths from Google Maps API
googleDriveDistByLatLon <- function(from.coord, to.coord){
  cat("Googling drive distance from [", from.coord, "] to [", to.coord, "]...")
  API_Key <- read_file("../credentials/GoogleMapsAPIKey")
  google.maps.query.url <- paste(
    "https://maps.googleapis.com/maps/api/distancematrix/json?origins=",
    from.coord,
    "&destinations=",
    to.coord,
    "&key=",
    API_Key,
    sep=""
  )
  response <- fromJSON(url(google.maps.query.url))
  status <- response$rows$elements[[1]]$status
  cat(status,"\n")
  
  if(status=="OK"){
    return(response$rows$elements[[1]]$distance$value)
  }else{
    cat(google.maps.query.url,'\n')
    return(NA)
  }
}
nodes.coord <- nodes %>% select(node_id, latlon_str)
arcs.coord <- arcs %>% 
  left_join(nodes.coord, by=c("from_node_id"="node_id")) %>% 
  left_join(nodes.coord, by=c("to_node_id"="node_id"), suffix=c("_from","_to")) 
arcs$drive_dist_meters <- pmin(
  mapply(googleDriveDistByLatLon, arcs.coord$latlon_str_from, arcs.coord$latlon_str_to),
  mapply(googleDriveDistByLatLon, arcs.coord$latlon_str_to, arcs.coord$latlon_str_from)
)
arcs <- arcs %>% mutate(drive_dist_km=round(drive_dist_meters/1000)) %>% 
  write_csv("../scratch/Arcs_with_lengths.csv")


# GENERATE TRIPS
# Generate trips by pairing all rank=1 nodes
od_nodes <- nodes %>% filter(rank<=1) %>% select(node_id, faf_zone)
trips <- od_nodes %>% 
  expand(orig_node_id=node_id, dest_node_id=node_id) %>% 
  filter(orig_node_id!=dest_node_id) %>% 
  mutate(trip_id = row_number()) %>% 
  left_join(od_nodes, by=c("orig_node_id"="node_id")) %>% 
  left_join(od_nodes, by=c("dest_node_id"="node_id"), suffix=c("_orig","_dest")) 
zz_pairs <- trips %>% group_by(faf_zone_orig, faf_zone_dest) %>% summarise(n_zz=n()) %>% ungroup()
# Assign tonnage to those trips. 
# *Note: Freight Analysis Framework (FAF) only gives zone-zone tons, 
#  but each zone-zone pair can have multiple node-node pairs 
#  because multiple nodes may belong to the same zone.
#  I split the tons of each zone-zone pair evenly to all the node-node pairs within that zone-zone pair
faf_tons <- read_csv("../input/FAF_CA.csv") %>%   # read csv
  gather(grep("Total KTons", names(.)), key="year", value="ktons") %>% # convert years as column names to a variable called year
  mutate_at(vars(year), funs(strtoi(str_extract(.,"\\d{4}")))) %>%  # extract the year as integers
  filter(year==2020)
trips_tons <- trips %>% 
  left_join(zz_pairs, by = c("faf_zone_orig", "faf_zone_dest")) %>% 
  left_join(faf_tons, by=c("faf_zone_orig"="DMS_ORIG", "faf_zone_dest"="DMS_DEST")) %>% 
  mutate(ktons=ktons/n_zz) %>% 
  select(trip_id, orig_node_id, dest_node_id, ktons) %>% 
  write_csv("../scratch/Trips_info.csv")



# FIND PATHS
# Find shortest path (series of arcs) for each trip. Using igraph package (which implements Dijkstra's algorithm)
## create an iGraph object from the arcs list
truck_network_graph <- graph_from_data_frame(select(arcs,-arc_id), directed = FALSE) 
## calculate shortest-path distances bewteen node pairs
node_node_dists <- distances(truck_network_graph, 
          v = nodes$node_id,
          to = nodes$node_id,
          weights = E(truck_network_graph)$drive_dist_km
          ) %>% 
  as.data.frame() %>% 
  mutate(from_node_name=row.names(.)) %>% 
  gather(nodes$node_id, key='to_node_id', value='dist_km') %>% 
  write_csv("../scratch/NodeNode_Dists.csv")
## find the paths for all the trips
trips_arcs <- tibble()
trips_nodes <- tibble()
for (t in 1:nrow(trips_tons)){ # t for 'trip'
  trip_id <- trips_tons$trip_id[t]
  cat("Finding path for trip [", trip_id, "]\n")
  orig_node_id <- trips_tons$orig_node_id[t]
  dest_node_id <- trips_tons$dest_node_id[t]
  vpath <- shortest_paths(truck_network_graph, 
                          orig_node_id, 
                          dest_node_id, 
                          weights = E(truck_network_graph)$drive_dist_meters)$vpath[[1]]
  for (a in 1:(length(vpath)-1)){ # a for 'arc'
    from_node_id <- vpath[a]$name
    to_node_id <- vpath[a+1]$name
    one_arc <- tibble(trip_id,
                        arc_seq=a,
                        arc_id=arcs$arc_id[(arcs$from_node_id==from_node_id & arcs$to_node_id==to_node_id) | 
                                           (arcs$from_node_id==to_node_id & arcs$to_node_id==from_node_id) ],
                        from_node_id,
                        to_node_id
                        )
    trips_arcs <- trips_arcs %>% bind_rows(one_arc)
  }
  one_vpath <- tibble(trip_id, node_id=vpath$name) %>% mutate(node_seq=row_number())
  trips_nodes <- trips_nodes %>% bind_rows(one_vpath)
}
trips_arcs %>% write_csv("../scratch/Trips_arcs.csv")
trips_nodes %>% write_csv("../scratch/Trips_nodes.csv")




# Codes here are just for outputing the arcs list in another format so it's easier for visualization in Tableau
arcs_endnodes <- arcs %>% select(-drive_dist_meters) %>% 
  gather(c("from_node_id", "to_node_id"), key="end_type", value="end_node_id") %>% 
  select(arc_id, end_node_id) %>%
  arrange(arc_id) %>% 
  write_csv("../scratch/Arcs_EndNodes.csv")


