library(tidyverse)
library(ggplot2)
library(ggthemes)
library(here)
library(ggrepel)

FCET_types <- c('MD Package Delivery', 'HD Port Drayage', 'HD Transit Bus', 'HD Other Drayage')

# target_pop_2030 <- c(10e3, 15e3, 5e3, 10e3)     # total 40K
# target_pop_2030 <- c(5000, 7500, 2500, 5000)    # total 20K
# target_pop_2030 <- c(2500, 3750, 1250, 2500)    # total 10K
# target_pop_2030 <- c(1250, 1875, 625, 1250)     # total 5K
target_pop_2030 <- c(625, 937, 312, 625)     # total 2.5K

Year_Range <- seq(2018, 2030)


CHIP.root.dir <- here()
local.module.dir <- file.path(CHIP.root.dir, 'Local_module')
r.script.dir <- file.path(local.module.dir, 'R')
source(file.path(r.script.dir, 'Find-ProjectPaths.R'))



New_Pop <- expand.grid(MY=Year_Range, FCET_type=FCET_types) %>% 
    as_tibble() %>% 
    group_by(FCET_type) %>% 
    mutate(baseMY=min(MY)) %>% 
    mutate(diffMY=MY-baseMY) %>% 
    mutate(Target_Pop = target_pop_2030[match(FCET_type, FCET_types)]) %>% 
    # mutate(New_Pop = round(Target_Pop/387*1.5^diffMY)) %>%
    mutate(FCET_new_pop = round(Target_Pop * (diffMY * 130/10400 + 1/400))) %>%
    mutate(Cum_Pop = cumsum(FCET_new_pop)) %>% 
    select(MY, FCET_type, FCET_new_pop) %>% 
    write_csv(file.path(input.dir, "FCET_new_pop.csv"))



fig <- ggplot(data = New_Pop, aes(x=MY, y=FCET_new_pop, fill=FCET_type, label=FCET_new_pop)) +
    geom_bar(stat = 'identity') +
    geom_text_repel(force=0.1, direction='y', max.iter=10, position=position_stack(vjust=0.5)) +
    labs(x="Model year", y='Target new FCV population in model year', fill='FCV type') + 
    theme_hc()


ggsave(file.path(plots.dir, 'in_FCET_New_Pop.png'), plot=fig, width=8, height=5, dpi=300)











