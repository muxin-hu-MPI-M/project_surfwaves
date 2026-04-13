#!/bin/bash
#SBATCH --job-name=mux0003_b5b7_atm_3d_interp_zlev
#SBATCH --time=00:45:00
#SBATCH --nodes=1
#SBATCH --mem=256G
#SBATCH --output=/home/m/m301254/project_surfwaves/bash_scripts/log/%x.%A.%a.out
#SBATCH --error=/home/m/m301254/project_surfwaves/bash_scripts/log/%x.%A.%a.err
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
# File selection (robust)
# ====================

mapfile -t FILES < <(find "${INDIR}" -maxdepth 1 -type f -name "${EXP}_${CATEGORY}_*.nc" | sort)

if [[ ${#FILES[@]} -eq 0 ]]; then
    echo "No input files found!"
    exit 1
fi

if [[ ${SLURM_ARRAY_TASK_ID} -ge ${#FILES[@]} ]]; then
    echo "Task ${SLURM_ARRAY_TASK_ID} exceeds file list size ${#FILES[@]}"
    exit 0
fi

INFILE="${FILES[$SLURM_ARRAY_TASK_ID]}"
BASENAME=$(basename "${INFILE}")
OUTFILE="${OUTDIR}/${BASENAME/_atm_3d_/_atm_3d_zlev_}"

echo "[$(date)] Processing: ${INFILE}"

# ====================
# Vertical levels (60-level smooth grid)
# ====================

hlevels="0,20,40,60,80,100,150,200,250,300,400,500,600,750,900,1100,1300,1600,1900,2200,2600,3000,3500,4000,4500,5000,6000,7000,8000,9000,10000,11000,12000,13000,14000,15000,16500,18000,19500,21000,22500,24000,26000,28000,30000,32000,34000,36000,38000,40000,45000,50000,55000,60000,65000,70000"

atm_3d_names="pres,geopot,temp,u,v,qv,rh,clc,tot_qc_dia,tot_qi_dia"

# ====================
# Environment
# ====================

module purge
module load cdo
export HDF5_USE_FILE_LOCKING=FALSE

THREADS=${SLURM_CPUS_PER_TASK:-16}

# ====================
# Temporary workspace
# ====================

TMPDIR=$(mktemp -d)
trap 'rm -rf "${TMPDIR}"' EXIT

GH_FILE="${TMPDIR}/gh.nc"
WORK_FILE="${TMPDIR}/work.nc"
RAW_OUT="${TMPDIR}/zlev.nc"

# ====================
# Build geometric height
# ====================

if ! cdo -s sinfo "${INFILE}" | grep -q geopot; then
    echo "ERROR: geopot variable not found"
    exit 1
fi

cdo -O -L \
    -setattribute,gh@standard_name=geometric_height_at_full_level_center,gh@long_name=geometric_height_at_full_level_center,gh@units=m \
    -expr,'gh=geopot/9.80665' \
    -selname,geopot \
    "${INFILE}" \
    "${GH_FILE}"

# ====================
# Merge fields
# ====================

cdo -O -L \
    -merge \
    -select,name=${atm_3d_names} "${INFILE}" \
    "${GH_FILE}" \
    "${WORK_FILE}"

# ====================
# Vertical interpolation
# ====================

cdo -O -L -P ${THREADS} \
    -gh2hlx,${hlevels} \
    "${WORK_FILE}" \
    "${RAW_OUT}"

# ====================
# Final selection
# ====================

cdo -O -L \
    -select,name=${atm_3d_names} \
    "${RAW_OUT}" \
    "${OUTFILE}"

echo "[$(date)] Finished: ${OUTFILE}"