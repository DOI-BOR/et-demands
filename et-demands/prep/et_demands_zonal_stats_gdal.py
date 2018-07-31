#--------------------------------
# Name:         et_demands_zonal_stats_gdal.py
# Purpose:      Calculate zonal stats for all rasters
#--------------------------------

import argparse
from collections import defaultdict
import datetime as dt
import logging
import os
import sys
import time

from osgeo import gdal, ogr, osr
import pandas as pd
import numpy as np
import rasterstats

import _arcpy
import _gdal_common as gdc
import _util as util


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
        # zone_id_field = 'FIPSCO'
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

    # station_id_field = 'NLDAS_ID'

    et_cells_path = os.path.join(gis_ws, 'ETCells.shp')
    # if gdb_flag:
    #     _path = os.path.join(
    #        os.path.dirname(gis_ws), 'et-demands_py\et_demands.gdb')
    #     _cells_path = os.path.join(gdb_path, 'et_cells')
    # else:
    #     _cells_path = os.path.join(gis_ws, 'ETCells.shp')

    cdl_ws = os.path.join(gis_ws, 'cdl')
    soil_ws = os.path.join(gis_ws, 'soils')
    zone_ws = os.path.dirname(zone_path)

    agland_path = os.path.join(
        cdl_ws, 'agland_{}_30m_cdls.img'.format(cdl_year))
    agmask_path = os.path.join(
        cdl_ws, 'agmask_{}_30m_cdls.img'.format(cdl_year))

    # Field names
    cell_lat_field = 'LAT'
    cell_lon_field = 'LON'
    cell_id_field = 'CELL_ID'
    cell_name_field = 'CELL_NAME'
    met_id_field = 'STATION_ID'
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

    # Output names/paths
    zone_proj_name = 'zone_proj.shp'
    zone_raster_name = 'zone_raster.img'
    table_ws = os.path.join(gis_ws, 'zone_tables')

    #
    snap_raster = os.path.join(cdl_ws, '{}_30m_cdls.img'.format(cdl_year))
    # snap_cs = 30
    sqm_2_acres = 0.000247105381        # From google

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

    # REMOVE LATER AFTER TESTING ABOVE
    # Link ET demands crop number (1-84) with CDL values (1-255)
    # Key is CDL number, value is crop number, comment is CDL class name
    # crop_num_dict = dict()
    # crop_num_dict[1] = [7]     # Corn -> Field Corn
    # crop_num_dict[2] = [58]    # Cotton -> Cotton
    # crop_num_dict[3] = [65]    # Rice -> Rice
    # crop_num_dict[4] = [60]    # Sorghum -> Sorghum
    # crop_num_dict[5] = [66]    # Soybeans -> Soybeans
    # crop_num_dict[6] = [36]    # Sunflower -> Sunflower -irrigated
    # crop_num_dict[10] = [67]   ## Peanuts -> Peanuts
    # crop_num_dict[11] = [36]   ## Tobacco -> Sunflower -irrigated
    # crop_num_dict[12] = [9]    # Sweet Corn -> Sweet Corn Early Plant
    # crop_num_dict[13] = [7]     # Pop or Orn Corn -> Field Corn
    # crop_num_dict[14] = [33]    # Mint -> Mint
    # crop_num_dict[21] = [11]    # Barley -> Spring Grain - irrigated
    # crop_num_dict[22] = [11]    # Durum Wheat -> Spring Grain - irrigated
    # crop_num_dict[23] = [11]    # Spring Wheat -> Spring Grain - irrigated
    # crop_num_dict[24] = [13]    # Winter Wheat -> Winter Grain - irrigated
    # crop_num_dict[25] = [11]    # Other Small Grains -> Spring Grain - irrigated
    # crop_num_dict[26] = [13, 85]    # Dbl Crop WinWht/Soybeans -> Soybeans After Another Crop
    # crop_num_dict[27] = [11]    # Rye -> Spring Grain - irrigated
    # crop_num_dict[28] = [11]    # Oats -> Spring Grain - irrigated
    # crop_num_dict[29] = [68]    # Millet -> Millet
    # crop_num_dict[30] = [11]    # Speltz -> Spring Grain - irrigated
    # crop_num_dict[31] = [40]    # Canola -> Canola
    # crop_num_dict[32] = [11]    # Flaxseed -> Spring Grain - irrigated
    # crop_num_dict[33] = [38]    # Safflower -> Safflower -irrigated
    # crop_num_dict[34] = [41]    # Rape Seed -> Mustard
    # crop_num_dict[35] = [41]    # Mustard -> Mustard
    # crop_num_dict[36] = [3]     # Alfalfa -> Alfalfa - Beef Style
    # crop_num_dict[37] = [4]     # Other Hay/Non Alfalfa -> Grass Hay
    # crop_num_dict[38] = [41]    # Camelina -> Mustard
    # crop_num_dict[39] = [41]    # Buckwheat -> Mustard
    # crop_num_dict[41] = [31]    # Sugarbeets -> Sugar beets
    # crop_num_dict[42] = [5]     # Dry Beans -> Snap and Dry Beans - fresh
    # crop_num_dict[43] = [30]    # Potatoes -> Potatoes
    # crop_num_dict[44] = [11]    # Other Crops -> Spring Grain - irrigated
    # crop_num_dict[45] = [76]    # Sugarcane -> Sugarcane
    # crop_num_dict[46] = [30]    # Sweet Potatoes -> Potatoes
    # crop_num_dict[47] = [21]    # Misc Vegs & Fruits -> Garden Vegetables  - general
    # crop_num_dict[48] = [24]    # Watermelons -> Melons
    # crop_num_dict[49] = [23]    # Onions -> Onions
    # crop_num_dict[50] = [21]    # Cucumbers -> Garden Vegetables  - general
    # crop_num_dict[51] = [5]     # Chick Peas -> Snap and Dry Beans - fresh
    # crop_num_dict[52] = [5]     # Lentils -> Snap and Dry Beans - fresh
    # crop_num_dict[53] = [27]    # Peas -> Peas--fresh
    # crop_num_dict[54] = [69]    # Tomatoes -> Tomatoes
    # crop_num_dict[55] = [75]    # Caneberries -> Cranberries
    # crop_num_dict[56] = [32]    # Hops -> Hops
    # crop_num_dict[57] = [21]    # Herbs -> Garden Vegetables  - general
    # crop_num_dict[58] = [41]    # Clover/Wildflowers -> Mustard
    # crop_num_dict[59] = [17]    # Sod/Grass Seed -> Grass - Turf (lawns) -irrigated
    # crop_num_dict[60] = [81]    # Switchgrass -> Sudan
    # crop_num_dict[66] = [19]    # Cherries -> Orchards - Apples and Cherries w/ground cover
    # crop_num_dict[67] = [19]    # Peaches -> Orchards - Apples and Cherries w/ground cover
    # crop_num_dict[68] = [19]    # Apples -> Orchards - Apples and Cherries w/ground cover
    # crop_num_dict[69] = [25]    # Grapes -> Grapes
    # crop_num_dict[70] = [82]    # Christmas Trees -> Christmas Trees
    # crop_num_dict[71] = [19]    # Other Tree Crops -> Orchards - Apples and Cherries w/ground cover
    # crop_num_dict[72] = [70]    # Citrus -> Oranges
    # crop_num_dict[74] = [74]    # Pecans -> Nuts
    # crop_num_dict[75] = [74]    # Almonds -> Nuts
    # crop_num_dict[76] = [74]    # Walnuts -> Nuts
    # crop_num_dict[77] = [19]    # Pears -> Orchards - Apples and Cherries w/ground cover
    # crop_num_dict[176] = [15]    # Grassland/Pasture -> Grass Pasture - high management
    # crop_num_dict[204] = [74]    # Pistachios -> Nuts
    # crop_num_dict[205] = [11]    # Triticale -> Spring Grain - irrigated
    # crop_num_dict[206] = [22]    # Carrots -> Carrots
    # crop_num_dict[207] = [21]    # Asparagus -> Aparagus
    # crop_num_dict[208] = [43]    # Garlic -> Garlic
    # crop_num_dict[209] = [24]    # Cantaloupes -> Melons
    # crop_num_dict[210] = [19]    # Prunes -> Orchards - Apples and Cherries w/ground cover
    # crop_num_dict[211] = [61]    # Olives -> Olives
    # crop_num_dict[212] = [70]    # Oranges -> Oranges
    # crop_num_dict[213] = [24]    # Honeydew Melons -> Melons
    # crop_num_dict[214] = [21]    # Broccoli -> Garden Vegetables  - general
    # crop_num_dict[216] = [59]    # Peppers -> Peppers
    # crop_num_dict[217] = [19]    # Pomegranates -> Orchards - Apples and Cherries w/ground cover
    # crop_num_dict[218] = [19]    # Nectarines -> Orchards - Apples and Cherries w/ground cover
    # crop_num_dict[219] = [21]    # Greens -> Garden Vegetables  - general
    # crop_num_dict[220] = [19]    # Plums -> Orchards - Apples and Cherries w/ground cover
    # crop_num_dict[221] = [62]    # Strawberries -> Strawberries
    # crop_num_dict[222] = [21]    # Squash -> Garden Vegetables  - general
    # crop_num_dict[223] = [19]    # Apricots -> Orchards - Apples and Cherries w/ground cover
    # crop_num_dict[224] = [6]     # Vetch -> Snap and Dry Beans - seed
    # crop_num_dict[225] = [77]    # Dbl Crop WinWht/Corn -> Field Corn After Another Crop
    # crop_num_dict[226] = [77]    # Dbl Crop Oats/Corn -> Field Corn After Another Crop
    # crop_num_dict[227] = [71]    # Lettuce -> Lettuce (Single Crop)
    # crop_num_dict[229] = [21]    # Pumpkins -> Garden Vegetables  - general
    # crop_num_dict[230] = [71, 84]    # Dbl Crop Lettuce/Durum Wht -> Grain After Another Crop
    # crop_num_dict[231] = [71, 83]    # Dbl Crop Lettuce/Cantaloupe -> Melons After Another Crop
    # crop_num_dict[232] = [71, 79]    # Dbl Crop Lettuce/Cotton -> Cotton After Another Crop
    # crop_num_dict[233] = [71, 84]    # Dbl Crop Lettuce/Barley -> Grain After Another Crop
    # crop_num_dict[234] = [71, 78]    # Dbl Crop Durum Wht/Sorghum -> Sorghum After Another Crop
    # crop_num_dict[235] = [71, 78]    # Dbl Crop Barley/Sorghum -> Sorghum After Another Crop
    # crop_num_dict[236] = [13, 78]    # Dbl Crop WinWht/Sorghum -> Sorghum After Another Crop
    # crop_num_dict[237] = [11, 77]    # Dbl Crop Barley/Corn -> Field Corn After Another Crop
    # crop_num_dict[238] = [13, 79]    # Dbl Crop WinWht/Cotton -> Cotton After Another Crop
    # crop_num_dict[239] = [66, 79]    # Dbl Crop Soybeans/Cotton -> Cotton After Another Crop
    # crop_num_dict[240] = [66, 84]    # Dbl Crop Soybeans/Oats -> Grain After Another Crop
    # crop_num_dict[241] = [7, 85]    # Dbl Crop Corn/Soybeans -> Soybeans After Another Crop
    # crop_num_dict[242] = [63]    # Blueberries -> Blueberries
    # crop_num_dict[243] = [80]    # Cabbage -> Cabbage
    # crop_num_dict[244] = [21]    # Cauliflower -> Garden Vegetables  - general
    # crop_num_dict[245] = [21]    # Celery -> Garden Vegetables  - general
    # crop_num_dict[246] = [21]    # Radishes -> Garden Vegetables  - general
    # crop_num_dict[247] = [21]    # Turnips -> Garden Vegetables  - general
    # crop_num_dict[248] = [21]    # Eggplants -> Garden Vegetables  - general
    # crop_num_dict[249] = [21]    # Gourds -> Garden Vegetables  - general
    # crop_num_dict[250] = [75]    # Cranberries -> Cranberries
    # crop_num_dict[254] = [11, 85]    # Dbl Crop Barley/Soybeans -> Soybeans After Another Crop
    # crop_num_dict[99] = [20]    #Empty CDL Placeholder for Orchards without Cover
    # crop_num_dict[98] = [86]    #Empty CDL Placeholder for AgriMet based "Grass Pasture- Mid Management"
    # crop_num_dict[97] = [16]    #Empty CDL Placeholder for "Grass Pasture- Low Management"

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

    # Build output table folder if necessary
    if not os.path.isdir(table_ws):
        os.makedirs(table_ws)
    # if gdb_flag and not os.path.isdir(os.path.dirname(gdb_path)):
    #     os.makedirs(os.path.dirname(gdb_path))

    # Remove existing data if overwrite
    # if overwrite_flag and _arcpy.exists(et_cells_path):
    #     _arcpy.delete(et_cells_path)
    # if overwrite_flag and gdb_flag and _arcpy.exists(gdb_path):
    #     shutil.rmtree(gdb_path)

    # # Build output geodatabase if necessary
    # if gdb_flag and not _arcpy.exists(gdb_path):
    #     arcpy.CreateFileGDB_management(
    #         os.path.dirname(gdb_path), os.path.basename(gdb_path))

    raster_list = [
        [awc_field, 'mean', os.path.join(input_soil_ws, 'AWC_30m_albers.img')],
        [clay_field, 'mean', os.path.join(input_soil_ws, 'CLAY_30m_albers.img')],
        [sand_field, 'mean', os.path.join(input_soil_ws, 'SAND_30m_albers.img')],
        ['AG_COUNT', 'sum', agmask_path],
        ['AG_ACRES', 'sum', agmask_path],
        ['AG_' + awc_field, 'mean', os.path.join(
            soil_ws, 'AWC_{}_30m_cdls.img'.format(cdl_year))],
        ['AG_' + clay_field, 'mean', os.path.join(
            soil_ws, 'CLAY_{}_30m_cdls.img'.format(cdl_year))],
        ['AG_' + sand_field, 'mean', os.path.join(
            soil_ws, 'SAND_{}_30m_cdls.img'.format(cdl_year))]
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

    # Join the stations to the zones and read in the matches
    # if not _arcpy.exists(et_cells_path):
    #     zone_field_list = _arcpy.list_fields(zone_path)
    #     zone_field_list.append(met_id_field)
    #     zone_field_list.append('OBJECTID_1')
    #     arcpy.SpatialJoin_analysis(zone_path, station_path, et_cells_path)
    #     # arcpy.SpatialJoin_analysis(station_path, zone_path, et_cells_path)
    #     delete_field_list = [f for f in _arcpy.list_fields(et_cells_path)
    #                          if f not in zone_field_list]
    #     logging.info('Deleting Fields')
    #     if field_name in delete_field_list:
    #         logging.debug('  {}'.format(field_name))
    #         try: _arcpy.delete_field(et_cells_path, field_name)
    #         except: pass

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
        lat_lon_flag = True
    if cell_lon_field not in field_list:
        logging.debug('  {}'.format(cell_lon_field))
        _arcpy.add_field(et_cells_path, cell_lon_field, ogr.OFTReal)
        lat_lon_flag = True
    # Cell/station ID
    if cell_id_field not in field_list:
        logging.debug('  {}'.format(cell_id_field))
        _arcpy.add_field(et_cells_path, cell_id_field, ogr.OFTString, width=24)
    if cell_name_field not in field_list:
        logging.debug('  {}'.format(cell_name_field))
        _arcpy.add_field(et_cells_path, cell_name_field, ogr.OFTString, width=48)
    if met_id_field not in field_list:
        logging.debug('  {}'.format(met_id_field))
        _arcpy.add_field(et_cells_path, met_id_field, ogr.OFTString, width=24)
    if zone_id_field not in field_list:
        logging.debug('  {}'.format(zone_id_field))
        _arcpy.add_field(et_cells_path, zone_id_field, ogr.OFTString, width=8)

    # Status flags
    # if active_flag_field not in field_list:
    #     logging.debug('  {}'.format(active_flag_field))
    #     _arcpy.add_field(et_cells_path, active_flag_field, OFTInteger)
    # if irrig_flag_field not in field_list:
    #     logging.debug('  {}'.format(irrig_flag_field))
    #     _arcpy.add_field(et_cells_path, irrig_flag_field, OFTInteger)
    # Add zonal stats fields
    for field_name, stat, raster_path in raster_list:
        if field_name not in field_list:
            logging.debug('  {}'.format(field_name))
            _arcpy.add_field(et_cells_path, field_name, ogr.OFTReal)

    # Other soil fields
    if awc_in_ft_field not in field_list:
        logging.debug('  {}'.format(awc_in_ft_field))
        _arcpy.add_field(et_cells_path, awc_in_ft_field, ogr.OFTReal,
                         width=8, precision=4)
    if hydgrp_num_field not in field_list:
        logging.debug('  {}'.format(hydgrp_num_field))
        _arcpy.add_field(et_cells_path, hydgrp_num_field, ogr.OFTReal)
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
    cell_lat_lon_func(et_cells_path, 'LAT', 'LON')

    # Set CELL_ID and CELL_NAME
    # zone_id_field must be a string
    _arcpy.calculate_field(
        et_cells_path, cell_id_field, 'str(!{}!)'.format(zone_id_field))
    _arcpy.calculate_field(
        et_cells_path, cell_name_field,
        '"{}" + str(!{}!)'.format(zone_name_str, zone_name_field))
    # # Set MET_ID (STATION_ID) to NLDAS_ID
    # _arcpy.calculate_field(
    #     et_cells_path, met_id_field, 'str(!{}!)'.format(station_id_field))

    # Remove existing (could use overwrite instead)
    zone_proj_path = os.path.join(table_ws, zone_proj_name)
    if overwrite_flag and _arcpy.exists(zone_proj_path):
        _arcpy.delete(zone_proj_path)

    # Project zones to match CDL/snap coordinate system
    if _arcpy.exists(et_cells_path) and not _arcpy.exists(zone_proj_path):
        logging.info('Projecting zones')
        _arcpy.project(et_cells_path, zone_proj_path, snap_osr)

    # Calculate zonal stats
    # Use "rasterstats" package for computing zonal statistics
    logging.info('\nProcessing soil rasters')
    zs_dict = defaultdict(dict)
    for field_name, stat, raster_path in raster_list:
        logging.info('{} {}'.format(field_name, stat))
        logging.debug('  {}'.format(raster_path))
        logging.debug('  {}'.format(zone_proj_path))
        zs = rasterstats.zonal_stats(zone_proj_path, raster_path, stats=[stat])

        # Save by FID/feature for easier writing to shapefile
        for i, item in enumerate(zs):
            if item[stat]:
                zs_dict[i][field_name] = item[stat]
            else:
                zs_dict[i][field_name] = None

    # Write zonal stats to shapefile
    _arcpy.update_cursor(et_cells_path, zs_dict)

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
    logging.debug('  {}'.format(zone_proj_path))
    logging.debug('  {}'.format(raster_path))
    zs = rasterstats.zonal_stats(zone_proj_path, agland_path, categorical=True)

    # Save by FID/feature for easier writing to shapefile
    zone_crop_dict = {}
    crop_field_fmt = 'CROP_{:02d}'
    for i, ftr in enumerate(zs):
        zone_crop_dict[i] = {}
        for cdl_str, cdl_pixels in ftr.items():
            cdl_number = int(cdl_str)
            # Only 'crops' have a crop number (no shrub, water, urban, etc.)
            if cdl_number not in crop_num_dict.keys():
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
                if crop_field not in zone_crop_dict[i].keys():
                    zone_crop_dict[i][crop_field] = crop_acreage
                else:
                    zone_crop_dict[i][crop_field] += crop_acreage

    # Get unique crop number values and field names
    crop_field_list = sorted(list(set([
        crop_field for crop_dict in zone_crop_dict.values()
        for crop_field in crop_dict.keys()])))
    logging.debug('Crop field list: ' + ', '.join(crop_field_list))
    crop_number_list = [int(f.split('_')[-1]) for f in crop_field_list]
    logging.debug('Crop number list: ' + ', '.join(map(str, crop_number_list)))

    # Add fields for CDL values
    logging.info('Adding crop fields')
    for field_name in crop_field_list:
        if field_name not in field_list:
            logging.debug('  {}'.format(field_name))
            _arcpy.add_field(et_cells_path, field_name, ogr.OFTReal)

    # Write zonal stats to shapefile
    logging.info('Writing crop zonal stats')
    _arcpy.update_cursor(et_cells_path, zone_crop_dict)

    if cleanup_flag and _arcpy.exists(zone_proj_path):
        _arcpy.delete(zone_proj_path)


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
        logging.debug('  FID: {}'.format(input_fid))
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
        type=lambda x: util.is_valid_directory(parser, x),
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
        type=lambda x: util.is_valid_directory(parser, x),
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
    #     =lambda x: util.is_valid_file(parser, x),
    #     ='Weather station shapefile', metavar='FILE')
    # parser.add_argument(
    #    '--gdb', default=None, action='store_true',
    #     ='Write ETCells to a geodatabase')
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
