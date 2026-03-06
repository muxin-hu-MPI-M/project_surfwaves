import numpy as np
import xarray as xr
import pyicon as pyic
from pyproj import Geod

# some more or less general functions to work efficiently on a cropped area of the icon grid

def xr_scalar_cell2edges_par(ds_IcD, scalar):
    """
    maps a scalar from cell centres to edges using
    the logic of the equivalent vector pyicon function

    Parameters
    ----------
    ds_IcD : xr.Dataset
        pyicon dataset containing coordinate info
    scalar : xr.DataArray
        scalar at cell center, dims ('cell', ...).
    """
    # scalar = scalar.where(scalar != 0, np.nan) # check if really needed !!
    ic0 = ds_IcD.adjacent_cell_of_edge.isel(nc_e=0).data
    ic1 = ds_IcD.adjacent_cell_of_edge.isel(nc_e=1).data
    edge_cell_distance0 = ds_IcD.edge_cell_distance.isel(nc_e=0).data
    edge_cell_distance1 = ds_IcD.edge_cell_distance.isel(nc_e=1).data

    scalar_pairs0 = scalar.isel(cell=ic0).rename({'cell': 'edge'}) * edge_cell_distance0
    scalar_pairs1 = scalar.isel(cell=ic1).rename({'cell': 'edge'}) * edge_cell_distance1

    scalar_e = (scalar_pairs0 + scalar_pairs1) / (edge_cell_distance0 + edge_cell_distance1)
    return scalar_e

def xr_scalar_cell2edges_par_new(ds_IcD, scalar, var_name):
    """
    Map scalar from cell centers to edges safely, bypassing xarray alignment issues.
    Works even if there are duplicate edges.
    """
    ic0 = ds_IcD.adjacent_cell_of_edge.isel(nc_e=0).values
    ic1 = ds_IcD.adjacent_cell_of_edge.isel(nc_e=1).values
    d0 = ds_IcD.edge_cell_distance.isel(nc_e=0).values
    d1 = ds_IcD.edge_cell_distance.isel(nc_e=1).values

    scalar_arr = scalar.values
    if scalar_arr.ndim == 3:
        val0 = scalar_arr[:, :, ic0] * d0[None, None, :]
        val1 = scalar_arr[:, :, ic1] * d1[None, None, :]
        edge_vals = (val0 + val1) / (d0 + d1)[None, None, :]
        dims = ["time", "depth", "edge"]
        coords = {"time": scalar.time, "depth": scalar.depth}
    elif scalar_arr.ndim == 2:
        val0 = scalar_arr[:, ic0] * d0[None, :]
        val1 = scalar_arr[:, ic1] * d1[None, :]
        edge_vals = (val0 + val1) / (d0 + d1)[None, :]
        dims = ["depth", "edge"]
        coords = {"depth": scalar.depth}
    else:
        raise ValueError("Unsupported da shape")

    # now assign edge coordinates correctly from the dataset
    coords["elon"] = ("edge", ds_IcD["elon"].values)
    coords["elat"] = ("edge", ds_IcD["elat"].values)

    da_edge = xr.DataArray(edge_vals, 
                           dims=dims, 
                           coords=coords, 
                           name=scalar.name if scalar.name is not None else var_name)
    return da_edge

def build_section_IcD(ds_tgrid, muxin_sec, section_name):
    """
    Build interpolated tgrid (IcD) for a given section.

    Parameters
    ----------
    ds_tgrid : xarray.Dataset
        Original tgrid
    muxin_sec : xarray.Dataset
        Dataset containing mask_section*
    section_name : str
        e.g. "mask_section1"

    Returns
    -------
    ds_IcD : xarray.Dataset
        Interpolated cropped grid for the section
    cells : np.ndarray
        Cell indices used for cropping
    crop_tg : xarray.Dataset
        Cropped tgrid
    """

    # find unique adjacent cells (convert from 1-based to 0-based)
    cells = np.unique(
        ds_tgrid.adjacent_cell_of_edge[:, (muxin_sec[section_name] != 0)].values
        - 1
    )

    # crop tgrid
    crop_tg = pyic.xr_crop_tgrid(ds_tgrid, cells)

    # build interpolated grid
    ds_IcD = pyic.convert_tgrid_data(crop_tg)

    return ds_IcD, cells, crop_tg

def center_to_section_edges(
    ds_IcD,
    ds,
    ds_tgrid,
    muxin_sec,
    crop_tg,
    cells,
    section_name,
    da_str='sigma0',
):
    """
    Computes interpolated scalar from cell to edges and restricted to a section.

    Returns
    -------
    da_e : xarray.DataArray
        da on section edges
    """

    # interpolate da from cells to edges
    da_e = xr_scalar_cell2edges_par(
        ds_IcD,
        ds[da_str].isel(ncells=cells).rename({'ncells': 'cell'})
    )

    # original section edge indices
    sec_ind = ds_tgrid.edge_index.where(
        muxin_sec[section_name] != 0,
        drop=True
    ).values

    # attach edge_index from cropped grid
    da_e = da_e.assign_coords(edge_index=crop_tg.edge_index)

    # keep only section edges
    mask = np.isin(da_e.edge_index, sec_ind)
    da_e = da_e.sel(edge=mask)

    return da_e

def center_to_section_edges_new(
    ds_IcD,
    ds,
    ds_tgrid,
    muxin_sec,
    crop_tg,
    section_name,
    var_name
):
    """
    Computes interpolated scalar from cell to edges. 
    ds need to be pre-selected by section (e.g., ds = ds_raw.sel(ncells=adj_cells))

    Returns
    -------
    da_e : xarray.DataArray
        da on section edges
    """

    # interpolate da from cells to edges
    da_e = xr_scalar_cell2edges_par_new(
        ds_IcD,
        ds.rename({'ncells': 'cell'}),
        var_name
    )

    # original section edge indices
    sec_ind = ds_tgrid.edge_index.where(
        muxin_sec[section_name] != 0,
        drop=True
    ).values

    # attach edge_index from cropped grid
    da_e = da_e.assign_coords(edge_index=crop_tg.edge_index)

    # keep only section edges
    mask = np.isin(da_e.edge_index, sec_ind)
    da_e = da_e.sel(edge=mask)

    return da_e

