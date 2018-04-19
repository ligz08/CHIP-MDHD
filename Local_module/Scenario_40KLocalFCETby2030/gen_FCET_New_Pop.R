library(tidyverse)

FCET_types <- c('MD Package Delivery', 'HD Port Drayage', 'HD Transit Bus', 'HD Other Drayage')
target_pop_2030 <- c(10e3, 15e3, 5e3, 10e3)
Year_Range <- seq(2018, 2030)

New_Pop <- expand.grid(MY=Year_Range, FCET_type=FCET_types) %>% 
    as_tibble() %>% 
    group_by(FCET_type) %>% 
    mutate(baseMY=min(MY)) %>% 
    mutate(diffMY=MY-baseMY) %>% 
    mutate(Target_Pop = target_pop_2030[match(FCET_type, FCET_types)]) %>% 
    # mutate(New_Pop = round(Target_Pop/387*1.5^diffMY)) %>%
    mutate(FCET_new_pop = round(Target_Pop*(diffMY*130/10400+1/400))) %>%
    mutate(Cum_Pop = cumsum(FCET_new_pop)) %>% 
    select(MY, FCET_type, FCET_new_pop) %>% 
    write_csv("in_FCET_new_pop.csv")



ggplot(data = New_Pop, aes(x=MY, y=FCET_new_pop, fill=FCET_type)) +
    geom_bar(stat = 'identity') +
    labs(x="Model Year", y='New FCV Population', fill='FCV Type')
