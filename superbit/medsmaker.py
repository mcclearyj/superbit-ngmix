import ngmix
import numpy as np
import meds
import os
import psfex
from astropy.io import fits
import string
import pdb
from astropy import wcs
import fitsio
import esutil as eu

import astropy.units as u
import astropy.coordinates
from astroquery.gaia import Gaia


'''
Goals:
  - Take as input calibrated images
  - Make masks/weight maps
    -- based on flats/darks: locate bad pixels there
    -- also choose a minimum distance from the edge to mask.
  - Make a catalog (SExtractor)
  - Build a psf model (PSFEx)
  - run the meds maker (use meds.Maker)
  - run ngmix (run library)

TO DO:
    - Make weight files
    - Do a flux calibration for photometric scaling in coaddition/divide by exposure time
    - Actually do darks better: match exposure times, rather than collapsing them all down
    - Run medsmaker
'''


class BITMeasurement():
    def __init__(self, image_files = None, weight_files = None, dark_files = None):
        '''
        :image_files: Python List of image filenames; must be complete relative or absolute path.
        :weight_files: Python List of weight filenames; must be complete relative or absolute path.
        :dark_files: Python List of dark filenames; must be complete relative or absolute path.
        '''

        self.image_files = image_files
        self.weight_files = weight_files
        self.dark_files = dark_files


    def set_working_path(self,path=None):
        if path is None:
            self.work_path = './tmp'
            if not os.path.exists(self.work_path):
                os.mkdir(self.work_path)
        else:
            self.work_path = path
            if not os.path.exists(self.work_path):
                os.mkdir(self.work_path)

    def set_path_to_calib_data(self,path=None):
        if path is None:
            self.calib_path = '../Data/calib'
        else:
            self.calib_path = path

    def set_psf_path(self,path=None):
        if path is None:
            self.psf_path = './tmp/psfex_output'
            if not os.path.exists(self.psf_path):
                os.mkdir(self.psf_path)
        else:
            self.psf_path = path


    
    def set_path_to_science_data(self,path=None):
        if path is None:
            self.science_path = '../Data/timmins2019/raw'
            self.reduced_science_path = '../Data/timmins2019/reduced'
        else:
            self.science_path = path
            self.reduced_science_path = path

    def set_path_to_wcs_data(self,path=None):
        # Possibly deprecated
        if path is None:
            self.wcs_path = '../Data/timmins2019/raw'
        else:
            self.wcs_path = path


    def _get_wcs_info(self,image_filename):
        '''
        Return a new image header with WCS (SIP) information,
        or nothing if the WCS file doesn't exist
        '''
        try:
            # os.path.basename gets the filename if a full path gets supplied
            basename = os.path.basename(image_filename)
            splitted=basename.split('_')
            wcsName=os.path.join(self.wcs_path,str('wcs_'+splitted[2]+'_'+splitted[3]+'.fits'))
            inhead=fits.getheader(wcsName)
            w=wcs.WCS(inhead)
            wcs_sip_header=w.to_header(relax=True)
        except:
            print('cluster %s has no WCS, skipping...' % wcsName )
            wcs_sip_header=None

        return wcs_sip_header

    def _make_new_fits(self,image_filename):
        '''
        Returns new cluster fits file with the
        updated WCS and some important keywords
        List of KW can probably be changed as needed
        '''
        if os.path.exists(image_filename):
            ClusterFITSFile=fits.open(image_filename)
            ClusterHeader=ClusterFITSFile[0].header
            WCSheader=self._get_wcs_info(image_filename)
            if WCSheader is not None:
                for key in WCSheader.keys():
                    ClusterHeader[key]=WCSheader[key]
                outFITS=fits.PrimaryHDU(ClusterFITSFile[0].data,header=ClusterHeader)
                new_image_filename = os.path.join(self.science_path,image_filename.replace(".fits","WCS.fits"))
                outFITS.writeto(new_image_filename)
                return new_image_filename
        else:
            print("Could not process %s" % image_filename)
            return None

    def add_wcs_to_science_frames(self):
        '''
        wrapper for _make_new_fits() which returns astrometry-corrected images
        '''
        fixed_image_files = []
        for image_file in self.image_files:
            fixed_image_file = self._make_new_fits(image_file)
            if fixed_image_file is not None:
                fixed_image_files.append(fixed_image_file)
        self.image_files = fixed_image_files

    def reduce(self,overwrite=False):
        # Read in and average together the bias, dark, and flat frames.
        bname = os.path.join(self.work_path,'master_bias_median.fits')
        if (not os.path.exists(bname) or (overwrite==True)):
            # Taking median biases and darks instead of mean to eliminate odd noise features
            bias_array=[]
            for ibias_file in self.bias_files:
                bias_frame = fitsio.read(ibias_file)
                bias_array.append(bias_frame)
                master_bias = np.median(bias_array,axis=0)
                fitsio.write(os.path.join(self.work_path,'master_bias_median.fits'),master_bias,clobber=True)
        else:
            master_bias = fitsio.read(bname)

        dname = os.path.join(self.work_path,'master_dark_median.fits')
        if (not os.path.exists(dname) or (overwrite==True)):
            dark_array=[]
            for idark_file in self.dark_files:
                hdr = fitsio.read_header(idark_file)
                time = hdr['EXPTIME'] / 1000. # exopsure time, seconds
                dark_frame = ((fitsio.read(idark_file)) - master_bias) * 1./time
                dark_array.append(dark_frame)
                master_dark = np.median(dark_array,axis=0)
                fitsio.write(os.path.join(self.work_path,'master_dark_median.fits'),master_dark,clobber=True)
        else:
            master_dark=fitsio.read(dname)

        fname = os.path.join(self.work_path,'master_flat_median.fits')
        if (not os.path.exists(fname) or (overwrite==True)):
            flat_array=[]
            # Ideally, all the flats should have the SAME exposure time, or rather, each filter
            # gets its own band with its own flat exptime
            for iflat_file in self.flat_files:
                hdr = fitsio.read_header(iflat_file)
                time = hdr['EXPTIME'] /  1000.
                flat_frame = (fitsio.read(iflat_file) - master_bias - master_dark * time ) * 1./time
                flat_array.append(flat_frame)
                master_flat1 = np.median(flat_array,axis=0)
                master_flat = master_flat1/np.median(master_flat1)
                fitsio.write(os.path.join(self.work_path,'master_flat_median.fits'),master_flat,clobber=True)
        else:
            master_flat=fitsio.read(fname)

        reduced_image_files=[]
        for this_image_file in self.image_files:
            # WARNING: as written, function assumes science data is in 0th extension
            this_image_fits=fits.open(this_image_file)
            time=this_image_fits[0].header['EXPTIME']/1000.
            this_reduced_image = (this_image_fits[0].data - master_bias)-(master_dark*time)
            this_reduced_image = this_reduced_image/master_flat
            updated_header = this_image_fits[0].header
            updated_header['HISTORY']='File has been bias & dark subtracted and FF corrected'
            this_image_outname=(os.path.basename(this_image_file)).replace(".fits","_reduced.fits")
            this_image_outname = os.path.join(self.work_path,this_image_outname)
            reduced_image_files.append(this_image_outname)
            this_outfits=fits.PrimaryHDU(this_reduced_image,header=updated_header)
            this_outfits.writeto(this_image_outname,overwrite=True)
        self.image_files=reduced_image_files


    def make_mask(self, global_dark_thresh = 10, global_flat_thresh = 0.85,overwrite=False):
        '''
        Use master flat and dark to generate a bad pixel mask.
        Default values for thresholds may be superseded in function call
        '''
        self.mask_file = os.path.join(self.work_path,'supermask.fits')

        if (not os.path.exists(self.mask_file)) or (overwrite==True):
            # It's bad practice to hard-code filenames in
            mdark_fname = os.path.join(self.work_path,'master_dark_median.fits')
            mflat_fname = os.path.join(self.work_path,'master_flat_median.fits')
            mdark = fits.getdata(mdark_fname)
            mflat = fits.getdata(mflat_fname)

            # Start with dark
            med_dark_array=[]
            flattened=np.ravel(mdark)
            outrav=np.zeros(mflat.size)
            outrav[flattened>=global_dark_thresh]=1
            med_dark_array.append(outrav)
            sum_dark = np.sum(med_dark_array,axis=0)
            # This transforms our bpm=1 array to a bpm=0 array
            darkmask=np.ones(sum_dark.size)
            #darkmask[sum_dark==(len(dark_files))]=0
            darkmask[sum_dark==1]=0
            outfile = fits.PrimaryHDU(darkmask.reshape(np.shape(mdark)))
            outfile.writeto(os.path.join(self.work_path,'darkmask.fits'),overwrite=True)

 
            # Now generate actual mask
            supermask = dark_mask
            outfile = fits.PrimaryHDU(flatmask.reshape(np.shape(mflat)))
            outfile.writeto(os.path.join(self.work_path,'supermask.fits'),overwrite=True)

        else:
            pass

    def _make_detection_image(self,outfile_name = 'detection.fits',weightout_name='weight.fits'):
        '''
        :output: output file where detection image is written.

        Runs SWarp on provided (reduced!) image files to make a coadd image
        for SEX and PSFEx detection.
        '''
        ### Code to run SWARP

        ###### Note that it is necessary to join the individual image/weight files (really the weights)
        ###### into a list for swarping
        inlist=''.join([self.work_path,'/','inlist']) 
        wtlist=''.join([self.work_path,'/','wtlist'])

        with open(inlist, 'w') as filehandle:
            for listitem in self.image_files:
                filehandle.write('%s\n' % listitem)
        with open(inlist, 'w') as filehandle:
            for listitem in self.weight_files:
                filehandle.write('%s\n' % listitem)

        image_args = inlist
        weight_arg = '-WEIGHT_IMAGE '+wtlist

        detection_file = os.path.join(self.work_path,outfile_name) # This is coadd
        weight_file = os.path.join(self.work_path,weightout_name) # This is coadd weight
        
        config_arg = '-c ../superbit/astro_config/swarp.config'
        #config_arg = '-HEADER_ONLY N -WEIGHT_TYPE MAP_WEIGHT'
        
        outfile_arg = '-IMAGEOUT_NAME '+ detection_file + ' -WEIGHTOUT_NAME ' + weight_file
        cmd = ' '.join(['swarp ',image_args,weight_arg,outfile_arg,config_arg])
        print("swarp cmd is " + cmd)
        os.system(cmd)
        return detection_file,weight_file

    def select_sources_from_catalog(self,fullcat,min_size = 1.,size_key='KRON_RADIUS',hdu=2):
        # Choose sources based on quality cuts on this catalog.                                                                            
        keep = (self.catalog[size_key] > min_size)
        self.catalog = self.catalog[keep.nonzero()[0]]

        print("Also selecting on SNR_WIN>10 and SExtractor flags <17...")
        keep2 = (self.catalog['SNR_WIN']>3.0) & (self.catalog['CLASS_STAR']<=0.7)
        self.catalog = self.catalog[keep2.nonzero()[0]]

        # Also write trimmed catalog to file                                                                                               
        cmd = 'mv coadd_catalog.fits coadd_catalog_full.fits'
        os.system(cmd)
        
        fullcat[hdu].data = self.catalog
        fullcat.writeto('coadd_catalog.fits',overwrite=True)

    def select_sources_from_gaia():
        # Use some set of criteria to choose sources for measurement.

        coord = astropy.coordinates.SkyCoord(hdr['CRVAL1'],hdr['CRVAL2'],unit='deg')
        result = Gaia.cone_search_async(coord,radius=10*u.arcminute)
        catalog = result.get_data()
        pass

    def make_catalog(self, sextractor_config_path = '../superbit/astro_config/',source_selection = False):
        '''
        Wrapper for astromatic tools to make catalog from provided images.
        This returns catalog for (stacked) detection image
        '''
        detection_file, weight_file= self._make_detection_image(outfile_name='A2457_coadd.fits',weightout_name='A2457_coadd.weight.fits')
        # Now for the million args...
        
        config_arg = sextractor_config_path+'sextractor.config'
        param_arg = '-PARAMETERS_NAME '+sextractor_config_path+'sextractor.param'
        nnw_arg = '-STARNNW_NAME '+sextractor_config_path+'default.nnw'
        filter_arg = '-FILTER_NAME '+sextractor_config_path+'default.conv'
        cmd = ' '.join(['sex',detection_file,'-WEIGHT_IMAGE',weight_file,param_arg,nnw_arg,filter_arg,'-c',config_arg])
        print("sex cmd is " + cmd)
        
        os.system(cmd)
        try:
            hdu=2
            le_cat = fits.open('coadd_catalog.fits')
            self.catalog = le_cat[hdu].data
            if source_selection is True:
                self.select_sources_from_catalog(fullcat=le_cat,hdu=hdu)
        except:
            print("coadd catalog could not be loaded; check name or catalog hdu extension?")
            pdb.set_trace()
            

    def make_psf_models(self):

        """ 
        Start by making reference star file for later psfcat matching 
        This arrangement is special to DECam data of a single cluster, 
        where all images will have roughly the same center
        """
        hdr = fits.getheader(self.image_files[0])
        coord = astropy.coordinates.SkyCoord(hdr['CRVAL1'],hdr['CRVAL2'],unit='deg')
        result = Gaia.cone_search_async(coord,radius=1.2*u.degree)
        catalog = result.get_data()
        catalog_wg = catalog[catalog['parallax'] >= catalog['parallax_error']]

        """
        now do actual PSF modelling
        """

        self.psfEx_models = []
        for i,imagefile in enumerate(self.image_files):
            weightfile=self.weight_files[i]
            psfex_model_file = self._make_psf_model(imagefile,weightfile = weightfile,star_reference=catalog_wg)
            # move checkimages to psfex_output
            cmd = ' '.join(['mv chi* resi* samp* snap* proto*',self.psf_path])
            os.system(cmd)

            try:
                self.psfEx_models.append(psfex.PSFEx(psfex_model_file))
            except:
                pdb.set_trace()

    def _make_psf_model(self,imagefile,weightfile = 'weight.fits',sextractor_config_path = '../superbit/astro_config/',psfex_out_dir='./tmp/',star_reference=None):
        '''
        Gets called by make_psf_models for every image in self.image_files
        Wrapper for PSFEx. Requires a FITS-LDAC format catalog with vignettes
        '''

        # First, run SExtractor.
        sextractor_config_file = sextractor_config_path+'sextractor.config'
        sextractor_param_arg = '-PARAMETERS_NAME '+sextractor_config_path+'sextractor.param'
        sextractor_nnw_arg = '-STARNNW_NAME '+sextractor_config_path+'default.nnw'
        sextractor_filter_arg = '-FILTER_NAME '+sextractor_config_path+'default.conv'
        imcat_ldac_name=imagefile.replace('.fits','_cat.ldac')
        cmd = ' '.join(['sex',imagefile,'-WEIGHT_IMAGE',weightfile,'-c',sextractor_config_file,'-CATALOG_NAME ',imcat_ldac_name,sextractor_param_arg,sextractor_nnw_arg,sextractor_filter_arg])
        print("sex4psf cmd is " + cmd)
        os.system(cmd)

        # Get a "clean" star catalog for PSFEx input
        psfcat_name = self._select_stars_for_psf(sscat=imcat_ldac_name,imfile=imagefile,star_ref=star_reference)
        # Now run PSFEx on that image and accompanying catalog
        psfex_config_arg = '-c '+sextractor_config_path+'psfex.config'
        # Will need to make that tmp/psfex_output generalizable
        cmd = ' '.join(['psfex', psfcat_name,psfex_config_arg,'-PSFVAR_DEGREES','5','-PSF_DIR', self.psf_path])
        print("psfex cmd is " + cmd)
        os.system(cmd)

        # Just return name, the make_psf_models method reads it in as a PSFEx object
        #psfex_model_file=(imcat_ldac_name.replace('.ldac','.psf')).replace('./tmp',self.psf_path)
        psfex_model_file = self.psf_path+'/'+imcat_ldac_name.split('/')[-1].replace('.ldac','.psf')
        return psfex_model_file

    def _select_stars_for_psf(self,sscat,imfile,star_ref=None):
        '''
        method to obtain stars from SExtractor catalog by comparing to GAIA
            sscat : input ldac-format catalog from which to select stars
            imfile : image file on which sscat is based; needed for header's CRVAL kw
        '''
        # Read in header, get catalog of GAIA sources that overlap the field, ish.

        # get RA/Dec of input catalog, cross-match against GAIA
        ss = fits.open(sscat)
        sexmatcher = eu.htm.Matcher(16, ra=ss[2].data['ALPHAWIN_J2000'], dec = ss[2].data['DELTAWIN_J2000'])
        gaia_matches, sexmatches, dist = sexmatcher.match(star_ref['ra'],star_ref['dec'],radius = 6E-4,maxmatch=1)
        # Save result to file, return filename
        outname = sscat.replace('.ldac','.star')
        ss[2].data=ss[2].data[sexmatches]
        ss.writeto(outname,overwrite=True)

        return outname

    def make_image_info_struct(self,max_len_of_filepath = 120):
        # max_len_of_filepath may cause issues down the line if the file path
        # is particularly long

        image_info = meds.util.get_image_info_struct(len(self.image_files),max_len_of_filepath)
        # When does i get defined?
        i=0
        for image_file in self.image_files:
            image_info[i]['image_path'] = image_file
            image_info[i]['image_ext'] = 0
            #image_info[i]['weight_path'] = self.weight_file
            # FOR NOW:
            image_info[i]['weight_path'] = self.weight_files[i]
            image_info[i]['weight_ext'] = 0
            image_info[i]['bmask_path'] = self.weight_files[i]
            image_info[i]['bmask_ext'] = 0
            i+=1
        return image_info

    def make_meds_config(self,extra_parameters = None):
        '''
        :extra_parameters: dictionary of keys to be used to update the base MEDS configuration dict

        '''
        # sensible default config.
        config = {'first_image_is_coadd': False,'cutout_types':['weight','seg','bmask'],'psf_type':'psfex'}
        if extra_parameters is not None:
            config.update(extra_parameters)
        return config

    def _meds_metadata(self,magzp=0.0):
        meta = np.empty(1,[('magzp_ref',np.float)])
        meta['magzp_ref'] = magzp
        return meta

    def _calculate_box_size(self,angular_size,size_multiplier = 2.5, min_size = 16, max_size= 64, pixel_scale = 0.263):
        '''
        Calculate the cutout size for this survey.

        :angular_size: angular size of a source, with some kind of angular units.
        :size_multiplier: Amount to multiply angular size by to choose boxsize.
        :deconvolved:
        :min_size:
        :max_size:

        '''
        box_size_float = np.ceil( angular_size/pixel_scale)

        # Available box sizes to choose from -> 16 to 256 in increments of 2
        available_sizes = min_size * 2**(np.arange(np.ceil(np.log2(max_size)-np.log2(min_size)+1)).astype(int))

        # If a single angular_size was proffered:
        if isinstance(box_size_float, np.ndarray):
            available_sizes_matrix = available_sizes.reshape(1,available_sizes.size).repeat(angular_size.size,axis=0)
            box_size_float_matrix=box_size_float.reshape(box_size_float.size,1)
            #available_sizes_matrix[box_size_float.reshape(box_size_float.size,1) > available_sizes.reshape(1,available_sizes.size)] = np.max(available_sizes)+1
            available_sizes_matrix[box_size_float.reshape(box_size_float.size,1) > available_sizes_matrix] = np.max(available_sizes)+1
            box_size = np.min(available_sizes_matrix,axis=1)
        else:
            box_size = np.min( available_sizes[ available_sizes > box_size_float ] )
        return box_size

    def make_object_info_struct(self,catalog=None):
        if catalog is None:
            catalog = self.catalog

        obj_str = meds.util.get_meds_input_struct(catalog.size,extra_fields = [('KRON_RADIUS',np.float),('number',np.int)])
        obj_str['id'] = catalog['NUMBER']
        obj_str['number'] = np.arange(catalog.size)+1
        obj_str['box_size'] = self._calculate_box_size(catalog['KRON_RADIUS'])
        obj_str['ra'] = catalog['ALPHAWIN_J2000']
        obj_str['dec'] = catalog['DELTAWIN_J2000']
        obj_str['KRON_RADIUS'] = catalog['KRON_RADIUS']
        return obj_str

    def run_meds_only(self,outfile = "superbit.meds",catalog='coadd_catalog.fits',source_selection=True):
        # Make a MEDS, clobbering if needed                                                                                                                                                

        # Set up the paths to the psf and temporary data                                                                                                                                   
        self.set_working_path()
        self.set_psf_path()
        print("I enter run_meds_only")
        # Image info needs a catalog, a list of images, a list of psfs                                                                                                                     
        try:
            self.psfEx_models
            pass
        except:
            self.psfEx_models=[]
            for i,image in enumerate(self.image_files):
                psf_name = self.psf_path+'/'+(image.split('/')[-1]).split('.fits')[0]+'_cat.psf'
                self.psfEx_models.append(psfex.PSFEx(psf_name))

        try:
            self.catalog
            pass
        except:
            try:
                le_cat = fits.open(catalog)
                #self.catalog = le_cat[2].data                                                                                                                                          
                self.catalog = le_cat[1].data
                if source_selection is True:
                    self.select_sources_from_catalog(fullcat=le_cat)
            except:
                print("coadd catalog could not be loaded; check name?")
                pdb.set_trace()


        # Make the image_info struct.                                                                                                                                                      
        image_info = self.make_image_info_struct()
        # Make the object_info struct.                                                                                                                                                     
        obj_info = self.make_object_info_struct()
        # Make the MEDS config file.                                                                                                                                                       
        meds_config = self.make_meds_config()
        # Create metadata for MEDS                                                                                                                                                         
        meta = self._meds_metadata(magzp=30.0)
        # Finally, make and write the MEDS file.                                                                                                                                           
        medsObj = meds.maker.MEDSMaker(obj_info,image_info,config=meds_config,psf_data = self.psfEx_models,meta_data=meta)
        medsObj.write(outfile)

        

    def run(self,outfile = "superbit.meds",clobber=False, source_selection = False):
        # Make a MEDS, clobbering if needed

        # Set up the paths to the science and calibration data.
        self.set_working_path()
        self.set_psf_path()

        # NB: can also read in a pre-existing mask by setting self.mask_file
        #self.make_mask(overwrite=clobber)
        
        # Combine images, make a catalog.
        self.make_catalog(source_selection=source_selection)
        # Build a PSF model for each image.
        self.make_psf_models()
        # Make the image_info struct.
        image_info = self.make_image_info_struct()
        # Make the object_info struct.
        obj_info = self.make_object_info_struct()
        # Make the MEDS config file.
        meds_config = self.make_meds_config()
        # Create metadata for MEDS
        meta = self._meds_metadata(magzp=30.0)
        # Finally, make and write the MEDS file.
        medsObj = meds.maker.MEDSMaker(obj_info,image_info,config=meds_config,psf_data = self.psfEx_models,meta_data=meta)
        medsObj.write(outfile)
