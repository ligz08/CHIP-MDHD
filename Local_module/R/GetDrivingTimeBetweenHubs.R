# Load Packages
library(ggmap)
library(curl)
library(jsonlite)
library(tidyverse)

# Set up working env
local.module.dir <- getwd()
active.scenario <- file.path(local.module.dir, 'active_scenario.txt') %>% read_file() %>% trimws()
scenario.dir <- file.path(local.module.dir, active.scenario)
input.dir <- file.path(scenario.dir, 'input')
scratch.dir <- file.path(scenario.dir, 'scratch')
output.dir <- file.path(scenario.dir, 'output')


# Read inputs
Hubs.List <- file.path(input.dir, 'Hubs_list.csv') %>%  read.csv(header=T, stringsAsFactors=F)

# Prepare data containers
output.file.path <- file.path(scratch.dir, "DriveDistTime_HubHub.csv")
if(file.exists(output.file.path)){
  DriveDistTime_HubHub <- read.csv(output.file.path, header = T, stringsAsFactors = F)
} else {
  DriveDistTime_HubHub <- data.frame()
}


# Define Google querying function
API_Key <- file.path(local.module.dir, 'credentials', 'GoogleMapsAPIKey.txt') %>% read_file() %>% trimws()

googleDriveDistByLatLon <- function(from.coord, to.coord){
  cat("Googling drive distance and time from [", from.coord$lat, ",", from.coord$lon, "] to [", to.coord$lat, ",", to.coord$lon,"]...")
  google.maps.query.url <- paste0(
    "https://maps.googleapis.com/maps/api/distancematrix/json?origins=",
    from.coord$lat, ",", from.coord$lon,
    "&destinations=",
    to.coord$lat, ",", to.coord$lon,
    "&key=",
    API_Key
  )
  response <- fromJSON(url(google.maps.query.url))
  status <- response$rows$elements[[1]]$status
  cat(status,"\n")
  
  if(status=="OK"){
    return(list(meters=response$rows$elements[[1]]$distance$value,
                minutes=round(response$rows$elements[[1]]$duration$value/60)))
  }else{
    return(list(meters=Inf, minutes=Inf))
  }
}


# Generate all the hub pairs
from.hubs <- Hubs.List[, c("hub.name", "lat", "lon")]
to.hubs <- Hubs.List[, c("hub.name", "lat", "lon")]
hubhub.combs <- merge.data.frame(from.hubs, to.hubs, by=NULL) # merging with by=NULL is esentially Cartesian Product
names(hubhub.combs) <- c("from.hub","from.lat", "from.lon","to.hub","to.lat", "to.lon")
# 
hubhub.combs$same.hub <- hubhub.combs$from.hub==hubhub.combs$to.hub
hubhub.combs$too.far <- (abs(hubhub.combs$from.lon-hubhub.combs$to.lon)>1) | (abs(hubhub.combs$from.lat-hubhub.combs$to.lat)>1)
hubhub.combs$already.known <- paste(hubhub.combs$from.hub, hubhub.combs$to.hub, sep = "-->") %in% paste(DriveDistTime_HubHub$from.hub, DriveDistTime_HubHub$to.hub, sep = "-->")
hubhub.combs$ask.google <- with(hubhub.combs, !same.hub & !too.far & !already.known)

hubhub.combs$drive.meters <- NA
hubhub.combs$drive.minutes <- NA

hubhub.combs[hubhub.combs$same.hub, c("drive.meters","drive.minutes")] <- NA
hubhub.combs[hubhub.combs$too.far, c("drive.meters","drive.minutes")] <- Inf

drive.time.query <- hubhub.combs[hubhub.combs$ask.google,]
query.count <- sum(drive.time.query$ask.google)
cat("Will send", query.count, "driving distance & time requests to Google.\n")

if(nrow(drive.time.query)){
  # Construct the coordinates to send to Google
  from.coord <- setNames(drive.time.query[,c("from.lat", "from.lon")], c("lat","lon"))
  from.coord <- split(from.coord, seq(nrow(from.coord)))
  to.coord <- setNames(drive.time.query[,c("to.lat", "to.lon")], c("lat","lon"))
  to.coord <- split(to.coord, seq(nrow(to.coord)))
  # Query Google
  google.result <- mapply(googleDriveDistByLatLon, 
                          from.coord=from.coord, 
                          to.coord=to.coord)
  # Interprete/clean the results from Google
  temp <- t(google.result)
  temp[sapply(temp[,"meters"], is.null),] <- list(meters=NA, minutes=NA)
  google.result.clean <- as.data.frame(apply(temp, 2, unlist))
  # Add the google results to our local data frame
  drive.time.query[,c("drive.meters","drive.minutes")] <- google.result.clean
}

# Append new findings to the data storage table
new.findings <- rbind(hubhub.combs[!hubhub.combs$already.known & !hubhub.combs$ask.google,],
                      drive.time.query)
DriveDistTime_HubHub <- rbind(DriveDistTime_HubHub, 
                              new.findings[ , c("from.hub", "to.hub", "drive.meters", "drive.minutes")])

# Save the data
DriveDistTime_HubHub %>% write.csv(file = output.file.path, row.names = F)


# Some diagnostic stuff
# a <- DriveDistTime_HubHub$drive.minutes
# max(a[a<Inf], na.rm = T)
