# ================================================== #
# Python scripts containing processing functions
# 
# Author: Muxin Hu (muxin.hu@mpimet.mpg.de)
# Last modified: 15.01.2026
# ================================================== #

# libraries
import numpy as np
import xarray as xr
import pyicon as pyic
from pyproj import Geod


# ------------------------------------------- #
# Function: crop tgrid file to a given region
# ------------------------------------------- #
def crop_tgrid_to_region(tgrid, mask):
	"""
    Crop tgrid to the region defined by the mask.
	
    Parameters
	----------
	- tgrid : xarray.Dataset
	    The original tgrid dataset.
	- mask : xarray.DataArray
        The mask defining the region to crop to.
    
	Returns
	----------
	- ds_IcD: xarray.Dataset
	    The cropped tgrid dataset.
    - crop_tg: xarray.Dataset
        The cropped tgrid dataset.
    - ireg_c: numpy array
        The cell indices of the cropped region.
	"""
	# contained_cells: cell index of masked area
	ireg_c = mask["contained_cells"].astype(int)
	crop_tg = pyic.xr_crop_tgrid(tgrid, ireg_c)
	# build icon-readable interpolated grid
	ds_IcD = pyic.convert_tgrid_data(crop_tg)

	return ds_IcD, crop_tg, ireg_c


# ------------------------------------------- #
# Function: Calculate regional mean ocean var
# ------------------------------------------- #
def regional_area_mean_oce(field, crop_tg, wet_c):
    """
    Parameters
	----------
    - field : xarray.Dataset 
        The target field for calculation with dims (time, ncells)
    - crop_tg : xarray.Dataset
        The cropped tgrid dataset from function "crop_tgrid_to_region"
    - wet_c : xarray.Dataset
        The wet cell mask dataset, with dims (ncells) and values of 1 for

    Returns
	----------
    - field_ave: xarray.Dataset
        The area-averaged field with dims (time, ncells)
    """
    # select cells from the cropped tgrid file
    cells_selected = crop_tg.cell.rename({"cell": "ncells"})

    # pre-select the field/cell_area to the selected cells
    field_selected = field.isel(ncells=cells_selected).compute()
    cell_area = crop_tg["cell_area"].rename({"cell": "ncells"})
    cell_area_selected = cell_area.isel(ncells=cells_selected)
    wet_c_selected = wet_c.isel(ncells=cells_selected)

    # calculate the weighted area mean
    field_ave = (field_selected * cell_area_selected * wet_c_selected).sum(dim="ncells") / (cell_area_selected * wet_c_selected).sum(dim="ncells")
    return field_ave

# ------------------------------------------- #
# Function: Calculate regional mean atmos var
# ------------------------------------------- #
def regional_area_mean_atm(field, tgrid, mask_atm):
    """
    Parameters
	----------
    - field : xarray.Dataset 
        The target field for calculation with dims (time, ncells)
    - tgrid : xarray.Dataset
        The original tgrid dataset.
    - mask_atm : xarray.Dataset
        The mask dataset for the atmosphere, containing the cell indices of the masked area.

    Returns
	----------
    - field_ave: xarray.Dataset
        The area-averaged field with dims (time,)
    """
    # select cells from the cropped tgrid file
    cells_selected = mask_atm.contained_cells.rename({"cell": "ncells"})

    # pre-select the field/cell_area to the selected cells
    field_selected = field.isel(ncells=cells_selected).compute()
    cell_area = tgrid["cell_area"].rename({"cell": "ncells"})
    cell_area_selected = cell_area.isel(ncells=cells_selected)

    # calculate the weighted area mean
    field_ave = (field_selected * cell_area_selected).sum(dim="ncells") / (cell_area_selected).sum(dim="ncells")
    return field_ave


