#!/bin/bash
#SBATCH --job-name=mux0001_b5b7_merge_atm_3d
#SBATCH --time=00:30:00
#SBATCH --nodes=2
#SBATCH --mem=256G
#SBATCH --output=/home/m/m301254/project_surfwaves/bash_scripts/log/%x.%A.out
#SBATCH --error=/home/m/m301254/project_surfwaves/bash_scripts/log/%x.%A.err
#SBATCH --account=mh0033
#SBATCH --partition=compute
#SBATCH --array=0-3%2
#SBATCH --exclusive

set -euo pipefail

# ====================
# Config
# ====================
EXP="mux0001_b5b7"
CATEGORY="atm_3d"

INDIR="/work/mh0033/m301254/proj_surfwave/icon-2025-08-06-XPP/icon-mpim/experiments/${EXP}/outdata"
OUTDIR="/work/mh0033/m301254/proj_surfwave/processed_data/${EXP}"
mkdir -p "${OUTDIR}"

VARS_3D=(u v)
VAR=${VARS_3D[$SLURM_ARRAY_TASK_ID]}

OUTFILE="${OUTDIR}/${EXP}_${CATEGORY}_${VAR}_1330-1345.nc"

echo "[$(date)] Processing variable: ${VAR}"

# ====================
# Environment
# ====================
module purge
module load cdo
export HDF5_USE_FILE_LOCKING=FALSE

# ====================
# Merge
# ====================
cdo -O \
  -selname,${VAR} \
  -mergetime \
  ${INDIR}/${EXP}_${CATEGORY}_13300101T000000Z.nc \
  ${INDIR}/${EXP}_${CATEGORY}_13350101T000000Z.nc \
  ${INDIR}/${EXP}_${CATEGORY}_13400101T000000Z.nc \
  ${INDIR}/${EXP}_${CATEGORY}_13450101T000000Z.nc \
  "${OUTFILE}"

echo "[$(date)] Finished ${VAR}"
