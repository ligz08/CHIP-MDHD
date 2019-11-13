import pandas as pd
import os

here = os.path.dirname(__file__)
survival = pd.read_csv(os.path.join(here, 'VISION-survival-curve.csv'))