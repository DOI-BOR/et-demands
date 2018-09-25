#--------------------------------
# Name:         build_ag_cdl_shapefiles.py
# Purpose:      Build agricultural land shapefiles from CDL rasters
#--------------------------------

import argparse
import datetime as dt
import logging
import os
import sys

import numpy as np
from osgeo import gdal, ogr, osr

import _arcpy as arcpy
import _gdal_common as gdc
import _ogr2ogr as ogr2ogr
import _util as util


def main(ini_path, overwrite_flag=False):
    """Build CDL shapefiles for agricultural pixels

    Parameters
    ----------
    ini_path : str
        File path of the parameter INI file.
    overwrite_flag : bool
        If True, overwrite existing shapefile (the default is False).

    Returns
    -------
    None

    """
    logging.info('\nBuilding Agricultural CDL Shapefile')

    logging.debug('INI: {}'.format(ini_path))
    config = util.read_ini(ini_path, 'CROP_ET')
    zones_path = config.get('CROP_ET', 'cells_path')
    crops_path = config.get('CROP_ET', 'crops_path')
    temp_path = crops_path.replace('.shp', '_temp.shp')

    cdl_ws = config.get('CROP_ET', 'cdl_folder')
    cdl_year = int(config.get('CROP_ET', 'cdl_year'))
    cdl_format = config.get('CROP_ET', 'cdl_format')
    # It might make more sense to pass the non-ag CDL values instead
    cdl_crops = util.parse_int_set(config.get('CROP_ET', 'cdl_crops'))
    # cdl_nonag = util.parse_int_set(config.get('CROP_ET', 'cdl_nonag'))

    cdl_path = os.path.join(cdl_ws, cdl_format.format(cdl_year, 'img'))

    # Output field name in the crops shapefile
    crops_field = config.get('CROP_ET', 'crops_field')

    shp_driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.isfile(crops_path):
        if overwrite_flag:
            shp_driver.DeleteDataSource(crops_path)
        else:
            return True

    if not os.path.isfile(zones_path):
        logging.error(
            '\nERROR: The ET zone shapefile doesn\'t exist, exiting\n'
            '  {}'.format(zones_path))
        sys.exit()
    elif not os.path.isfile(cdl_path):
        logging.error(
            '\nERROR: The CDL raster doesn\'t exist, exiting\n'
            '  {}'.format(cdl_path))
        sys.exit()

    logging.debug('Zones: {}'.format(zones_path))

    # CDL Raster Properties
    cdl_ds = gdal.Open(cdl_path)
    cdl_band = cdl_ds.GetRasterBand(1)
    cdl_nodata = cdl_band.GetNoDataValue()
    cdl_gtype = cdl_band.DataType
    cdl_proj = cdl_ds.GetProjection()
    cdl_osr = gdc.proj_osr(cdl_proj)
    cdl_geo = cdl_ds.GetGeoTransform()
    cdl_x, cdl_y = gdc.geo_origin(cdl_geo)
    cdl_cs = gdc.geo_cellsize(cdl_geo, x_only=True)
    logging.debug('\nCDL Raster Properties')
    logging.debug('  Geo:        {}'.format(cdl_geo))
    logging.debug('  Snap:       {} {}'.format(cdl_x, cdl_y))
    logging.debug('  Cellsize:   {}'.format(cdl_cs))
    logging.debug('  Nodata:     {}'.format(cdl_nodata))
    logging.debug('  GDAL Type:  {}'.format(cdl_gtype))
    logging.debug('  Projection: {}'.format(cdl_osr.ExportToWkt()))
    # logging.debug('  OSR: {}'.format(cdl_osr))
    # logging.debug('  Extent: {}'.format(zones_extent))

    # ET Zones Properties
    zones_ds = shp_driver.Open(zones_path, 0)
    zones_lyr = zones_ds.GetLayer()
    zones_osr = zones_lyr.GetSpatialRef()
    zones_wkt = gdc.osr_proj(zones_osr)
    zones_extent = gdc.feature_lyr_extent(zones_lyr)
    logging.debug('\nET Zones Shapefile Properties')
    logging.debug('  Extent:     {}'.format(zones_extent))
    logging.debug('  Projection: {}'.format(zones_osr.ExportToWkt()))
    # logging.debug('  OSR: {}'.format(zones_osr))

    # Subset/clip properties
    # Project the extent to the CDL spatial reference
    logging.debug('\nClip Subset')
    clip_extent = zones_extent.project(zones_osr, cdl_osr)
    logging.debug('  Projected:  {}'.format(clip_extent))
    # Adjust the clip extent to the CDL snap point and cell size
    clip_extent.buffer(10 * cdl_cs)
    clip_extent.adjust_to_snap(snap_x=cdl_x, snap_y=cdl_y, cs=cdl_cs,
                               method='EXPAND')
    logging.debug('  Snapped:    {}'.format(clip_extent))
    # Limit the subset extent to CDL extent
    clip_extent.clip(clip_extent)
    logging.debug('  Clipped:    {}'.format(clip_extent))
    # Compute the clip geotransform and shape
    clip_geo = clip_extent.geo(cs=cdl_cs)
    clip_rows, clip_cols = clip_extent.shape(cs=cdl_cs)
    logging.debug('  Rows/Cols:  {} {}'.format(clip_rows, clip_cols))


    # Build a raster mask was a little more efficient than selecting
    # touching features later on
    logging.debug('\nBuilding ET Zones mask')
    zones_count = zones_lyr.GetFeatureCount()
    if zones_count < 255:
        zones_mask_gtype = gdal.GDT_Byte
        zones_mask_nodata = 255
    elif zones_count < 65535:
        zones_mask_gtype = gdal.GDT_UInt16
        zones_mask_nodata = 65535
    else:
        zones_mask_gtype = gdal.GDT_UInt32
        zones_mask_nodata = 4294967295

    memory_driver = gdal.GetDriverByName('GTiff')
    # zones_mask_ds = memory_driver.Create(
    #     os.path.join(os.path.dirname(zones_path), 'zones_mask.tiff'),
    #     clip_cols, clip_rows, 1,  zones_mask_gtype)
    memory_driver = gdal.GetDriverByName('MEM')
    zones_mask_ds = memory_driver.Create(
        '', clip_cols, clip_rows, 1,  zones_mask_gtype)
    zones_mask_ds.SetProjection(cdl_proj)
    zones_mask_ds.SetGeoTransform(clip_geo)
    zones_mask_band = zones_mask_ds.GetRasterBand(1)
    zones_mask_band.Fill(zones_mask_nodata)
    zones_mask_band.SetNoDataValue(zones_mask_nodata)
    gdal.RasterizeLayer(zones_mask_ds, [1], zones_lyr, burn_values=[1])
    # zones_mask_ds = None
    # zones_mask_band = zones_mask_ds.GetRasterBand(1)
    zones_mask = zones_mask_band.ReadAsArray(0, 0, clip_cols, clip_rows)
    zones_mask = (zones_mask != zones_mask_nodata)
    zones_mask_ds = None

    logging.debug('\nBuilding initial CDL polygon shapefile')
    if os.path.isfile(temp_path):
        shp_driver.DeleteDataSource(temp_path)
    polygon_ds = shp_driver.CreateDataSource(temp_path)
    polygon_lyr = polygon_ds.CreateLayer(
        'OUTPUT_POLY', geom_type=ogr.wkbPolygon)
    field_defn = ogr.FieldDefn(crops_field, ogr.OFTInteger)
    polygon_lyr.CreateField(field_defn)

    # TODO: Process CDL by tile
    # logging.debug('\nProcessing CDL by tile')
    # tile_list = [[0, 0]]
    # for tile_i, tile_j in tile_list:
        # logging.debug('  Tile: {} {}'.format(tile_i, tile_j))

    logging.debug('\nConverting CDL raster to polygon')

    # Read the CDL subset array
    clip_xi, clip_yi = array_geo_offsets(cdl_geo, clip_geo)
    logging.debug('  Subset i/j: {} {}'.format(clip_xi, clip_yi))
    cdl_array = cdl_band.ReadAsArray(clip_xi, clip_yi, clip_cols, clip_rows)
    cdl_ds = None

    # Apply the zones mask
    if np.any(zones_mask):
        cdl_array[~zones_mask] = cdl_nodata

    # Set non-agricultural pixels to nodata
    logging.debug('\nMasking non-crop pixels')
    cdl_array_values = np.unique(cdl_array)
    nodata_mask = np.zeros(cdl_array.shape, dtype=np.bool)
    for value in range(1, 255):
        if value in cdl_crops:
            continue
        elif value not in cdl_array_values:
            continue
        # logging.debug('  Value: {}'.format(value))
        nodata_mask |= (cdl_array == value)
    cdl_array[nodata_mask] = cdl_nodata

    # # DEADBEEF - This is using the remap ranges
    # # It is probably more efficient than processing each crop separately
    # nodata_mask = np.zeros(cdl_array.shape, dtype=np.bool)
    # for [start, end, value] in cdl_agmask_remap:
    #     if value == 1:
    #         continue
    #     logging.debug([start, end, value])
    #     nodata_mask |= (cdl_array >= start) & (cdl_array <= end)
    # cdl_array[nodata_mask] = cdl_nodata

    # Create an in-memory raster to read the CDL into
    memory_driver = gdal.GetDriverByName('MEM')
    memory_ds = memory_driver.Create(
        '', clip_cols, clip_rows, 1, cdl_gtype)
    memory_ds.SetGeoTransform(clip_geo)
    memory_ds.SetProjection(cdl_proj)
    memory_band = memory_ds.GetRasterBand(1)
    memory_band.SetNoDataValue(cdl_nodata)

    # Write the CDL subset array to the memory raster
    logging.debug('\nWriting array')
    memory_band.WriteArray(cdl_array, 0, 0)

    # Polygonize the CDL array
    logging.debug('\nConverting raster to polygon')
    gdal.Polygonize(memory_band, memory_band, polygon_lyr, 0)

    # Cleanup
    memory_band = None
    memory_ds = None
    polygon_lyr = None
    polygon_ds = None
    del cdl_array, nodata_mask, zones_mask

    # Write projection/spatial reference
    polygon_osr = gdc.proj_osr(cdl_proj)
    polygon_osr.MorphToESRI()
    polygon_proj = polygon_osr.ExportToWkt()
    with open(temp_path.replace('.shp', '.prj'), 'w') as prj_f:
        prj_f.write(polygon_proj)

    # Project crops to zones spatial reference
    logging.debug('\nProjecting crops to ET zones spatial reference')
    # ogr2ogr.project(temp_path, crops_path, zones_wkt)
    arcpy.project(temp_path, crops_path, zones_osr)

    logging.debug('\nRemoving temporary crops shapefile')
    arcpy.delete(temp_path)


