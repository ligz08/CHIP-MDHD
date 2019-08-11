import pandas as pd
import os

here = os.path.dirname(__file__)
nodes = pd.read_csv(os.path.join(here, 'Nodes.csv'))
arcs = pd.read_csv(os.path.join(here, 'Arcs.csv'))
routes = pd.read_csv(os.path.join(here, 'Routes.csv'))