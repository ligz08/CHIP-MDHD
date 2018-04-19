# Read the active scenario from active_scenario.txt
f <- file(file.path(local.module.dir, 'active_scenario.txt'), 'r')
active.scenario <- f %>% readLines(n=1) %>% trimws()
close(f)
remove(f)

# Set scenario dir
scenario.dir <- file.path(local.module.dir, active.scenario)
input.dir <- file.path(scenario.dir, 'input')
scratch.dir <- file.path(scenario.dir, 'scratch')
output.dir <- file.path(scenario.dir, 'output')