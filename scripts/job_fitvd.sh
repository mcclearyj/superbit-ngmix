#!/bin/sh
#SBATCH -t 2:00:00
#SBATCH --mem=4G
#SBATCH -n 1
#SBATCH -J meds_fitvd_test
#SBATCH -v 
#SBATCH --array=0-10
# Use '%A' for array-job ID, '%J' for job ID and '%a' for task ID
#SBATCH -o array-job-outputs/arrayjob-%a.out
#SBATCH -e array-job-outputs/arrayjob-%a.err


### Now do serial job
#mkdir -p array-job-outputs/
echo "Starting job $SLURM_ARRAY_TASK_ID on $HOSTNAME"

if [ "$SLURM_ARRAY_TASK_ID" != "10"  ]; then
    #catalog="$SLURM_ARRAY_TASK_ID"
    end=$((SLURM_ARRAY_TASK_ID * 100))
    start=$((end - 99))
    fitvd --seed 1 --config superbit_meds.yaml --output fitvd-out.chip8.$SLURM_ARRAY_TASK_ID.fits --start $start --end $end chip8.meds
else
    start=$((SLURM_ARRAY_TASK_ID*100 - 99))
    fitvd --seed 1 --config superbit_meds.yaml --output fitvd-out.chip8.$SLURM_ARRAY_TASK_ID.fits --start $start  chip8.meds
fi
