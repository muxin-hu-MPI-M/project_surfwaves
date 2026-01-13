#!/bin/bash
#SBATCH --job-name=c_k-10_timmean_oce_def_3d
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --mem=256G
#SBATCH --output=/home/m/m301254/project_surfwaves/bash_scripts/log/%x.%A_%a.out
#SBATCH --error=/home/m/m301254/project_surfwaves/bash_scripts/log/%x.%A_%a.err
#SBATCH --account=mh0033
#SBATCH --partition=compute
#SBATCH --array=0-3%2
#SBATCH --exclusive

set -euo pipefail

# ====================
# Config
# ====================
EXP="mux0001_b5b7_c_k-10"
CATEGORY="oce_def"

INDIR="/work/mh0033/m301254/proj_surfwave/processed_data/${EXP}"
OUTDIR="/work/mh0033/m301254/proj_surfwave/processed_data/${EXP}"
#mkdir -p "${OUTDIR}"

VARS_3D=(rhopot so to mass_flux)
VAR=${VARS_3D[$SLURM_ARRAY_TASK_ID]}

INFILE="${INDIR}/${EXP}_${CATEGORY}_${VAR}_1330-1345.nc"
OUTFILE="${OUTDIR}/${EXP}_${CATEGORY}_${VAR}_1330-1345_mean.nc"

echo "============================================"
echo "Job name    : ${SLURM_JOB_NAME}"
echo "Job ID      : ${SLURM_JOB_ID}"
echo "Array ID    : ${SLURM_ARRAY_TASK_ID}"
echo "Variable    : ${VAR}"
echo "Input file  : ${INFILE}"
echo "Output file : ${OUTFILE}"
echo "Start time  : $(date)"
echo "============================================"

# ====================
# Environment
# ====================
module purge
module load cdo
export HDF5_USE_FILE_LOCKING=FALSE

# ====================
# Time mean
# ====================
cdo -O \
  -timmean \
  "${INFILE}" \
  "${OUTFILE}"

echo "[$(date)] Finished timmean for ${VAR}"
