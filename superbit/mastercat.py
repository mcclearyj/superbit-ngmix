import numpy as np
import os
from astropy.io import fits
import pdb
from astropy.table import Table,vstack,unique
import glob
from esutil import htm

"""
Goals:
  - Take as input split fitvd catalogs
  - Build a master fitvd catalog
  - Include option to delete subcats 
  - Match fitvd sources with master coadd catalog
  - Write to file a catalog with positions and ellipticity moments, ready for lensing
  - Also has capability to run annular

TO DO:
  - add capabilty to make a matching annular catalog without necessarily having multiple fitvd files
  - possibly add the "split master catalog" capability here, though it could also go into the medsmaker class
  - possibly add the 'annular_plot_rides_again' module here 

"""

class Catalogs():
   def __init__(self, fitvd_files = None):

       self.chipfiles = fitvd_files
       self.master_fitvd = None
       
    def set_coadd_catalog(self,coadd_catalog=None):
        if coadd_catalog is None:
            self.coadd_catalog='./coadd_catalog.fits'
        else:
            self.coadd_catalog=coadd_catalog
            

    def make_master_fitvd(self,hdu = 1,make_clean=True, clobber=True):
        """
        concatenate all the fitvd subcatalogs, then write to file

        make_clean : delete fitvd subcats after making master
        overwrite : overwrite existing master fitvd catalog 

        """
        master_tab=Table.read(self.chipfiles[0]) 
        for c in self.chipfiles[1:]:
            ctab=Table.read(c)
            master_tab1=vstack([master_tab,ctab])
            master_tab=unique(master_tab1,keys='id')
        self.master_fitvd=master_tab

        # now write to file
        master_tab.write('master-fitvd-out.fits',format='fits',overwrite=clobber)
        

    def make_annular_cat(self, hdu_ext=hdu_ext, filter_g=True, clobber=True):
        """
        make a catalog of positions and shapes
        ready for annular.c and lensing in general
      
        Filter_g : whether to clean failed fits or not

        """

        # actually load the master coadd catalog
        try:
            coadd_cat = Table.read(self.coadd_catalog,hdu=hdu_ext)
        except:
            print "wrong coadd extension, try again?"
            pdb.set_trace()

        # do matching
        fitvd_matcher=htm.Matcher(16,ra=self.fit['ra'],dec=self.master_fitvd['dec'])
        sex_ind,fitvd_ind,dist=fitvd_matcher.match(ra=self.master_fitvd['ALPHAWIN_J2000'],dec=self.master_fitvd['DELTAWIN_J2000'],maxmatch=1,radius=5.5E-4)
        for_annular=Table()
        for_annular.add_columns([coadd_cat['ALPHAWIN_J2000'][sex_ind],coadd_cat[sex_ind]['DELTAWIN_J2000'],coadd_cat[sex_ind]['X_IMAGE'],
                                     coadd_cat[sex_ind]['Y_IMAGE']])
        for_annular.add_columns([self.master_fitvd[fitvd_ind]['exp_g'][:,0],self.master_fitvd[fitvd_ind]['exp_g'][:,1]],names=['g1','g2'])
        self.annular_cat = for_annular
        
        # write to file
        if filter_g=True:
            for_annular_clean=for_annular[for_annular['g1']>-10.]
            for_annular_clean.write('fitvd-out.csv',format='ascii.csv',overwrite=clobber)
        else:
            for_annular.write('fitvd-out.csv',format='ascii.csv',overwrite=clobber)

    def _convert_to_fiat(self, annular_cat):
        if (annular_cat.split('.')[1] !='fiat'):
            outfile_arg=annular_cat.split('.')[1]+'.fiat'
            cmd=' '.join(['sdsscsv2fiat',annular_cat,'>',outfile_arg])
            print("sdsscsv2fiat cmd is " + cmd)
            os.system(cmd)
        else:
            print("input catalog %s is already in fiat format, skipping..." % annular_cat)
            outfile_arg=annular_cat
        return outfile_arg
         
    def _make_annular_cmd(self,annular_cat,xcenter,ycenter,startrad,endrand,nbins):
        fiatcat = self._convert_to_fiat(annular_cat)
        col_args = '-c "X_WIN Y_WIN g1 g2"'
        start_arg = ' '.join('-s',startrad)
        end_arg = ' '.join('-e',endrad)
        nbins_arg = ' '.join('-n',nbins)
        outfile_arg = fiatcat.replace('.fiat','.annular')
        cmd = ' '.join(['annular',col_args,start_arg,end_arg,nbins_arg,'>',outfile_arg])
        print('annular cmd is %s' % cmd)
        return cmd


    def run_annular(self, annular_cat=None, xcenter=None, ycenter=None, startrad=500, endrad=14000, nbins=35):

        cmd = self._make_annular_cmd(annular_cat,xcenter,ycenter,startrad,endrand,nbins)
        os.system(cmd)
        
    
    def run(self,coadd_catalog=None, hdu=2, filter_g=True, make_clean=True, clobber=True)

        self.set_coadd_catalog(coadd_catalog=coadd_catalog)
        self.make_master_fitvd(make_clean=make_clean, clobber = clobber)
        self.make_annular_cat(hdu_ext=1,filter_g=filter_g)

        
