#--------------------------------
# Name:         et_demands_zonal_stats.py
# Purpose:      Calculate zonal stats for all rasters
#--------------------------------

import argparse
from collections import defaultdict
import datetime as dt
import logging
import os
import sys

from osgeo import gdal, ogr, osr
import pandas as pd

import _arcpy
import _gdal_common as gdc
import _rasterstats
import _util


def main(gis_ws, input_soil_ws, cdl_year, zone_type='huc8',
         overwrite_flag=False, cleanup_flag=False):
    """Calculate zonal statistics needed to run ET-Demands model

    Args:
        gis_ws (str): Folder/workspace path of the GIS data for the project
        input_soil_ws (str): Folder/workspace path of the common soils data
        cdl_year (int): Cropland Data Layer year
        zone_type (str): Zone type (huc8, huc10, county)
        overwrite_flag (bool): If True, overwrite existing files
        cleanup_flag (bool): If True, remove temporary files

    Returns:
        None

    """
    logging.info('\nCalculating ET-Demands Zonal Stats')

    # DEADBEEF - Hard code for now
    if zone_type == 'huc10':
        zone_path = os.path.join(gis_ws, 'huc10', 'wbdhu10_albers.shp')
        zone_id_field = 'HUC10'
        zone_name_field = 'HUC10'
        zone_name_str = 'HUC10 '
    elif zone_type == 'huc8':
        zone_path = os.path.join(gis_ws, 'huc8', 'wbdhu8_albers.shp')
        zone_id_field = 'HUC8'
        zone_name_field = 'HUC8'
        zone_name_str = 'HUC8 '
    elif zone_type == 'county':
        zone_path = os.path.join(
            gis_ws, 'counties', 'county_nrcs_a_mbr_albers.shp')
        zone_id_field = 'COUNTYNAME'
        zone_name_field = 'COUNTYNAME'
        zone_name_str = ''
    elif zone_type == 'gridmet':
        zone_path = os.path.join(
            gis_ws, 'gridmet', 'gridmet_4km_cells_albers.shp')
        zone_id_field = 'GRIDMET_ID'
        zone_name_field = 'GRIDMET_ID'
        zone_name_str = 'GRIDMET_ID '
    # elif zone_type == 'nldas':
    #     zone_path = os.path.join(
    #         gis_ws, 'counties', 'county_nrcs_a_mbr_albers.shp')
    #     zone_id_field = 'NLDAS_ID'
    #     zone_name_field = 'NLDAS_ID'
    #     zone_name_str = 'NLDAS_4km_'

    et_cells_path = os.path.join(gis_ws, 'ETCells.shp')

    cdl_ws = os.path.join(gis_ws, 'cdl')
    soil_ws = os.path.join(gis_ws, 'soils')
    zone_ws = os.path.dirname(zone_path)

    agland_path = os.path.join(
        cdl_ws, 'agland_{}_30m_cdls.img'.format(cdl_year))
    agmask_path = os.path.join(
        cdl_ws, 'agmask_{}_30m_cdls.img'.format(cdl_year))

    # ET cell field names
    cell_lat_field = 'LAT'
    cell_lon_field = 'LON'
    cell_id_field = 'CELL_ID'
    cell_name_field = 'CELL_NAME'
    # cell_station_id_field = 'STATION_ID'
    awc_field = 'AWC'
    clay_field = 'CLAY'
    sand_field = 'SAND'
    awc_in_ft_field = 'AWC_IN_FT'
    hydgrp_num_field = 'HYDGRP_NUM'
    hydgrp_field = 'HYDGRP'

    # active_flag_field = 'ACTIVE_FLAG'
    # irrig_flag_field = 'IRRIGATION_FLAG'
    # permeability_field = 'PERMEABILITY'
    # soil_depth_field = 'SOIL_DEPTH'
    # aridity_field = 'ARIDITY'
    # dairy_cutting_field = 'DAIRY_CUTTINGS'
    # beef_cutting_field = 'BEEF_CUTTINGS'

    # active_flag_default = 1
    # irrig_flag_default = 1
    # permeability_default = -999
    # soil_depth_default = 60         # inches
    # aridity_default = 50
    # dairy_cutting_default = 3
    # beef_cutting_default = 2

    # DEADBEEF - Needed if using projected cells for computing zonal stats
    # Output names/paths
    # zone_proj_name = 'zone_proj.shp'
    # # zone_raster_name = 'zone_raster.img'
    # table_ws = os.path.join(gis_ws, 'zone_tables')

    snap_raster = os.path.join(cdl_ws, '{}_30m_cdls.img'.format(cdl_year))
    sqm_2_acres = 0.000247105381        # Square meters to acres (from google)

    # Link ET demands crop number (1-84) with CDL values (1-255)
    # Key is CDL number, value is crop number, comment is CDL class name
    # Crosswalk values are coming from cdl_crosswalk.csv and being upacked into a dictionary
    # Allows user to modify crosswalk in excel
    # Pass in crosswalk file as an input argument
    crosswalk_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'cdl_crosswalk_usbrmod.csv')
    cross = pd.read_csv(crosswalk_file)

    # Add Try and Except for header names, unique crop numbers, etc.
    crop_num_dict = dict()
    for index, row in cross.iterrows():
        crop_num_dict[int(row.cdl_no)] = list(
            map(int, str(row.etd_no).split(',')))
    logging.debug(crop_num_dict)

    # Check input folders
    if not os.path.isdir(gis_ws):
        logging.error('\nERROR: The GIS workspace does not exist'
                      '\n  {}'.format(gis_ws))
        sys.exit()
    elif not os.path.isdir(cdl_ws):
        logging.error('\nERROR: The CDL workspace does not exist'
                      '\n  {}'.format(cdl_ws))
        sys.exit()
    elif not os.path.isdir(soil_ws):
        logging.error('\nERROR: The soil workspace does not exist'
                      '\n  {}'.format(soil_ws))
        sys.exit()
    elif input_soil_ws != soil_ws and not os.path.isdir(input_soil_ws):
        logging.error('\nERROR: The input soil folder does not exist'
                      '\n  {}'.format(input_soil_ws))
        sys.exit()
    elif not os.path.isdir(zone_ws):
        logging.error('\nERROR: The zone workspace does not exist'
                      '\n  {}'.format(zone_ws))
        sys.exit()
    logging.info('\nGIS Workspace:   {}'.format(gis_ws))
    logging.info('CDL Workspace:   {}'.format(cdl_ws))
    logging.info('Soil Workspace:  {}'.format(soil_ws))
    if input_soil_ws != soil_ws:
        logging.info('Soil Workspace:  {}'.format(input_soil_ws))
    logging.info('Zone Workspace:  {}'.format(zone_ws))

    # Check input files
    if not os.path.isfile(snap_raster):
        logging.error('\nERROR: The snap raster does not exist'
                      '\n  {}'.format(snap_raster))
        sys.exit()
    elif not os.path.isfile(agland_path):
        logging.error('\nERROR: The agland raster does not exist'
                      '\n  {}'.format(agland_path))
        sys.exit()
    elif not os.path.isfile(agland_path):
        logging.error('\nERROR: The agmask raster does not exist'
                      '\n  {}'.format(agland_path))
        sys.exit()
    elif not os.path.isfile(zone_path):
        logging.error('\nERROR: The zone shapefile does not exist'
                      '\n  {}'.format(zone_path))
        sys.exit()

    # DEADBEEF - Needed if using projected cells for computing zonal stats
    # # Build output table folder if necessary
    # if not os.path.isdir(table_ws):
    #     os.makedirs(table_ws)

    raster_list = [
        [awc_field, 'mean', ogr.OFTReal,
            os.path.join(input_soil_ws, 'awc_30m_albers.img')],
        [clay_field, 'mean', ogr.OFTReal,
            os.path.join(input_soil_ws, 'clay_30m_albers.img')],
        [sand_field, 'mean', ogr.OFTReal,
            os.path.join(input_soil_ws, 'sand_30m_albers.img')],
        ['AG_COUNT', 'sum', ogr.OFTInteger, agmask_path],
        ['AG_ACRES', 'sum', ogr.OFTReal, agmask_path],
        ['AG_' + awc_field, 'mean', ogr.OFTReal,
            os.path.join(soil_ws, 'awc_{}_30m_cdls.img'.format(cdl_year))],
        ['AG_' + clay_field, 'mean', ogr.OFTReal,
            os.path.join(soil_ws, 'clay_{}_30m_cdls.img'.format(cdl_year))],
        ['AG_' + sand_field, 'mean', ogr.OFTReal,
            os.path.join(soil_ws, 'sand_{}_30m_cdls.img'.format(cdl_year))]
    ]

    # The zone field must be defined
    if zone_id_field not in _arcpy.list_fields(zone_path):
        logging.error('\nERROR: The zone ID field {} does not exist\n'.format(
            zone_id_field))
        sys.exit()
    elif zone_name_field not in _arcpy.list_fields(zone_path):
        logging.error(
            '\nERROR: The zone name field {} does not exist\n'.format(
                zone_name_field))
        sys.exit()

    # The built in ArcPy zonal stats function fails if count >= 65536
    zone_count = _arcpy.get_count(zone_path)
    logging.info('\nZone count: {}'.format(zone_count))

    # Copy the zone_path
    if overwrite_flag and _arcpy.exists(et_cells_path):
        _arcpy.delete(et_cells_path)
    # Just copy the input shapefile
    if not _arcpy.exists(et_cells_path):
        _arcpy.copy(zone_path, et_cells_path)

    # Get spatial reference
    output_osr = gdc.feature_path_osr(et_cells_path)
    snap_osr = gdc.raster_path_osr(snap_raster)
    snap_geo = gdc.raster_path_geo(snap_raster)
    snap_cs = gdc.raster_path_cellsize(snap_raster, x_only=True)
    logging.debug('  Zone WKT: {}'.format(output_osr.ExportToWkt()))
    logging.debug('  Snap WKT: {}'.format(snap_osr.ExportToWkt()))
    logging.debug('  Snap Geo: {}'.format(snap_geo))
    logging.debug('  Snap Cellsize: {}'.format(snap_cs))

    # Add lat/lon fields
    logging.info('Adding Fields')
    field_list = _arcpy.list_fields(et_cells_path)
    if cell_lat_field not in field_list:
        logging.debug('  {}'.format(cell_lat_field))
        _arcpy.add_field(et_cells_path, cell_lat_field, ogr.OFTReal)
    if cell_lon_field not in field_list:
        logging.debug('  {}'.format(cell_lon_field))
        _arcpy.add_field(et_cells_path, cell_lon_field, ogr.OFTReal)

    # Cell ID/name
    if cell_id_field not in field_list:
        logging.debug('  {}'.format(cell_id_field))
        _arcpy.add_field(et_cells_path, cell_id_field, ogr.OFTString, width=24)
    if cell_name_field not in field_list:
        logging.debug('  {}'.format(cell_name_field))
        _arcpy.add_field(et_cells_path, cell_name_field, ogr.OFTString,
                         width=48)

    # Status flags
    # if active_flag_field not in field_list:
    #     logging.debug('  {}'.format(active_flag_field))
    #     _arcpy.add_field(et_cells_path, active_flag_field, OFTInteger)
    # if irrig_flag_field not in field_list:
    #     logging.debug('  {}'.format(irrig_flag_field))
    #     _arcpy.add_field(et_cells_path, irrig_flag_field, OFTInteger)

    # Add zonal stats fields
    for field_name, stat, field_type, raster_path in raster_list:
        if field_name not in field_list:
            logging.debug('  {}'.format(field_name))
            _arcpy.add_field(et_cells_path, field_name, field_type)

    # Other soil fields
    if awc_in_ft_field not in field_list:
        logging.debug('  {}'.format(awc_in_ft_field))
        _arcpy.add_field(et_cells_path, awc_in_ft_field, ogr.OFTReal,
                         width=8, precision=4)
    if hydgrp_num_field not in field_list:
        logging.debug('  {}'.format(hydgrp_num_field))
        _arcpy.add_field(et_cells_path, hydgrp_num_field, ogr.OFTInteger)
    if hydgrp_field not in field_list:
        logging.debug('  {}'.format(hydgrp_field))
        _arcpy.add_field(et_cells_path, hydgrp_field, ogr.OFTString, width=1)
    # if permeability_field not in field_list:
    #     logging.debug('  {}'.format(permeability_field))
    #     _arcpy.add_field(et_cells_path, permeability_field, ogr.OFTReal)
    # if soil_depth_field not in field_list:
    #     logging.debug('  {}'.format(soil_depth_field))
    #     _arcpy.add_field(et_cells_path, soil_depth_field, ogr.OFTReal)
    # if aridity_field not in field_list:
    #     logging.debug('  {}'.format(aridity_field))
    #     _arcpy.add_field(et_cells_path, aridity_field, ogr.OFTReal)

    # Cuttings
    # if dairy_cutting_field not in field_list:
    #     logging.debug('  {}'.format(dairy_cutting_field))
    #     _arcpy.add_field(et_cells_path, dairy_cutting_field, ogr.OFTInteger)
    # if beef_cutting_field not in field_list:
    #     logging.debug('  {}'.format(beef_cutting_field))
    #     _arcpy.add_field(et_cells_path, beef_cutting_field, ogr.OFTInteger)

    # Crop fields are only added for needed crops (after zonal histogram)
    # for crop_num in crop_num_list:
    #     field_name = 'CROP_{0:02d}'.format(crop_num)
    #     if field_name not in field_list:
    #         logging.debug('  {}'.format(field_name))
    #         _arcpy.add_field(et_cells_path, field_name, ogr.OFTInteger)

    # Calculate lat/lon
    logging.info('Calculating lat/lon')
    cell_lat_lon_func(et_cells_path, cell_lat_field, cell_lon_field)

    # Set CELL_ID and CELL_NAME
    # zone_id_field must be a string
    logging.info('Calculating {}'.format(cell_id_field))
    _arcpy.calculate_field(
        et_cells_path, cell_id_field, 'str(!{}!)'.format(zone_id_field))
    logging.info('Calculating {}'.format(cell_name_field))
    _arcpy.calculate_field(
        et_cells_path, cell_name_field,
        '"{}" + str(!{}!)'.format(zone_name_str, zone_name_field))

    # DEADBEEF - Needed if using projected cells for computing zonal stats
    # # Remove existing (could use overwrite instead)
    # zone_proj_path = os.path.join(table_ws, zone_proj_name)
    # if overwrite_flag and _arcpy.exists(zone_proj_path):
    #     _arcpy.delete(zone_proj_path)
    #
    # # Project zones to match CDL/snap coordinate system
    # if _arcpy.exists(et_cells_path) and not _arcpy.exists(zone_proj_path):
    #     logging.info('Projecting zones')
    #     _arcpy.project(et_cells_path, zone_proj_path, snap_osr)

    # Calculate zonal stats
    # Use "rasterstats" package for computing zonal statistics
    logging.info('\nProcessing soil rasters')
    # zs_dict = defaultdict(dict)
    for field_name, stat, field_type, raster_path in raster_list:
        logging.info('{} {}'.format(field_name, stat))
        logging.debug('  {}'.format(raster_path))
        zs = _rasterstats.zonal_stats(et_cells_path, raster_path, stats=[stat])

        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug('Sample Output')
            for i, item in enumerate(zs[:3]):
                logging.debug('  {} {}'.format(i, item))
            # input('ENTER')

        # DEADBEEF - Needed if using projected cells for computing zonal stats
        # logging.debug('  {}'.format(zone_proj_path))
        # zs = _rasterstats.zonal_stats(zone_proj_path, raster_path, stats=[stat])

        # Save by FID/feature for easier writing to shapefile
        zs_dict = defaultdict(dict)
        for i, item in enumerate(zs):
            try:
                zs_dict[i][field_name] = item[stat]
            except:
                zs_dict[i][field_name] = None

        # Write zonal stats to shapefile separately for each raster
        _arcpy.update_cursor(et_cells_path, zs_dict)

        logging.debug('')

    # # Write zonal stats to shapefile
    # _arcpy.update_cursor(et_cells_path, zs_dict)

    # Calculate agricultural area in acres
    logging.info('\nCalculating agricultural acreage')
    _arcpy.calculate_field(
        et_cells_path, 'AG_ACRES',
        '!AG_COUNT! * {0} * {1} * {1}'.format(sqm_2_acres, snap_cs))

    # Calculate AWC in in/feet
    logging.info('Calculating AWC in in/ft')
    _arcpy.calculate_field(
        et_cells_path, awc_in_ft_field, '!{}! * 12'.format(awc_field))

    # Calculate hydrologic group
    logging.info('Calculating hydrologic group')
    fields = (clay_field, sand_field, hydgrp_num_field, hydgrp_field)
    values = _arcpy.search_cursor(et_cells_path, fields)
    for fid, row in values.items():
        if row[sand_field] > 50:
            values[fid][hydgrp_num_field], values[fid][hydgrp_field] = 1, 'A'
        elif row[clay_field] > 40:
            values[fid][hydgrp_num_field], values[fid][hydgrp_field] = 3, 'C'
        else:
            values[fid][hydgrp_num_field], values[fid][hydgrp_field] = 2, 'B'
    _arcpy.update_cursor(et_cells_path, values)

    # # Calculate default values
    # logging.info('\nCalculating default values')
    # logging.info('  {:10s}: {}'.format(
    #     active_flag_field, active_flag_default))
    # _arcpy.calculate_field(
    #     _cells_path, active_flag_field, active_flag_default)
    # logging.info('  {:10s}: {}'.format(irrig_flag_field, irrig_flag_default))
    # _arcpy.calculate_field(_cells_path, irrig_flag_field, irrig_flag_default)
    #
    # logging.info('  {:10s}: {}'.format(
    #     permeability_field, permeability_default))
    # _arcpy.calculate_field(
    #     _cells_path, permeability_field, permeability_default)
    # logging.info('  {:10s}: {}'.format(soil_depth_field, soil_depth_default))
    # _arcpy.calculate_field(_cells_path, soil_depth_field, soil_depth_default)
    # logging.info('  {:10s}: {}'.format(aridity_field, aridity_default))
    # _arcpy.calculate_field(_cells_path, aridity_field, aridity_default)
    #
    # logging.info('  {:10s}: {}'.format(
    #     dairy_cutting_field, dairy_cutting_default))
    # _arcpy.calculate_field(
    #     _cells_path, dairy_cutting_field, dairy_cutting_default)
    # logging.info('  {:10s}: {}'.format(
    #     beef_cutting_field, beef_cutting_default))
    # _arcpy.calculate_field(
    #     _cells_path, beef_cutting_field, beef_cutting_default)

    # Calculate zonal stats
    # Use "rasterstats" package for computing zonal statistics
    logging.info('\nCalculating crop zonal stats')
    logging.debug('  {}'.format(et_cells_path))
    logging.debug('  {}'.format(raster_path))
    zs = _rasterstats.zonal_stats(et_cells_path, agland_path, categorical=True)

    # DEADBEEF - Needed if using projected cells for computing zonal stats
    # logging.debug('  {}'.format(zone_proj_path))
    # zs = _rasterstats.zonal_stats(zone_proj_path, agland_path, categorical=True)

    if logging.getLogger().isEnabledFor(logging.DEBUG):
        logging.debug('Sample Output')
        for i, item in enumerate(zs[:3]):
            logging.debug('  {} {}'.format(i, item))
        # input('ENTER')

    # Save by FID/feature for easier writing to shapefile
    logging.debug('\nParsing crop zonal stats')
    zone_crop_dict = {}
    crop_field_fmt = 'CROP_{:02d}'
    for fid, ftr in enumerate(zs):
        # logging.debug('FID: {}'.format(i))
        zone_crop_dict[fid] = {}
        for cdl_str, cdl_pixels in ftr.items():
            # logging.debug('  {} {}'.format(cdl_str, cdl_pixels))
            cdl_number = int(cdl_str)
            # Only 'crops' have a crop number (no shrub, water, urban, etc.)
            if cdl_number not in crop_num_dict.keys():
                if cdl_number != 0:
                    logging.debug('  Skipping CDL {}'.format(cdl_number))
                continue

            # Crop number can be an integer or list of integers (double crops)
            crop_number = crop_num_dict[cdl_number]

            # Crop numbers of -1 are for crops that haven't been linked
            #   to a CDL number
            if not crop_number or crop_number == -1:
                logging.warning('  Missing CDL {}'.format(cdl_number))
                continue

            crop_acreage = cdl_pixels * sqm_2_acres * snap_cs ** 2

            # Save acreage for both double crops
            for c in crop_number:
                crop_field = crop_field_fmt.format(c)
                if crop_field not in zone_crop_dict[fid].keys():
                    zone_crop_dict[fid][crop_field] = crop_acreage
                else:
                    zone_crop_dict[fid][crop_field] += crop_acreage

    # Get unique crop number values and field names
    crop_field_list = sorted(list(set([
        crop_field for crop_dict in zone_crop_dict.values()
        for crop_field in crop_dict.keys()])))
    logging.debug('\nCrop field list: ' + ', '.join(crop_field_list))
    crop_number_list = [int(f.split('_')[-1]) for f in crop_field_list]
    logging.debug('Crop number list: ' + ', '.join(map(str, crop_number_list)))

    # Add fields for CDL values
    logging.info('\nAdding crop fields')
    for field_name in crop_field_list:
        if field_name not in field_list:
            logging.debug('  {}'.format(field_name))
            _arcpy.add_field(et_cells_path, field_name, ogr.OFTReal)

    # Write zonal stats to shapefile
    logging.info('\nWriting crop zonal stats')
    _arcpy.update_cursor(et_cells_path, zone_crop_dict)

    # DEADBEEF - Needed if using projected cells for computing zonal stats
    # if cleanup_flag and _arcpy.exists(zone_proj_path):
    #     _arcpy.delete(zone_proj_path)