def add_section_distance(sec_e):
    """
    Add a 'distance' coordinate to a section DataArray based on edge lon/lat.

    Parameters
    ----------
    sec_e : xarray.DataArray
        Section data with 'elon' and 'elat' coordinates in radians.

    Returns
    -------
    data : xarray.DataArray
        Same DataArray with an added 'distance' coordinate (in km), 
        distance measured from eastmost point.
    """
    geod = Geod(ellps="WGS84")

    # sort by longitude descending (east to west)
    data = sec_e.sortby("elon", ascending=False)

    # convert radians to degrees
    lon_deg = np.rad2deg(data.elon)
    lat_deg = np.rad2deg(data.elat)

    # compute cumulative distance along the section
    distances_m = np.r_[0.0, np.cumsum(
        geod.inv(
            lon_deg[:-1].values,
            lat_deg[:-1].values,
            lon_deg[1:].values,
            lat_deg[1:].values,
        )[2]  # [2] is the distance in meters
    )]

    # assign distance coordinate in km
    data = data.assign_coords(distance=("edge", distances_m / 1000))

    return data

def remap_vect_to_edge(crop_ds_IcD, crop_tgrid, uo, vo):
    """
    Remap horizontal velocity components from cell centers to cell edges,
    returning the velocity normal to each edge on a cropped ICON grid.

    This function takes zonal (uo) and meridional (vo) velocity components
    defined at cell centers and:
      1. Ensures that the velocity fields are defined on the same (possibly
         reduced) set of cells as the cropped grid.
      2. Rotates the horizontal velocity vector into the local grid
         coordinate system to obtain the normal velocity at cell centers.
      3. Interpolates the cell-centered normal velocity to cell edges.

    The output represents the velocity crossing each edge, i.e. the normal
    velocity, BUT NOT YET POINTING IN THE SAME DIRECTION FOR A GIVEN SECTION.
    TO DO THAT, WE NEED TO MULTIPLY BY THE SECTION MASK.

    Parameters
    ----------
    crop_ds_IcD : xarray.Dataset
        ICON grid dataset containing geometry and metric information
        (e.g. local coordinate transforms, edge normals) for the cropped grid.
        Typically obtained via `pyic.convert_tgrid_data`.
    crop_tgrid : xarray.Dataset
        Cropped ICON t-grid containing the subset of cells and edges of
        interest. Used to ensure consistency between the grid and the
        velocity fields.
    uo : xarray.DataArray
        Zonal (eastward) velocity at cell centers. May be defined on the full
        grid or already cropped. Dimension must include `ncells` or `cell`.
    vo : xarray.DataArray
        Meridional (northward) velocity at cell centers. Same grid and
        dimensions as `uo`.

    Returns
    -------
    vn_e : xarray.DataArray
        Velocity normal to each cell edge, defined at edges of the cropped
        grid. Positive values indicate flow in the direction of the ICON
        edge-normal convention.

    Notes
    -----
    - If the velocity fields are defined on the full grid, they are first
      subset to the cells present in `crop_tgrid` using `cell_index`.
    - Cell indices are converted from 1-based (ICON convention) to 0-based
      indexing for xarray selection.
    - All non-horizontal dimensions (e.g. time, depth) are preserved.

    """
    if crop_tgrid.cell.size != uo.ncells.size:
        print('selecting velocities on the reduced grid...')
        cells_selected = (crop_tgrid.cell_index.compute() -1)
        uo = uo.rename({'ncells': 'cell'}).sel(cell=cells_selected)
        vo = vo.rename({'ncells': 'cell'}).sel(cell=cells_selected)
    

    vn_c = pyic.xr_calc_3d_from_2dlocal(crop_ds_IcD, uo, vo)
    vn_e = pyic.xr_cell2edges(crop_ds_IcD, vn_c)
    return vn_e

def bin_sections_by_distance(das, dx, section_names=None):
    """
    Bin multiple section DataArrays by distance and stack along a new
    `section` dimension.

    Parameters
    ----------
    das : sequence of xarray.DataArray
        Each DataArray must have:
        - dimension: edge
        - coordinate: distance
        Typical dims: (time, depth, edge)

    dx : float
        Distance bin width (same units as `distance`, e.g. km)

    section_names : sequence of str, optional
        Names for the section dimension. If None, integer labels are used.

    Returns
    -------
    binned : xarray.DataArray
        DataArray with dimensions:
        (section, time, depth, distance)
        where `distance` are bin centers.
    """

    # ---------------- bins ----------------
    dmax = max(float(da.distance.max()) for da in das)
    bins = np.arange(0.0, dmax + dx, dx)
    bin_centers = 0.5 * (bins[:-1] + bins[1:])

    # ---------------- bin each section ----------------
    binned = []
    for da in das:
        out = (
            da
            .groupby_bins("distance", bins)
            .mean("edge", skipna=True)
            .assign_coords(distance=("distance_bins", bin_centers))
            .swap_dims({"distance_bins": "distance"})
            .drop_vars("distance_bins")
        )
        binned.append(out)

    # ---------------- stack along section ----------------
    binned = xr.concat(
        binned,
        dim=xr.DataArray(
            section_names if section_names is not None else np.arange(len(das)),
            dims="section",
            name="section",
        )
    )

    return binned
