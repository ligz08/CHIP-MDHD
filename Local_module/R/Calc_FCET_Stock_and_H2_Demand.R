grm(list=ls())

# Load packages
library(tidyverse)
library(here)

# Setup work environment
CHIP.root.dir <- here()
local.module.dir <- file.path(CHIP.root.dir, 'Local_module')
r.script.dir <- file.path(local.module.dir, 'R')
# Find paths, directories
# like local.module.dir, scenario.dir, input.dir, output.dir, scratch.dir, etc.
source(file.path(r.script.dir, 'find_paths.R'))

cat('Local module directory:', local.module.dir, '\n')
# today <- Sys.Date()
growth_constrain <- FALSE

# Read inputs
setwd(scenario.dir)
cat('Active scenario:', active.scenario, '\n')
cat('Scenario directory:', scenario.dir, '\n')
Survival.Curve <- read_csv("input/Survival_curve.csv", col_types = cols())
New.Pop <- read_csv("input/FCET_new_pop.csv", col_types = cols())
Fleets.List <- read_csv("input/Fleets_list.csv", col_types = cols())
Hubs.List <- read_csv("input/Hubs_list.csv", col_types = cols())
Fleet.VMT <- read_csv("input/Fleet_VMT.csv", col_types = cols())
Fuel.Economy <- read_csv("input/FCET_Fuel_Economy.csv", col_types = cols())
DriveDistTime_HubHub <- read_csv("scratch/DriveDistTime_HubHub.csv", col_types = cols())

# Prepare variables & data containers
FCET.types <- as.character(unique(New.Pop$FCET_type))
Year.Range <- sort(unique(New.Pop$MY))
FCET.Stock <- tibble(CY=integer(),
                         MY=integer(),
                         FCET_type=character(),
                         Population.NoLoss=numeric(),
                         Population.Survived=numeric(),
                         Fleet=character(),
                         Hub=character())
FCET.Allocation.Logbook <- tibble()