def cell_lat_lon_func(input_path, lat_field, lon_field):
    """"""

    shp_driver = ogr.GetDriverByName('ESRI Shapefile')
    input_ds = shp_driver.Open(input_path, 1)
    input_lyr = input_ds.GetLayer()
    input_osr = input_lyr.GetSpatialRef()
    # input_osr.MorphToESRI()
    output_osr = input_osr.CloneGeogCS()
    # output_osr = osr.SpatialReference()
    # output_osr.ImportFromEPSG(4326)

    for input_ftr in input_lyr:
        input_fid = input_ftr.GetFID()
        # logging.debug('  FID: {}'.format(input_fid))
        input_geom = input_ftr.GetGeometryRef()
        # Project geometry to 4326 then extract geometry centroid
        centroid_geom = input_geom.Clone()
        centroid_geom.Transform(
            osr.CoordinateTransformation(input_osr, output_osr))
        centroid_geom = centroid_geom.Centroid()
        input_ftr.SetField(lat_field, centroid_geom.GetY())
        input_ftr.SetField(lon_field, centroid_geom.GetX())
        input_lyr.SetFeature(input_ftr)
    input_ds = None


def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='ET-Demands Zonal Stats',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--gis', nargs='?', default=os.path.join(os.getcwd(), 'gis'),
        type=lambda x: _util.is_valid_directory(parser, x),
        help='GIS workspace/folder', metavar='FOLDER')
    parser.add_argument(
        '--zone', default='huc8', metavar='', type=str,
        choices=('huc8', 'huc10', 'county','gridmet'),
        help='Zone type [{}]'.format(', '.join(['huc8', 'huc10', 'county','gridmet'])))
    parser.add_argument(
        '-y', '--year', metavar='YEAR', required=True, type=int,
        help='CDL year')
    parser.add_argument(
        '--soil', metavar='FOLDER',
        nargs='?', default=os.path.join(os.getcwd(), 'gis', 'soils'),
        type=lambda x: _util.is_valid_directory(parser, x),
        help='Common soil workspace/folder')
    parser.add_argument(
        '-o', '--overwrite', default=None, action='store_true',
        help='Overwrite existing file')
    parser.add_argument(
        '--clean', default=None, action='store_true',
        help='Remove temporary datasets')
    parser.add_argument(
        '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action="store_const", dest="loglevel")
    # parser.add_argument(
    #    '--station', nargs='?', required=True,
    #     =lambda x: _util.is_valid_file(parser, x),
    #     ='Weather station shapefile', metavar='FILE')
    args = parser.parse_args()

    # Convert relative paths to absolute paths
    if args.gis and os.path.isdir(os.path.abspath(args.gis)):
        args.gis = os.path.abspath(args.gis)
    # if args.station and os.path.isfile(os.path.abspath(args.station)):
    #     .station = os.path.abspath(args.station)
    if args.soil and os.path.isdir(os.path.abspath(args.soil)):
        args.soil = os.path.abspath(args.soil)
    return args


if __name__ == '__main__':
    args = arg_parse()

    logging.basicConfig(level=args.loglevel, format='%(message)s')
    logging.info('\n{}'.format('#' * 80))
    logging.info('{0:<20s} {1}'.format(
        'Run Time Stamp:', dt.datetime.now().isoformat(' ')))
    logging.info('{0:<20s} {1}'.format('Current Directory:', os.getcwd()))
    logging.info('{0:<20s} {1}'.format(
        'Script:', os.path.basename(sys.argv[0])))

    main(gis_ws=args.gis, input_soil_ws=args.soil,
         cdl_year=args.year, zone_type=args.zone,
         overwrite_flag=args.overwrite, cleanup_flag=args.clean)
