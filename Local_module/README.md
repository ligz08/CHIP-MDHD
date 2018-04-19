# Local FCV Module

*Local* FCVs are FCVs that operate in a local area, 
and travel to a fixed central location 
(e.g. a base yard or a central workplace) daily.
Package delivery trucks and port trucks are examples of local FCVs.
The convergence of their travel trajectory makes it feasible 
to provide hydrogen fuel only at or near the central locations 
to refuel entire FCV fleets.

# Required Software
- R
- ArcGIS Desktop with Network Analyst extension
- Python 2.7 with `arcpy`

# Instructions for Using This Module
### Notes before you start: 
- It is highly recommended to use the a 
  [command line interface](https://tutorial.djangogirls.org/en/intro_to_command_line/)
  when following these instructions.

- The terminal commands (code lines starting with a `$`) here are primarily written for the macOS operating system.
  Windows and Linux users can follow these steps too, but exact commands may differ.
- In Windows, I recommend using the [PowerShell](https://docs.microsoft.com/en-us/powershell/scripting/getting-started/getting-started-with-windows-powershell?view=powershell-6)
  instead of the Command Prompt (`cmd`), 
  since some software tools such as `wget` are available in PowerShell but not in `cmd`.
  

### Step-by-step instructions:
1. Navigate to the `Local_module` directory.

Use the `cd` command to navigate to the `Local_module` directory.
Make sure `pwd` command gives you the following output:
```bash
$ pwd
<some_parent_directory>/CHIP-MDHD/Local_module
```

2. Prepare your scenario directory.

The scenario folder contains all the inputs, outputs, and intermediate files
related to a scenario you want to analyze. 
This is where you can customize your scenario inputs.

The scenario directory should be named by the scenario name,
and have the following structure
(using a sample scenario `Scenario_Template` for demonstration):

```
Scenario_Template/
├── input
│   ├── FCET_Fuel_Economy.csv
│   ├── FCET_new_pop.csv
│   ├── Fleet_VMT.csv
│   ├── Fleets_list.csv
│   ├── Hubs_list.csv
│   └── Survival_curve.csv
├── output
├── plots
└── scratch
```

You may use our `Scenario_Template` to create new scenarios.
Simply make a copy of the directory:
```bash
$ cp -r Scenario_Template New_Scenario
```
Then modify contents in the `New_Scenario` directory.


3. Choose active scenario by updating `active_scenario.txt`
 
Modify content of `active_scenario.txt` to the directory name
of the scenario you want to perform analysis on. 
For example, to set `Scenario_40KLocalFCETby2030` as the active scenario, 
you can run the following command:
```bash
$ echo 'Scenario_40KLocalFCETby2030' > active_scenario.txt  
```

4. Install required R packages.

The model depends on several R packages like `tidyverse`, `jsonlite`, and `ggmap`.
You can install all needed R packaged in one step by running the `install_packages.R` script in `CHIP-MDHD/Local_module/R/`.
```bash
$ Rscript R/install_packages.R
```

5. Get driving distances between fleet hubs

First you need to [obtain a Google Maps Distance Matrix API key](https://developers.google.com/maps/documentation/distance-matrix/get-api-key), and save the key string to  `CHIP-MDHD/Local_module/credentials/GoogleMapsAPIKey.txt`.
This is necessary so that you can access Google Maps' web service.

After that, run the following command:
```bash
$ Rscript R/GetDrivingTimeBetweenHubs.R
```
This script will generate a .csv file at 
`<scenario_dir>/scratch/DriveDistTime_HubHub.csv`,
which contains driving distances between all pairs of hubs 
provided in `<scenario_dir>/scratch/Hubs_list.csv`.

The distances calculated here will later be used 
when deciding fleet priorities for allocating new FCV populations.

6. Calculate fleet stock inventory and fuel demand.
```bash
$ Rscript R/Calc_FCET_Stock_and_H2_Demand.R
```

7. Prepare road network data.

Road network data is necessary for finding locations of 
local hydrogen stations.
This step can be skipped if it has be
We obtain such data from Calforina Air Resources Board's (ARB's)
California Hydrogen Infrastructure Tool (CHIT) website 
([link](https://www.arb.ca.gov/msprog/zevprog/hydrogen/h2fueling.htm)). 
ARB's road network dataset is adapted from UC Census Bureau's
[TIGER database](https://www.census.gov/geo/maps-data/data/tiger.html).

---
**Important Notes**: 
- From this point on, 
you need ArcGIS and ArcPy available on your computer.
- Make sure you're running the Python executable that comes with ArcGIS.
Normally it is in `C:\Python27\ArcGIS\`
- Because ArcGIS is only available on the Windows platform, 
commands below are written for Windows PowerShell. 
PowerShell commands are denoted with a `>` character at the line beginning. 
---

Prepare road network data by running the following script:
```powershell
> python .\python\Prepare_TIGER_Network_Dataset.py
```

This script will download CHIT 2017 data package from CARB's website, 
and extract necessary data files.

About 11GB data will be generated during the process.
Please be prepared with plenty of disk space and patience.

8. Find minimum refueling station layout

Run `Minimize_HRS_for_Local_H2Demands.py`. Expect 10+ minutes on a run.
```powershell
> python .\python\Minimize_HRS_for_Local_H2Demands.py
```
The output shapefiles will be stored in `<scenario_directory>/output/shapefile/`