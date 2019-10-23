# Long-Haul FCV Module

_Long-haul_ FCVs travel to distant destinations, and need refueling en-route. 
This module deals with planning of a wide-area refueling network, with HRS (hydrogen refueling stations) located along long-haul trip paths.

# Required Software
- Python
- [Gurobi Optimizer](http://www.gurobi.com/products/gurobi-optimizer)

I recommend installing the Anaconda Python distribution, which makes working with Gurobi easier. See the [Prepare Software Environment for CHIP-MDHD](../docs/prep-software-guide.md) guide for how to install Anaconda Python and Gurobi.

# Instructions for Using This Module
## Notes before you start
- It is highly recommended to use the a [command line interface](https://tutorial.djangogirls.org/en/intro_to_command_line/), or CLI, when following these instructions.
- The commands here are primarily written for the Windows operating system. Linux and macOS users can follow these steps too, but exact commands/syntax may differ.
- In Windows, I recommend using [PowerShell](https://docs.microsoft.com/en-us/powershell/scripting/getting-started/getting-started-with-windows-powershell?view=powershell-6) as CLI.

## Step-by-step instructions
### 1. Activate `CHIP-MDHD` Python Environment
From the [Prepare Software Environment for CHIP-MDHD](../docs/prep-software-guide.md) guide, you should have installed Anaconda Python distribution and created a virtual environment for `CHIP-MDHD`. 

Run the following command in your CLI to activate the `CHIP-MDHD` virtual environment.
```powershell
conda activate CHIP-MDHD
```





# TODOs
- [ ] Transfer R script contents to Python