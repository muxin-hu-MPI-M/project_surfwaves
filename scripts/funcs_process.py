# ================================================== #
# Python scripts containing processing functions
# 
# Author: Muxin Hu (muxin.hu@mpimet.mpg.de)
# Last modified: 15.01.2026
# ================================================== #

# libraries
import numpy as np
import pandas as x
import matplotlib.pyplot as plt
import xarray as xr
import pyicon as pyic
import cartopy.crs as ccrs
import sys
import cartopy.feature as cfeature
from matplotlib import cm
import cftime

# ------------------------------------------- #
# Function: Averaging regional values 
# ------------------------------------------- #
def regional_area_mean(field, cell_area, mask):
    """
    - field: DataArray with dims (time, ncells)
    - cell_area: ds_tgrid["cell_area"] (reanme to ncells)
    - mask: regional mask (ncells)
    """
    w = cell_area * mask
    return (field * w).sum("ncells") / w.sum("ncells")
