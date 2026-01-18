# ================================================== #
# Python scripts containing plotting functions
# for atmosphere r2b5 and ocean r2b7 configuration
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

# paths for grids and ckdtree
gname_oce = 'r2b7_oce_r0005'
gname_atm = 'r2b5_atm_r0030'
lev_oce = 'L72'

path_grid_oce = f'/home/m/m301254/pyicon_data/grids/{gname_oce}/'
path_grid_atm = f'/home/m/m301254/pyicon_data/grids/{gname_atm}/'

fpath_tgrid = {}
fpath_ckdtree = {}
fpath_tgrid['atm'] = (f'{path_grid_atm}{gname_atm}_tgrid.nc')
fpath_tgrid['oce'] = (f'{path_grid_oce}{gname_oce}_tgrid.nc')
fpath_ckdtree['atm'] = (f'{path_grid_atm}ckdtree/rectgrids/r2b5_atm_r0030_res0.30_180W-180E_90S-90N.nc')
fpath_ckdtree['oce'] = (f'{path_grid_oce}ckdtree/rectgrids/r2b7_oce_r0005_res0.30_180W-180E_90S-90N.nc')

# ------------------------------------------- #
# Function: plot 2d fields for both ocean or 
# atmosphere, with the following settings:
# 1: Default climatology
# 2&3: climatological difference
# ------------------------------------------- #
def plot_2d_3exps(axes, grid_type, field_def, diff1, diff2, varname, diff_clim, unit,
                         titles=("Default", "Exp1 − Default", "Exp2 − Default"), 
                         lon_reg=None, lat_reg=None, use_contf=True,):
    """
    Plot ONE ROW (1×3): default + two differences
    """
    # ---- base kwargs ----
    plot_kwargs = dict(
        cax=0,
        fpath_tgrid=fpath_tgrid[grid_type],
        fpath_ckdtree=fpath_ckdtree[grid_type],
        title_right="",
    )

    # optional settings (one-liners, no branches)
    lon_reg is not None and plot_kwargs.update(lon_reg=lon_reg)
    lat_reg is not None and plot_kwargs.update(lat_reg=lat_reg)
    use_contf and plot_kwargs.update(use_pcol_or_contf=True, conts=1.0)

    # ---- default climatology ----
    _, ct = field_def.pyic.plot(ax=axes[0], **plot_kwargs)
    axes[0].set_title(f"{varname}: {titles[0]}")
    axes[0].figure.colorbar(ct[0], ax=axes[0], label=unit, pad=0.02)

    # ---- differences ----
    for ax, field, title in zip(
        axes[1:], (diff1, diff2), titles[1:]
    ):
        _, ct = field.pyic.plot(
            ax=ax,
            **plot_kwargs,
            clim=diff_clim,
        )
        ax.set_title(f"{varname}: {title}")
        ax.figure.colorbar(ct[0], ax=ax, label=unit, pad=0.02)

# the function to gather all variables
def plot_all_vars_3exps(var_list, save_path=False, use_contf=True):
    '''
    Docstring for plot_all_variables_global_3exps
    var_list: list of dicts, each containing:
      - grid_type ("atm" or "oce")
      - field_def
      - diff1
      - diff2
      - varname
      - diff_clim
      - unit
      - (optional) titles
      - (optional) lon_reg
      - (optional) lat_reg
      - (optional) use_contf
    '''
    nvar = len(var_list)

    fig, axes = plt.subplots(
        nvar, 3,
        figsize=(5*nvar - 2, 2*nvar),
        subplot_kw={'projection': ccrs.PlateCarree()},
        constrained_layout=True,
        dpi=150,
    )

    if nvar == 1:
        axes = axes[np.newaxis, :]

    for i, var in enumerate(var_list):
        plot_2d_3exps(
            axes=axes[i],
            grid_type=var["grid_type"],
            field_def=var["field_def"],
            diff1=var["diff1"],
            diff2=var["diff2"],
            varname=var["varname"],
            diff_clim=var["diff_clim"],
            unit=var["unit"],
            titles=var.get("titles", None),
            lon_reg=var.get("lon_reg", None),
            lat_reg=var.get("lat_reg", None),
            use_contf=var.get("use_contf", use_contf),
        )

    save_path and fig.savefig(save_path, dpi=150)

