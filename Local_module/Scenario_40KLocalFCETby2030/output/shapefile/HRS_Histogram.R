install.packages('foreign')
library(foreign)
library(tidyverse)
d <- read.dbf('Local_Min_Facilities_2030_10min_coverage.dbf')

d$DemandWeig %>% summary()

hist_Daily.kgH2 <- ggplot(data = d,
                          aes(x=DemandWeig)) +
    geom_histogram(bins=40) +
    scale_x_log10(breaks = c(100, 500, 1000, 2000, 5000, 10e3, 20e3, 50e3), labels = scales::comma) +
    theme(plot.margin = margin(0.1,0.2,0.1,0.1, unit='in')) +
    labs(x = 'Daily hydrogen demanded at station (kgH2/day, log scale)', y = 'Count of stations') + 
    theme_minimal()
ggsave('2030 Histogram of daily kgH2.png', plot = hist_Daily.kgH2, width=5, height=3)

hist_nhubs.served <- ggplot(data = d,
       aes(x=DemandCoun)) +
  geom_histogram(binwidth = 1, color='white') +
  scale_x_continuous(breaks = seq(1,15, by=2)) +
  labs(x = 'Number of fleets served by station', y = 'Count of stations') + 
    theme_minimal()
ggsave('2030 Histogram of fleets served.png', plot = hist_nhubs.served, width=5, height=3)

sum(d$DemandCoun==1)
sum(d$DemandCoun==1)/nrow(d)
d$DemandCoun %>% table()
d$DemandCoun %>% table() %>% prop.table()
