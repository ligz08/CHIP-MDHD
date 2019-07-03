import os

# Long-Haul Module directories
SCRIPTS_FOLDER = os.path.dirname(os.path.realpath(__file__))    # CHIP-MDHD\LongHaul_module\scripts
LH_MODULE_ROOT = os.path.abspath(os.path.join(SCRIPTS_FOLDER, os.path.pardir))  # CHIP-MDHD\LongHaul_module
with open(os.path.join(LH_MODULE_ROOT, 'active-scenario.txt'), 'r') as f: 
    ACTIVE_SCENARIO = f.readline().strip()
    print('Active scenario:', ACTIVE_SCENARIO)
SCENARIO_ROOT = os.path.join(LH_MODULE_ROOT, '_'.join(['Scenario', ACTIVE_SCENARIO]))
INPUT_FOLDER = os.path.join(SCENARIO_ROOT, 'input')
SCRATCH_FOLDER = os.path.join(SCENARIO_ROOT, 'scratch')
OUTPUT_FOLDER = os.path.join(SCENARIO_ROOT, 'output')
