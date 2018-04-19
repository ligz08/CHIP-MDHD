# Load packages
library(here)

# Setup work environment
CHIP.root.dir <- here()
local.module.dir <- file.path(CHIP.root.dir, 'Local_module')
r.script.dir <- file.path(local.module.dir, 'R')

# Find paths, directories
# like local.module.dir, scenario.dir, input.dir, output.dir, scratch.dir, etc.
source(file.path(r.script.dir, 'find_paths.R'))



# Plot every year's new population
plot.new.pop <- ggplot(data=New.Pop, aes(x=MY, y=FCET_new_pop, fill=FCET_type)) + 
    geom_bar(stat="identity") +
    scale_y_continuous(labels = scales::comma) +
    labs(x="Model Year", y='New FCV Population Target', fill='FCV Type')
if(!dir.exists("plots")) dir.create("plots")
ggsave("./plots/in_New_Pop.png", plot = plot.new.pop, width = 7, height = 4.5)
ggsave("./plots/in_New_Pop_by_Type.png", plot = plot.new.pop + facet_wrap(~FCET_type))



# Plot the survival curve
survival.curve.plot <- ggplot(data=Survival.Curve, aes(x=Age, y=Survival)) + 
    geom_line() + 
    scale_y_continuous(labels = scales::percent)
ggsave("plots/in_Survival_Curve.png", plot = survival.curve.plot, width = 5, height = 3)


# Plot FCET stock growth
plot.stock <- ggplot(data=FCET.Simp.Stock, aes(x=CY, y=Population.Survived, fill=FCET_type)) +
    geom_bar(stat = "identity") +
    scale_y_continuous(labels = scales::comma) +
    labs(x="Calendar Year", y='FCV Population', fill='FCV Type')
ggsave("plots/out_FCET_Stock.png", plot.stock, width = 6, height = 4)
ggsave("plots/out_FCET_Stock_by_Type.png", plot.stock+facet_wrap(~FCET_type), width = 6, height = 4)
ggsave("plots/out_FCET_Stock_by_Hub.png", plot.stock+facet_wrap(~Hub), width = 20, height = 12)


# Plot every year's new FCET population, by hub location
plot.new.stock <- ggplot(data=FCET.New.Stock, aes(x=MY, y=Population.NoLoss, fill=FCET_type))+
    geom_bar(stat = "identity") +
    scale_y_continuous(labels = scales::comma) +
    labs(x='Calendar Year', y='New Population', fill='FCV Type')
ggsave("plots/out_FCET_New_Stock.png", plot.new.stock, width = 6, height = 4)
ggsave("plots/out_FCET_New_Stock_by_Type.png", plot.new.stock+facet_wrap(~FCET_type), width = 6, height = 4)



# Plot scores each fleet get every year
plot.score <- ggplot(data=FCET.Allocation.Logbook, aes(x=this.year, y=final.score, fill=FCET_type))+
    geom_bar(stat="identity") +
    facet_wrap(~fleet.name)