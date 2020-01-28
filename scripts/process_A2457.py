import os,sys
import importlib.util
import glob
import pdb, traceback
import esutil as eu
# Get the location of the main superbit package.
dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,dir)
from superbit import medsmaker

# Start by making a directory...
if not os.path.exists('../Data/calib'):
    os.mkdir('../Data/')
    os.mkdir('../Data/calib')

# This is picking out only Luminance images
science = glob.glob('/users/jmcclear/scratch/A2457_data/c4d_141024_*ooi_r_v1_*.fits')
weights = glob.glob('/users/jmcclear/scratch/A2457_data/c4d_141024_*oow_r_v1_*.fits') # this is actually weights but w/e
darks = glob.glob('/users/jmcclear/scratch/A2457_data/c4d_141024_*ood_r_v1_*.fits')
try:
    bm = medsmaker.BITMeasurement(image_files=science,weight_files=weights, dark_files=darks)
    # The path names should be updated; as written the code also expects all
    # calibration files to be in the same directory

    """
    bm.set_working_dir()
    bm.set_psf_dir()
    bm.set_path_to_calib_data(path='/users/jmcclear/scratch/A2457_data/')
    bm.set_path_to_science_data(path='/users/jmcclear/scratch/A2457_data/')

    #bm.reduce(overwrite=False)
    #bm.make_mask(overwrite=False)
    bm.make_catalog(source_selection = True)

    bm.make_psf_models()

    image_info = bm.make_image_info_struct()
    obj_info = bm.make_object_info_struct()
    """
    bm.run(outfile="a2457.meds",clobber=True,source_selection = False)

except:
    thingtype, value, tb = sys.exc_info()
    traceback.print_exc()
    pdb.post_mortem(tb)
