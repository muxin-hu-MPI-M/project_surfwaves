#!/bin/bash
#SBATCH --job-name=merge_mux0001_b5b7
#SBATCH --time=00:20:00
#SBATCH --nodes=1
#SBATCH --mem=256G
#SBATCH --output=log.o-%j.out
#SBATCH --error=log.e-%j.err
#SBATCH --account=mh0033
#SBATCH --partition=compute
#SBATCH --exclusive

set -euo pipefail

# ====================
# User settings
# ====================
EXP="mux0001_b5b7"
CATEGORY="oce_def"

INDIR="/work/mh0033/m301254/proj_surfwave/icon-2025-08-06-XPP/icon-mpim/experiments/${EXP}/outdata"
OUTDIR="/work/mh0033/m301254/proj_surfwave/processed_data/${EXP}"

OUTFILE_3d="${OUTDIR}/${EXP}_${CATEGORY}_3d_1330-1345.nc"
OUTFILE_2d="${OUTDIR}/${EXP}_${CATEGORY}_2d_1330-1345.nc"

vars_3d="rhopot,so,to,mass_flux"
vars_2d="tos,sos,mld"

mkdir -p "${OUTDIR}"

echo "[$(date)] Input directory : ${INDIR}"
echo "[$(date)] 3D output file : ${OUTFILE_3d}"
echo "[$(date)] 3D variables   : ${vars_3d}"
echo "[$(date)] 2D output file : ${OUTFILE_2d}"
echo "[$(date)] 2D variables   : ${vars_2d}"

# ====================
# Environment
# ====================
module purge
module load cdo
export HDF5_USE_FILE_LOCKING=FALSE

# =========================
# Merge 3D variables
# =========================
cdo -O -selname,${vars_3d} -mergetime \
  ${INDIR}/${EXP}_${CATEGORY}_13300101T000000Z.nc \
  ${INDIR}/${EXP}_${CATEGORY}_13350101T000000Z.nc \
  ${INDIR}/${EXP}_${CATEGORY}_13400101T000000Z.nc \
  ${INDIR}/${EXP}_${CATEGORY}_13450101T000000Z.nc \
  "${OUTFILE_3d}"
echo "[$(date)] CDO 3D merge finished"

# =========================
# Merge 2D variables
# =========================
cdo -O -selname,${vars_2d} -mergetime \
  ${INDIR}/${EXP}_${CATEGORY}_13300101T000000Z.nc \
  ${INDIR}/${EXP}_${CATEGORY}_13350101T000000Z.nc \
  ${INDIR}/${EXP}_${CATEGORY}_13400101T000000Z.nc \
  ${INDIR}/${EXP}_${CATEGORY}_13450101T000000Z.nc \
  "${OUTFILE_2d}"
echo "[$(date)] CDO 2D merge finished"
