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
    Plot a single-row (1 × 3) comparison of one variable:
    the default climatology and two experiment-minus-default differences.

    The function fills three pre-existing axes:
      1) default climatology
      2) experiment 1 − default
      3) experiment 2 − default

    Parameters
    ----------
    axes : array-like of matplotlib.axes.Axes
        A length-3 array of axes on which the plots are drawn.
        The axes are assumed to use a geographic projection
        (e.g., PlateCarree).

    grid_type : str
        Grid type identifier used to select grid and KD-tree files
        (e.g., "atm" or "oce").

    field_def : xarray.DataArray or compatible object
        The default climatological field. Must provide a
        ``.pyic.plot()`` method.

    diff1, diff2 : xarray.DataArray or compatible object
        Difference fields relative to the default climatology
        (e.g., Exp1 − Default, Exp2 − Default).

    varname : str
        Name of the variable, used in subplot titles.

    diff_clim : tuple or list
        Color limits (vmin, vmax) applied to both difference plots
        to ensure consistent scaling.

    unit : str
        Unit label for the colorbars.

    titles : tuple of str, optional
        Titles for the three panels, ordered as
        (default, diff1, diff2).

    lon_reg, lat_reg : tuple, optional
        Longitude and latitude bounds (min, max) for regional
        plotting. If None, the full domain is shown.

    use_contf : bool, optional
        If True, use contourf-style plotting with predefined
        contour spacing; otherwise, fall back to the default
        plotting behavior of ``pyic.plot``.

    Notes
    -----
    This function does not create a figure or axes. It is intended
    to be called within a higher-level plotting routine that
    manages figure layout and iteration over variables.
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
    """
    Plot multiple variables as a stacked set of 1 × 3 panels
    (default climatology + two experiment differences per variable).

    Each variable occupies one row, producing an overall layout
    of (N variables) × 3 columns.

    Parameters
    ----------
    var_list : list of dict
        List of variable configuration dictionaries. Each dictionary
        must contain the following keys:

        Required keys:
          - "grid_type" : str
              Grid identifier (e.g., "atm" or "oce").
          - "field_def" : DataArray-like
              Default climatological field.
          - "diff1" : DataArray-like
              Experiment 1 − default difference.
          - "diff2" : DataArray-like
              Experiment 2 − default difference.
          - "varname" : str
              Variable name for plot titles.
          - "diff_clim" : tuple
              Color limits (vmin, vmax) for difference plots.
          - "unit" : str
              Unit label for the colorbars.

        Optional keys:
          - "titles" : tuple of str
              Custom titles for the three panels.
          - "lon_reg" : tuple
              Longitude bounds (min, max).
          - "lat_reg" : tuple
              Latitude bounds (min, max).
          - "use_contf" : bool
              Override the global ``use_contf`` setting for this variable.

    save_path : str or False, optional
        If a string is provided, the figure is saved to this path.
        If False, the figure is not saved.

    use_contf : bool, optional
        Default contourf-style plotting flag applied to all variables
        unless overridden in an individual variable dictionary.

    Returns
    -------
    None

    Notes
    -----
    - A PlateCarree projection is used for all subplots.
    - Colorbars are added individually to each panel.
    - This function serves as a high-level wrapper around
      ``plot_2d_3exps`` for batch plotting of multiple variables.
    """
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

