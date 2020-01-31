import os,sys
import importlib.util
import glob
import pdb, traceback
import esutil as eu
# Get the location of the main superbit package.
dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,dir)
from superbit import medsmaker2


science = glob.glob('/users/jmcclear/scratch/A2457_data/c4d_141024_*ooi_r_v1_*.fits'); science.sort()
weights = glob.glob('/users/jmcclear/scratch/A2457_data/c4d_141024_*oow_r_v1_*.fits'); weights.sort()
darks = glob.glob('/users/jmcclear/scratch/A2457_data/c4d_141024_*ood_r_v1_*.fits'); darks.sort()
"""
science = list(np.loadtxt('inlist.partial',dtype=np.str)); science.sort()
weights = [s.replace('ooi','oow') for s in science]; weights.sort()
darks = [w.replace('oow','ood') for w in weights]; darks.sort()
"""
try:
    bm = medsmaker2.BITMeasurement(image_files=science,weight_files=weights, dark_files=darks)
    # The path names should be updated; as written the code also expects all
    # calibration files to be in the same directory


    bm.set_working_path()
    bm.set_psf_path()

    #bm.reduce(overwrite=False)
    #bm.make_mask(overwrite=False)
    #bm.make_catalog(source_selection = False)
    #bm.make_psf_models()

    """
    image_info = bm.make_image_info_struct()
    obj_info = bm.make_object_info_struct()
    """
    #bm.run(outfile="a2457.meds",clobber=True,source_selection = False)
    bm.run_meds_only(outfile = "superbit.meds",catalog='coadd_catalog_subset_chunk.fits')

except:
    thingtype, value, tb = sys.exc_info()
    traceback.print_exc()
    pdb.post_mortem(tb)
