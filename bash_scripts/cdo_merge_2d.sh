#!/bin/bash
#SBATCH --job-name=mux0001_b5b7_c_k-10_merge_oce_def_2d
#SBATCH --time=00:30:00
#SBATCH --nodes=1
#SBATCH --mem=256G
#SBATCH --output=/home/m/m301254/project_surfwaves/bash_scripts/log/%x.%A.out
#SBATCH --error=/home/m/m301254/project_surfwaves/bash_scripts/log/%x.%A.err
#SBATCH --account=mh0033
#SBATCH --partition=compute

set -euo pipefail

# ====================
# Config
# ====================
EXP="mux0001_b5b7_c_k-10"
CATEGORY="oce_def"
VARS_2D="tos,sos,mld"

INDIR="/work/mh0033/m301254/proj_surfwave/icon-2025-08-06-XPP/icon-mpim/experiments/${EXP}/outdata"
OUTDIR="/work/mh0033/m301254/proj_surfwave/processed_data/${EXP}"
OUTFILE="${OUTDIR}/${EXP}_${CATEGORY}_2d_1330-1345.nc"

# temporary file directory
TMPDIR="${OUTDIR}/tmp_2d"

mkdir -p "${OUTDIR}"
mkdir -p "${TMPDIR}"

echo "[$(date)] EXP        : ${EXP}"
echo "[$(date)] VARIABLES  : ${VARS_2D}"
echo "[$(date)] INDIR      : ${INDIR}"
echo "[$(date)] TMPDIR     : ${TMPDIR}"
echo "[$(date)] OUTFILE    : ${OUTFILE}"

# ====================
# Environment
# ====================
module purge
module load cdo
export HDF5_USE_FILE_LOCKING=FALSE

# ====================
# Step 1: select per file (SAFE)
# ====================
FILES=(
  13300101T000000Z
  13350101T000000Z
  13400101T000000Z
  13450101T000000Z
)

echo "[$(date)] Selecting 2D variables per file..."

for f in "${FILES[@]}"; do
  echo "[$(date)]  -> ${f}"
  cdo -O -selname,${VARS_2D} \
    "${INDIR}/${EXP}_${CATEGORY}_${f}.nc" \
    "${TMPDIR}/${EXP}_${CATEGORY}_2d_${f}.nc"
done

# ====================
# Step 2: merge time
# ====================
echo "[$(date)] Merging time dimension..."

cdo -O -mergetime \
  "${TMPDIR}/${EXP}_${CATEGORY}_2d_13300101T000000Z.nc" \
  "${TMPDIR}/${EXP}_${CATEGORY}_2d_13350101T000000Z.nc" \
  "${TMPDIR}/${EXP}_${CATEGORY}_2d_13400101T000000Z.nc" \
  "${TMPDIR}/${EXP}_${CATEGORY}_2d_13450101T000000Z.nc" \
  "${OUTFILE}"

# ====================
# Sanity check
# ====================
echo "[$(date)] Sanity check:"
cdo sinfo "${OUTFILE}"

# ====================
# Cleanup
# ====================
echo "[$(date)] Cleaning temporary files..."
rm -rf "${TMPDIR}"

echo "[$(date)] 2D merge finished successfully"
