#!/bin/sh
#SBATCH -t 48:00:00
#SBATCH -n 1
#SBATCH --mem=10G
#SBATCH -J A2457_meds_production_run
#SBATCH -o A2457_meds_production_run.out
#SBATCH -v 
#SBATCH --mail-type=ALL
#SBATCH --mail-user=jmac.ftw@gmail.com
#

python process_A2457.py
 
#fitvd --seed 1 --config superbit_meds.yaml --output fitvd-exp-out.fits a2457.meds
