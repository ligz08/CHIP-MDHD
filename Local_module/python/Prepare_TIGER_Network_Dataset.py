
"""
Download CHIT 2017 fom CARB website,
and extract TIGER network dataset `ITN_TIGER_2017_ND`

This script is written for and tested under the Python that comes with ArcGIS Desktop 10.4, that is:
Python 2.7.10 (default, May 23 2015, 09:40:32) [MSC v.1500 32 bit (Intel)]
Python 3.x and 64-bit Python are known to be incompatible with ArcGIS Desktop.
"""


import urllib
import zipfile
import arcpy
import os
import sys
import argparse
import shutil

def download_CHIT2017(dest_path='CHIT_2017.ZIP'):
    CHIT2017_url = 'https://www.arb.ca.gov/msprog/zevprog/hydrogen/CHIT_2017.ZIP'
    conn = urllib.urlopen(CHIT2017_url)
    meta = conn.info()
    filesize = meta.getheaders('Content-Length')[0]
    conn.close()
    print 'Fetching CHIT 2017 from CARB\'s website: {}'.format(CHIT2017_url)
    print 'File size: {} bytes.'.format(filesize)
    sys.stdout.write('Downloading... ')
    sys.stdout.flush()
    urllib.urlretrieve(CHIT2017_url, dest_path)
    print 'Complete.'


try:
    '''
    Parse Arguments
    '''
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-c','--clean', help='clean downloaded files after obtaining needed dataset.', action='store_true')
    args = arg_parser.parse_args()

    '''
    Work Environment
    '''
    script_dir = os.path.dirname(os.path.abspath(__file__))
    module_dir = os.path.join(script_dir, '..')
    module_dir = os.path.normpath(module_dir)
    network_dataset_gdb_name = 'TIGER_ND.gdb'
    network_dataset_gdb_path = os.path.join(module_dir, network_dataset_gdb_name)
    network_dataset_parent_path = os.path.join(network_dataset_gdb_path, 'ITN_TIGER_2017')
    network_dataset_path = os.path.join(network_dataset_parent_path, 'ITN_TIGER_2017_ND')
    CHIT2017_zipfile_path = os.path.join(module_dir, 'CHIT_2017.ZIP')
    CHIT2017_gdb_path = os.path.join(module_dir, 'CHIT2017.gdb')
    
    arcpy.env.workspace = module_dir
    arcpy.env.overwriteOutput = True

    '''
    Check if network dataset already exists
    '''
    if arcpy.Exists(network_dataset_path) and raw_input('Network dataset `ITN_TIGER_2017_ND` already exists. Overwrite? [y/n] ').lower() not in ['y', 'yes']:
        print 'Exiting.'
        quit()

    '''
    Download CHIT 2017 from CARB website
    '''
    if os.path.exists(CHIT2017_zipfile_path) and raw_input('`CHIT_2017.ZIP` already exists. Overwrite? [y/n] ').lower() not in ['y', 'yes']:
        print 'Using existing `CHIT_2017.ZIP`.'
    else:
        download_CHIT2017(dest_path=CHIT2017_zipfile_path)

    '''
    Extract zip file
    '''
    if os.path.exists(CHIT2017_gdb_path) and raw_input('`CHIT2017.gdb` already exists. Overwrite? [y/n] ').lower() not in ['y', 'yes']:
        print 'Using existing `CHIT2017.gdb`.'
    else:
        sys.stdout.write('Extracting CHIT2017.gdb from CHIT_2017.ZIP... ')
        sys.stdout.flush()
        with zipfile.ZipFile(CHIT2017_zipfile_path, 'r') as z:
            for f in z.namelist():
                if f.startswith('CHIT2017.gdb/'):
                    z.extract(f, module_dir)
        print 'Complete.'

    '''
    Copy network dataset to another gdb
    '''
    sys.stdout.write('Copying `ITN_TIGER_2017` from `CHIT2017.gdb` to `TIGER_ND.gdb`... ')
    if not os.path.exists(network_dataset_gdb_path):
        arcpy.CreateFileGDB_management(module_dir, network_dataset_gdb_name)
    arcpy.Copy_management(
        in_data=os.path.join(CHIT2017_gdb_path, 'ITN_TIGER_2017'), 
        out_data=network_dataset_parent_path)
    print 'Complete.'

    '''
    Clean downloads
    '''
    if args.clean:
        print 'Cleaning up downloads:'
        for trash in [CHIT2017_zipfile_path, CHIT2017_gdb_path]:
            sys.stdout.write('{}:... '.format(trash))
            sys.stdout.flush()
            if not os.path.exists(trash):
                print 'not found.'
            elif os.path.isdir(trash):
                shutil.rmtree(trash)
                print 'directory removed.'
            else:
                os.remove(trash)
                print 'file removed.'



except Exception as e:
    # If an error occurred, print line number and error message
    import traceback, sys
    tb = sys.exc_info()[2]
    print "An error occurred on line %i" % tb.tb_lineno
    print str(e)