# Assign yearly new pop to fleets
for(this.year in Year.Range){
  for(truck.type in FCET.types){
    # Get quota of current truck.type for this.year from the statewide New.Pop table
    quota <- New.Pop %>% filter(MY==this.year, FCET_type==truck.type) %>% select(FCET_new_pop) %>% as.integer()
    # Create a temporary table of the fleets that are relevent, i.e. operates current truck.type. Many columns are added with placeholder values.
    fleet.candidates <- Fleets.List %>% 
      filter(FCET_type==truck.type) %>% 
      select("fleet.name","base.hub","FCET_type","Seed_year","Fleet_size_cap") %>% 
      add_column(pre.existing.fcet.pop=0) %>% 
      add_column(seed.year.score=0) %>% 
      add_column(have.fcet.score=0) %>% 
      add_column(share.fcet.hub.score=0) %>%
      add_column(near.fcet.hub.score=0) %>% 
      add_column(minutes.to.nearest.fcet.hub=Inf) %>% 
      add_column(new.fcet.wanted=0) %>% 
      add_column(new.FCET.pop=0)
    
    # Give scores to fleets that are "seed fleet" of this year
    seed.fleet.filter <- !is.na(fleet.candidates$Seed_year) & fleet.candidates$Seed_year==this.year
    fleet.candidates$seed.year.score[seed.fleet.filter] <- 10   # 10 points for seed fleets
    
    # Give scores to fleets that already had FCETs last year
    fcet.fleet.filter <- unique(match(FCET.Stock[FCET.Stock$CY==this.year-1 & FCET.Stock$FCET_type==truck.type  & FCET.Stock$Population.Survived>0,]$Fleet,
                                      fleet.candidates$fleet.name))
    if(length(fcet.fleet.filter)){
      temp <- FCET.Stock[FCET.Stock$CY==this.year-1 & FCET.Stock$FCET_type==truck.type,]
      pre.existing.fcet.by.fleet <- aggregate(Population.Survived~Fleet, data=temp, sum)
      fleet.candidates$pre.existing.fcet.pop <- pre.existing.fcet.by.fleet$Population.Survived[match(fleet.candidates$fleet.name, pre.existing.fcet.by.fleet$Fleet)]
      fleet.candidates$have.fcet.score[fcet.fleet.filter] <- 8    # 8 points for already having FCETs in fleet
    }
    fleet.candidates$new.fcet.wanted <- fleet.candidates$Fleet_size_cap - fleet.candidates$pre.existing.fcet.pop
    if(growth_constrain){
      fleet.candidates$new.fcet.wanted <- pmin(fleet.candidates$new.fcet.wanted, 100) # make sure no fleet gets more than 100 new vehicles in a year
      fleet.candidates$new.fcet.wanted <- pmin(fleet.candidates$new.fcet.wanted, pmax(50, round(0.1 * fleet.candidates$pre.existing.fcet.pop)))
      # make sure no fleet grows faster than 10%, unless 50% is fewer than 50
    }
    
    
    # Give scores to fleets located at a hub location that already had FCETs last year
    # fcet.hub.names <- unique(FCET.Stock[FCET.Stock$CY==this.year-1 & FCET.Stock$FCET_type==truck.type  & FCET.Stock$Population.Survived>0,]$Hub)
    fcet.hub.names <- FCET.Stock %>% filter(CY==this.year-1, FCET_type==truck.type, Population.Survived>0) %>% select(Hub) %>%  as_vector() %>% unique()
    if(length(fcet.hub.names)){
      fleet.candidates$share.fcet.hub.score[fleet.candidates$base.hub %in% fcet.hub.names] <- 5    # 5 points for fleets sharing a hub with other FCET fleet(s)
      # fleet.candidates$share.fcet.hub.score[fleet.candidates$have.fcet.score>0] <- 0
    }
    
    # Give score to hubs that are close to other hubs w/ FCET fleet
    if(length(fcet.hub.names)){
      dt.to.fcet.hubs <- subset(DriveDistTime_HubHub, to.hub %in% fcet.hub.names)
      dt.to.nearest.fcet.hub <- aggregate(drive.minutes~from.hub, data=dt.to.fcet.hubs, FUN=min)
      fleet.candidates$minutes.to.nearest.fcet.hub <- dt.to.nearest.fcet.hub$drive.minutes[match(fleet.candidates$base.hub, dt.to.nearest.fcet.hub$from.hub)]
      fleet.candidates$near.fcet.hub.score <- pmax(5-fleet.candidates$minutes.to.nearest.fcet.hub/4, 0)    # Linearly reduce near.fcet.hub.score as distance gets further, but no less than 0
      fleet.candidates$near.fcet.hub.score[is.na(fleet.candidates$near.fcet.hub.score)] <- 0 
    }
    
    # Take highest score from above as final score
    fleet.candidates <- fleet.candidates %>% 
      mutate(final.score = pmax(seed.year.score, have.fcet.score, share.fcet.hub.score, near.fcet.hub.score)) %>% 
      mutate(final.rank = rank(-final.score, ties.method='min'))
    
    # fleet.candidates$total.score <- fleet.candidates$seed.year.score + 
    #   fleet.candidates$have.fcet.score + 
    #   fleet.candidates$share.fcet.hub.score +
    #   fleet.candidates$near.fcet.hub.score
    # fleet.candidates$total.score.rank <- rank(-fleet.candidates$total.score, ties.method = "min")
    
    quota.left <- quota
    for(pos in sort(unique(fleet.candidates$final.rank))){
      if(quota.left<=0) break
      candidate.index <- fleet.candidates$final.rank==pos
      n.candidates <- sum(candidate.index)
      fleet.candidates$new.FCET.pop[candidate.index] <- pmin(fleet.candidates$new.fcet.wanted[candidate.index], round(quota.left/n.candidates))
      # fleet.candidates$new.FCET.pop[fleet.candidates$total.score<=0] <- 0
      quota.left <- quota - sum(fleet.candidates$new.FCET.pop)
    }
    
    new.stock <- tibble(MY=this.year,
                            FCET_type=truck.type,
                            Population.NoLoss=fleet.candidates$new.FCET.pop,
                            Fleet=fleet.candidates$fleet.name,
                            Hub=fleet.candidates$base.hub)
    
    cy=Year.Range[Year.Range>=this.year]
    
    
    # temp <- merge(data.frame(CY=cy), new.stock, by=NULL)
    temp <- tibble(CY=cy) %>% 
      merge(new.stock, by=NULL) %>% as_tibble() %>% 
      mutate(Age=CY-MY) %>% 
      left_join(Survival.Curve, by='Age') %>% 
      mutate(Population.Survived=round(Population.NoLoss * Survival))
    
    
    # temp$Age <- temp$CY - temp$MY
    # temp <- merge(temp, Survival.Curve)
    # temp$Population.Survived <- round(temp$Population.NoLoss * temp$Survival)
    
    
    FCET.Stock <- bind_rows(FCET.Stock, temp)
    FCET.Allocation.Logbook <- bind_rows(FCET.Allocation.Logbook, fleet.candidates %>% add_column(year=this.year, .before=1))
  }
}




