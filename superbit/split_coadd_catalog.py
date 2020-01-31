import numpy as np
import os
from astropy.io import fits
import pdb
from astropy.table import Table,vstack,unique
import glob
#from superbit import split_coadd_catalog

""""
This was written as a standalone script, to be executed on the command line.
However, it can also be imported as a module

TO DO:
   - Rewrite as a class
   - Incorporate into medsmaker.py
"""


def select_sources_from_catalog(fullcat,min_size = 1.,size_key='KRON_RADIUS',hduext=2):

    try:
        catalog=Table.read(fullcat,hdu=hduext)
        keep = (catalog[size_key] > min_size)
        catalog = catalog[keep.nonzero()[0]]
        
        print("Also selecting on SNR_WIN>3 and CLASS_STAR<0.7")
        keep2 = (catalog['SNR_WIN']>3.0) & (catalog['CLASS_STAR']<=0.7)
        catalog = catalog[keep2.nonzero()[0]]
        
        catalog.write('coadd_catalog.fits',overwrite=True,format='fits')
        #cmd = ('mv %s coadd_catalog_full.fits' % fullcat)
        #os.system(cmd)
    except:
        pdb.set_trace()
    #.data[hduext].data = catalog
    catalog.write('coadd_catalog.fits',format='fits',overwrite=True)
    return catalog

def split_cat(catn,hduext=2):
    try:
        catalog=Table.read(catn,hdu=2)
    except:
        catalog=catn
    
    ncats=np.ceil(len(catalog)/200)
    indices=np.arange(ncats)

    for i,index in enumerate(indices):
        #start=int(index*10000); end=int(start+9999)
        start=int(index*100); end=int(start+99)
        if (i!=indices[-1]):
            outtab_name=''.join(['./tmp/coadd_catalog_',str(int(index)),'.fits'])
            catalog[start:end].write(outtab_name,format='fits',overwrite=True)
        else:
            outtab_name=''.join(['./tmp/coadd_catalog_',str(int(index)),'.fits'])
            catalog[start:].write(outtab_name,format='fits',overwrite=True)
    return



def main():

    catalog_name='coadd_catalog_full.fits'
    trimmed_cat=select_sources_from_catalog(catalog_name)
    split_cat(trimmed_cat)

if __name__ == "__main__":
    import pdb, traceback, sys
    try:
        main()
    except:
        thingtype, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)

