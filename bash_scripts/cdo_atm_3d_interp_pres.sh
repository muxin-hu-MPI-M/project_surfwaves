#!/bin/bash
#SBATCH --job-name=mux0003_b5b7_atm_3d_interp_pres
#SBATCH --time=00:45:00
#SBATCH --nodes=1
#SBATCH --mem=256G
#SBATCH --output=/home/m/m301254/project_surfwaves/bash_scripts/log/%x.%A.out
#SBATCH --error=/home/m/m301254/project_surfwaves/bash_scripts/log/%x.%A.err
#SBATCH --account=mh0033
#SBATCH --partition=compute
#SBATCH --array=0-3
#SBATCH --exclusive

set -euo pipefail

# ====================
# Config
# ====================

EXP="mux0003_b5b7_c_k-03"
CATEGORY="atm_3d"

INDIR="/work/mh0033/m301254/proj_surfwave/icon-2025-08-06-XPP/icon-mpim/experiments/${EXP}/outdata"
OUTDIR="/work/mh0033/m301254/proj_surfwave/processed_data/${EXP}"
mkdir -p "${OUTDIR}"

# ====================
# Automatically find files
# ====================

mapfile -t FILES < <(ls ${INDIR}/${EXP}_${CATEGORY}_*.nc | sort)

FILE=${FILES[$SLURM_ARRAY_TASK_ID]}

if [[ -z "${FILE:-}" ]]; then
    echo "No file for task ${SLURM_ARRAY_TASK_ID}"
    exit 0
fi

INFILE="${FILE}"
BASENAME=$(basename "${FILE}")
OUTFILE="${OUTDIR}/${BASENAME/_atm_3d_/_atm_3d_preslev_}"

echo "[$(date)] Processing ${INFILE}"

# ====================
# Pressure levels
# ====================

plevels=100000,99000,98000,97000,96000,95000,94000,93000,92000,91000,90000,\
88000,86000,84000,82000,80000,\
77500,75000,72500,70000,\
67500,65000,62500,60000,\
57500,55000,52500,50000,\
47500,45000,42500,40000,\
37500,35000,32500,30000,\
27500,25000,22500,20000,\
17500,15000,12500,10000,\
7500,5000,2500

atm_3d_names=pres,geopot,temp,u,v,qv,rh,clc,tot_qc_dia,tot_qi_dia

# ====================
# Environment
# ====================

module purge
module load cdo
export HDF5_USE_FILE_LOCKING=FALSE

# ====================
# Interpolation
# ====================

cdo -O -L -P ${SLURM_CPUS_PER_TASK:-32} \
-select,name=${atm_3d_names} \
-ap2plx,${plevels} \
"${INFILE}" \
"${OUTFILE}"

echo "[$(date)] Finished ${OUTFILE}"