#!/bin/sh
#SBATCH -t 4:00:00
#SBATCH -n 1
#SBATCH --mem=10G
#SBATCH -J A2457_annular
#SBATCH -o A2457_annular.out
#SBATCH -v 
#SBATCH --mail-type=ALL
#SBATCH --mail-user=jmac.ftw@gmail.com
#

python process_annular.py
 
#fitvd --seed 1 --config superbit_meds.yaml --output fitvd-exp-out.fits a2457.meds
