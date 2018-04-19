library(tidyverse)
library(readxl)

New.Pop <- read_csv("in_FCET_new_pop.csv")
FCET.types <- as.character(unique(New.Pop$FCET_type))
Year.Range <- sort(unique(New.Pop$MY))

Burke.FCV.Sim <- read_excel('Burke MDHD FCV Sim Summary.xlsx') %>% 
    filter(MY==2030) %>% 
    select(FCV_type, MPkgH2)


Fuel.Economy <- expand.grid(FCET_type=FCET.types, MY=Year.Range, Age=0:30) %>% 
    left_join(Burke.FCV.Sim, by=c('FCET_type'='FCV_type')) %>% 
    mutate(MPGGE = MPkgH2/ 1.019) %>% 
    mutate(MPDGE = MPGGE * 1.155) %>% 
    mutate(MJPKM = 119.93/(MPkgH2*1.60934))


write_csv(Fuel.Economy, "in_FCET_Fuel_Economy.csv")
