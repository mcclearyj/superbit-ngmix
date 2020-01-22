# superbit-ngmix
package originally designed for running ngmix on SuperBIT data, now adapted to run on DECam data

Py3 required to run

The following python packages are required to run:
  - `ngmix` (obviously)
  - `esutil`
  - `meds`
  - `astropy`
  - `fitsio`
  - `psfex` (AstrOmatic; don't use conda forge) 
  - `sextractor` (AstrOmatic; don't use conda forge) 
  - `swarp` (AstrOmatic; don't use conda forge) 

If using conda to manage python installation, packages can be installed with e.g.

`conda install -c conda-forge esutil`

NOTE: `psfex` needs to be installed with git to be a python module, i.e.,
`git clone https://github.com/esheldon/psfex.git`

