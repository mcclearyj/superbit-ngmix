#!/bin/sh
#SBATCH -t 06:00:00
#SBATCH --mem=10G
#SBATCH -n 1
#SBATCH -J meds_fitvd
#SBATCH -v 
#SBATCH --array=1005-1587
# Use '%A' for array-job ID, '%J' for job ID and '%a' for task ID
#SBATCH -o array-job-outputs/arrayjob-%a.out
#SBATCH -e array-job-outputs/arrayjob-%a.err


### Now do serial job

# initialize array

echo "Starting job $SLURM_ARRAY_TASK_ID on $HOSTNAME"

CATALOG='./tmp/coadd_catalog_'$SLURM_ARRAY_TASK_ID'.fits'
MEDSFILE='./tmp/a2457_'$SLURM_ARRAY_TASK_ID'.meds'
python run_medsmaker.py $CATALOG $MEDSFILE
fitvd --seed 1111 --config superbit_meds.yaml --output ./tmp/fitvd-out-$SLURM_ARRAY_TASK_ID.fits $MEDSFILE

