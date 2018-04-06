####################################################################################################
## This script queries Google Maps API to find driving distances on arcs (node node pairs)
## Notices:
## - A Google Maps API key must be available at file "../credentials/GoogleMapsAPIKey"
####################################################################################################

library(tidyverse)

# Function that queries arc lengths from Google Maps API
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


# READ NODES AND ARCS
nodes <- read_excel("../input/Nodes_manual_input.xlsx", 
                    col_types = c("text", "text", "numeric", "numeric", "numeric", "text", "numeric", "text", "numeric"))
arcs <- read_excel("../input/Arcs_manual_input.xlsx",
                   col_types = c("text", "text", "text"))

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