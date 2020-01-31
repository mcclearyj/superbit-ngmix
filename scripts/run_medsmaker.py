import os,sys
import importlib.util
import glob
import pdb, traceback
import esutil as eu
# Get the location of the main superbit package.
dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,dir)
from superbit import medsmaker

science = glob.glob('/users/jmcclear/scratch/A2457_data/c4d_141024_*ooi_r_v1_*.fits'); science.sort()
weights = glob.glob('/users/jmcclear/scratch/A2457_data/c4d_141024_*oow_r_v1_*.fits'); weights.sort()
darks = glob.glob('/users/jmcclear/scratch/A2457_data/c4d_141024_*ood_r_v1_*.fits'); darks.sort()

try:

    print ('Number of arguments:', len(sys.argv), 'arguments.')
    print ('Argument List:', str(sys.argv))
    incat = sys.argv[1]
    outmeds = sys.argv[2]

    bm = medsmaker.BITMeasurement(image_files=science,weight_files=weights, dark_files=darks)

    bm.run_meds_only(outfile = outmeds,catalog=incat,source_selection=False)

except:
    thingtype, value, tb = sys.exc_info()
    traceback.print_exc()
    pdb.post_mortem(tb)
