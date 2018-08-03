# Local FCV Module

*Local* FCVs operate in a local area, 
and each travel to a fixed central location 
(e.g. a base yard or a central workplace) daily.
Package delivery trucks and port trucks are examples of local FCVs.
The convergence of their travel trajectories makes it feasible 
to provide hydrogen fuel only at or near the central locations 
to refuel entire FCV fleets.

# Required Software
- [R](https://www.r-project.org/about.html)
- [ArcGIS Desktop](http://desktop.arcgis.com/) with [Network Analyst](http://desktop.arcgis.com/en/arcmap/latest/extensions/network-analyst/what-is-network-analyst-.htm) extension
- Python 2.7 with `arcpy` (should come with ArcGIS Desktop)

# Instructions for Using This Module
## Notes before you start: 
- It is highly recommended to use the a 
  [command line interface](https://tutorial.djangogirls.org/en/intro_to_command_line/)
  when following these instructions.
- On Windows, [PowerShell](https://docs.microsoft.com/en-us/powershell/scripting/getting-started/getting-started-with-windows-powershell?view=powershell-6) is recommend.
- Every command is denoted with a `>` symbol ahead of it
  

## Step-by-step instructions:
### 1. Navigate to the `Local_module` directory.

Use the `cd` command to navigate to the `Local_module` directory.
Make sure eventually `pwd` command gives you the following output:
```powershell
> pwd

Path
----
C:\<some_parent_directory>\CHIP-MDHD\Local_module

```

### 2. Prepare your scenario directory

The scenario directory contains all the inputs, outputs, and intermediate files
related to a scenario you analyze. 
This is where you can customize your scenario inputs.

The scenario directory should be named by its scenario name,
and have the following structure
(using a sample scenario `Scenario_Template` for demonstration):

```
Scenario_Template\
├── input
│   ├── FCET_Fuel_Economy.csv
│   ├── FCET_new_pop.csv
│   ├── Fleet_VMT.csv
│   ├── Fleets_list.csv
│   ├── Hubs_list.csv
│   └── Survival_curve.csv
├── output
├── plots
└── scratch
```

You may use our `Scenario_Template` to create new scenarios.
Simply make a copy of the directory:
```powershell
> cp -r Scenario_Template New_Scenario
```
Then modify contents in the `New_Scenario` directory.


### 3. Choose active scenario by updating `active_scenario.txt`

Modify content of `active_scenario.txt` to the directory name
of the scenario you want to perform analysis on. 
For example, to set `Scenario_40KLocalFCETby2030` as active scenario, 
you can run the following command:
```powershell
> 'Scenario_40KLocalFCETby2030' | Out-File active_scenario.txt -Encoding ascii
```

### 4. Install required R packages

The model depends on several R packages like `tidyverse`, `jsonlite`, and `ggmap`.
You can install all needed R packages in one step by running the `install_packages.R` script in `CHIP-MDHD\Local_module\R\`.
```powershell
> Rscript R\install_packages.R
```

### 5. Get driving distances between fleet hubs

First you need to [obtain a Google Maps Distance Matrix API key](https://developers.google.com/maps/documentation/distance-matrix/get-api-key), and save the key string to  `CHIP-MDHD\Local_module\credentials\GoogleMapsAPIKey.txt`.
This is necessary so that you can access Google Maps' web service.

After the API key is in place, run the following command:
```powershell
> Rscript R\GetDrivingTimeBetweenHubs.R
```
This script will generate a `.csv` file at 
`<scenario_dir>\scratch\DriveDistTime_HubHub.csv`,
which contains driving distances between all pairs of hubs 
provided in `<scenario_dir>\scratch\Hubs_list.csv`.

The distances calculated here will later be used 
when deciding fleet priorities for allocating new FCV populations.

### 6. Calculate fleet stock inventory and fuel demand.
```powershell
> Rscript R\Calc-FcvStockH2Demand.R
```
This script calculates FCV stock population and their fuel demand based on the inputs you provided in the `input` directory in [Step 2](#2-Prepare-your-scenario-directory).

The outputs are placed in `<scenario_dir>\output\` directory as several CSV files.
They include:

| File name | Description |
|---|---|
|`out_FCET_Full_Stock.csv`| FCV stock information with full details, including vehicle populatin by calendar year (`CY`), model year (`MY`), vehicle type (`FCET_type`), and fleet. |
|`out_FCET_Simplified_Stock.csv`| A simplified version of FCV stock information. Model years and vehicle ages are hidden, and only shows FCV population by vehicle type and by fleet in each calendar year. This is useful if one is only interested in how many active FCVs are in operation in each year, regardless of how old those vehicles are. |
|`out_H2_Demand_By_Hub.csv`| H2 fuel demand at each fleet hub in each calendar year, in kgH2/day. |

At this point, you have obtained information about demand of H2 at each fleet.
The next steps are to find optimum locations of refueling facilities to meet such demand.


### 7. Prepare road network data.

Road network data is necessary to run ArcGIS Network Analyst, which finds optimal locations of hydrogen refueling stations for local FCVs.
This step can be skipped if it has been performed before.

We fetch road network data from Calforina Air Resources Board's (ARB's)
California Hydrogen Infrastructure Tool (CHIT) website 
([link](https://www.arb.ca.gov/msprog/zevprog/hydrogen/h2fueling.htm)). 
ARB's road network dataset is adapted from US Census Bureau's
[TIGER database](https://www.census.gov/geo/maps-data/data/tiger.html).

---
**Important Notes**: 
- From this point on, 
you need ArcGIS and ArcPy available on your computer.
- Make sure you're running the Python executable that comes with ArcGIS.
Normally it is in `C:\Python27\ArcGIS10.4\` (or similar)
- At the point of writing this, ArcGIS Desktop is only available on the Windows platform. All following commands are for PowerShell only.
---

First, make sure your default Python executable is the one that comes with ArcGIS.
To check this, run the following command:
```powershell
> Get-Command python | Select-Object Name,Path

Name       Path
----       ----
python.exe C:\Python27\ArcGIS10.4\python.exe
```
If the "Path" column shows a different path than `C:\Python27\ArcGIS*\python.exe`, that means your computer has another Python installation. 
This is OK, just remember to replace any `python` command in the following steps with the full path to the ArcGIS Python executable on you system (e.g. `C:\Python27\ArcGIS10.4\python.exe`)

Make sure again you are in the `Local_module` directory.
In Windows PowerShell, you should see the following outputs from the `pwd` command:
```powershell
> pwd

Path
----
C:\<some_parent_directory>\CHIP-MDHD\Local_module
```

Prepare road network data by running the following script. 
This script downloads CHIT 2017 data package from CARB's website, 
and extracts necessary data files.
About 11GB of data will be generated during this process.
Please be prepared with plenty of disk space and patience.
```powershell
> python .\python\Prepare_TIGER_Network_Dataset.py
```


### 8. Find minimum refueling station layout

Run `Minimize_HRS_for_Local_H2Demands.py`. Expect 10+ minutes on a run.
```powershell
> python .\python\Minimize_HRS_for_Local_H2Demands.py
```
The output shapefiles will be stored in `<scenario_directory>\output\shapefile\`

# TODOs
