import os,sys
import importlib.util
import glob
import pdb, traceback
dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,dir)
from superbit import mastercat

subcats = glob.glob("./tmp/fitvd-out*.fits")
sextractor_catalog = "./coadd_catalog.fits" 
outcat = 'fitvd-out.csv'

try:
    mc = mastercat.Catalogs(fitvd_files=subcats)
    mc.run(coadd_catalog=sextractor_catalog)
    mc.run_annular(annular_cat=outcat, xcenter=16629, ycenter=14555)

except:
    thingtype, value, tb = sys.exc_info()
    traceback.print_exc()
    pdb.post_mortem(tb)
