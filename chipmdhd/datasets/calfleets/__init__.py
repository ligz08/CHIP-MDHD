import pandas as pd
import os

here = os.path.dirname(__file__)
fleets = pd.read_csv(os.path.join(here, 'fleets.csv'))
hubs = pd.read_csv(os.path.join(here, 'hubs.csv'))
VMT = pd.read_csv(os.path.join(here, 'fleet-VMT.csv'))
FCEV_new_pop = pd.read_csv(os.path.join(here, 'FCEV-new-pop.csv'))
FCEV_fuel_economy = pd.read_csv(os.path.join(here, 'FCEV-fuel-economy.csv'))
hub2hub_dist = pd.read_csv(os.path.join(here, 'hub2hub-drive-dist.csv'))