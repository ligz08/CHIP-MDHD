library(ggplot2)


New.Pop <- read.csv("in_FCET_new_pop.csv", header=T)
Fleets.List <- read.csv("in_Fleets_list.csv", header = T)

FCET.types <- as.character(unique(New.Pop$FCET_type))
Year.Range <- sort(unique(New.Pop$MY))




Fleet.VMT <- merge(data.frame(Fleet=Fleets.List$fleet.name), data.frame(CY=Year.Range), by=NULL)
# Fleet.VMT$Daily.H2VMT.per.Veh <- abs(rnorm(nrow(Fleet.VMT), mean=150, sd=5))
Fleet.VMT$Daily.H2VMT.per.Veh <- 150


write.csv(Fleet.VMT, "in_Fleet_VMT.csv", row.names = F)


# ggplot(data=Fleet.VMT, aes(x=CY, y=Daily.H2VMT.per.Veh)) +
#   geom_line() +
#   facet_wrap(~Fleet)

hist_dailyH2VMT <- qplot(Fleet.VMT$Daily.H2VMT.per.Veh) +
    geom_histogram(color = 'white') +
    labs(x='Daily hydrogen miles per vehicle', y='Count')
ggsave('plots/in_Fleet_VMT.png', width = 4, height = 2.5)