# Complete fleet info is stored in FCET.Stock dataframe. 
# Here we generate some subsets/aggregates of it for analysis
FCET.New.Stock <- FCET.Stock %>% filter(Age==0)
FCET.Simp.Stock <- 
  aggregate(Population.Survived~CY+FCET_type+Hub, data=FCET.Stock, FUN=sum)

FCET.Simp.Stock %>% write.csv(file = file.path(output.dir, "out_FCET_Simplified_Stock.csv"), row.names = F)
FCET.Stock %>% write_csv(file.path(output.dir, 'out_FCET_Full_Stock.csv'))






# Calculate H2 damand from FCET stock, fleet VMT, and fuel economies
H2.Demand <- merge(FCET.Stock, Fleet.VMT)
H2.Demand <- merge(H2.Demand, Fuel.Economy)
H2.Demand$Daily.kgH2 <- H2.Demand$Population.Survived * H2.Demand$Daily.H2VMT.per.Veh / H2.Demand$MPkgH2

H2.Demand.Simp <- aggregate(data=H2.Demand, Daily.kgH2~CY+FCET_type+Fleet+Hub, FUN = sum)

plot.h2.demand <- ggplot(data=H2.Demand.Simp, aes(x=CY, y=Daily.kgH2, fill=FCET_type)) +
    geom_bar(stat = "identity") +
    scale_y_continuous(labels = scales::comma) +
    labs(x='Calendar Year', y='Daily Hydrogen Demand (kgH2/day)', fill='FCV Type')
ggsave("plots/out_H2_Demand_Total.png", plot.h2.demand, width = 6, height = 4)


# Aggregate H2 demand by hub location
H2.Demand.by.Location <- aggregate(data=H2.Demand.Simp, Daily.kgH2~CY+Hub, FUN = sum)
H2.Demand.by.Location <- merge(H2.Demand.by.Location, Hubs.List, by.x = "Hub", by.y = "hub.name")
H2.Demand.by.Location %>% write.csv(file = file.path(output.dir, 'out_H2_Demand_By_Hub.csv'), row.names = F)

# Aggregate H2 demand by zip code
H2.Demand.by.Zip <- aggregate(data=H2.Demand.by.Location, Daily.kgH2~CY+zip, FUN=sum)
H2.Demand.by.Zip$country <- "USA"
H2.Demand.by.Zip %>% write.csv(file = file.path(output.dir, 'out_H2_Demand_By_Zip.csv'), row.names = F)

# Create a snapshot of H2 demand for every 5 years
Snapshot.Years <- Year.Range[Year.Range %% 5 ==0]
for(y in Snapshot.Years){
    snapshot <- subset(H2.Demand.by.Location, CY==y)
    snapshot %>% write.csv(file = file.path(output.dir, 
                                            paste0("out_H2_Demand_By_Hub_", y, "_Snapshot.csv")), 
                           row.names = F)
    hist_hubDailykgH2 <- qplot(snapshot$Daily.kgH2) + 
        geom_histogram() + 
        scale_x_log10(breaks=c(100, 200, 500, 1000, 2000, 5e3, 10e3, 20e3),labels = scales::comma) +
        labs(x='Hydrogen demand at hub (kgH2/day)', y='Count of hubs', title=paste(y,'snapshot'))
    ggsave(paste0("plots/out_H2_Demand_By_Hub_Histogram_", y, "_Snapshot.png"),
           hist_hubDailykgH2, 
           width = 4, 
           height= 4,
           scale = 0.8)
}




# Save data objects into an image
save(DriveDistTime_HubHub, FCET.Allocation.Logbook, FCET.Stock, FCET.New.Stock, FCET.Simp.Stock,
     Fleet.VMT, Fleets.List, Fuel.Economy, Hubs.List, New.Pop, Survival.Curve,
     file = file.path(scratch.dir, 'LocalFCV.RData'))