# TODO: Move to gdal_common
def array_geo_offsets(full_geo, sub_geo, cs=None):
    """Return x/y offset of a gdal.geotransform based on another gdal.geotransform

    Parameters
    ----------
    full_geo :
        Larger gdal.geotransform from which the offsets should be calculated.
    sub_geo :
        Smaller form.

    Returns
    -------
    x_offset: number of cells of the offset in the x direction
    y_offset: number of cells of the offset in the y direction

    """
    if cs is None and full_geo[1] == sub_geo[1]:
        cs = full_geo[1]

    # Return UPPER LEFT array coordinates of sub_geo in full_geo
    # If portion of sub_geo is outside full_geo, only return interior portion
    x_offset = int(round((sub_geo[0] - full_geo[0]) / cs, 0))
    y_offset = int(round((sub_geo[3] - full_geo[3]) / -cs, 0))

    # Force offsets to be greater than zero
    x_offset, y_offset = max(x_offset, 0), max(y_offset, 0)
    return x_offset, y_offset


def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='Build Agricultural CDL Shapefile',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-i', '--ini', required=True, metavar='INI',
        type=lambda x: util.is_valid_file(parser, x),
        help='Input INI File')
    parser.add_argument(
        '-o', '--overwrite', default=None, action='store_true',
        help='Overwrite existing files')
    parser.add_argument(
        '-d', '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action="store_const", dest="loglevel")
    args = parser.parse_args()

    # Convert input file to an absolute path
    if args.ini and os.path.isdir(os.path.abspath(args.ini)):
        args.ini = os.path.abspath(args.ini)

    return args


if __name__ == '__main__':
    args = arg_parse()

    logging.basicConfig(level=args.loglevel, format='%(message)s')
    logging.info('\n{}'.format('#' * 80))
    log_f = '{:<20s} {}'
    logging.info(log_f.format('Start Time:', dt.datetime.now().isoformat(' ')))
    logging.info(log_f.format('Current Directory:', os.getcwd()))
    logging.info(log_f.format('Script:', os.path.basename(sys.argv[0])))

    main(ini_path=args.ini, overwrite_flag=args.overwrite)
