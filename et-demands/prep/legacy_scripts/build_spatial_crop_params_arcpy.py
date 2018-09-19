#--------------------------------
# Name:         build_spatial_crop_params_arcpy.py
# Purpose:      Build spatial parameter files for ET-Demands from zonal stats ETCells
# Python:       2.7
#--------------------------------

import argparse
from collections import defaultdict
import datetime as dt
import logging
import os
import re
import sys

import arcpy

import _util as util


def main(ini_path, zone_type='huc8', area_threshold=10,
         dairy_cuttings=5, beef_cuttings=4, crop_str='',
         remove_empty_flag=True, overwrite_flag=False):
    """Build a feature class for each crop and set default crop parameters

    Apply the values in the CropParams.txt as defaults to every cell

    Args:
        ini_path (str): file path of the project INI file
        zone_type (str): Zone type (huc8, huc10, county, gridmet)
        area_threshold (float): CDL area threshold [acres]
        dairy_cuttings (int): Initial number of dairy hay cuttings
        beef_cuttings (int): Initial number of beef hay cuttings
        crop_str (str): comma separated list or range of crops to compare
        overwrite_flag (bool): If True, overwrite existing output rasters

    Returns:
        None

    """
    logging.info('\nCalculating ET-Demands Spatial Crop Parameters')

    remove_empty_flag = True

    # Input paths
    # DEADBEEF - For now, get cropET folder from INI file
    # This function may eventually be moved into the main cropET code
    crop_et_sec = 'CROP_ET'
    config = util.read_ini(ini_path, section=crop_et_sec)

    try:
        project_ws = config.get(crop_et_sec, 'project_folder')
    except:
        logging.error('project_folder parameter must be set in the INI file, '
                      'exiting')
        return False
    try:
        gis_ws = config.get(crop_et_sec, 'gis_folder')
    except:
        logging.error('gis_folder parameter must be set in the INI file, '
                      'exiting')
        return False
    try:
        cells_path = config.get(crop_et_sec, 'cells_path')
    except:
        # cells_path = os.path.join(gis_ws, 'ETCells.shp')
        logging.error('et_cells_path parameter must be set in the INI file, '
                      'exiting')
        return False
    try:
        stations_path = config.get(crop_et_sec, 'stations_path')
    except:
        logging.error('stations_path parameter must be set in the INI file, '
                      'exiting')
        return False

    crop_et_ws = config.get(crop_et_sec, 'crop_et_folder')
    bin_ws = os.path.join(crop_et_ws, 'bin')

    try:
        calibration_ws = config.get(crop_et_sec, 'spatial_cal_folder')
    except:
        calibration_ws = os.path.join(project_ws, 'calibration')

    # Sub folder names
    static_ws = os.path.join(project_ws, 'static')
    # pmdata_ws = os.path.join(project_ws, 'pmdata')
    crop_params_path = os.path.join(static_ws, 'CropParams.txt')

    # ET cells field names
    cell_id_field = 'CELL_ID'
    cell_name_field = 'CELL_NAME'
    crop_acres_field = 'CROP_ACRES'

    # Only keep the following ET Cell fields
    keep_field_list = [cell_id_field, cell_name_field, 'AG_ACRES']
    # keep_field_list = ['CELL_ID', 'STATION_ID', 'HUC8', 'HUC10', 'GRIDMET_ID,
    #                    'COUNTYNAME', 'AG_ACRES']
    # keep_field_list = ['FIPS', 'COUNTYNAME']

    # Check input folders
    if not os.path.isdir(crop_et_ws):
        logging.error('\nERROR: The INI cropET folder does not exist'
                      '\n  {}'.format(crop_et_ws))
        sys.exit()
    elif not os.path.isdir(bin_ws):
        logging.error('\nERROR: The bin workspace does not exist'
                      '\n  {}'.format(bin_ws))
        sys.exit()
    elif not os.path.isdir(project_ws):
        logging.error('\nERROR: The project folder does not exist'
                      '\n  {}'.format(project_ws))
        sys.exit()
    elif not os.path.isdir(gis_ws):
        logging.error('\nERROR: The GIS folder does not exist'
                      '\n  {}'.format(gis_ws))
        sys.exit()
    if '.gdb' not in calibration_ws and not os.path.isdir(calibration_ws):
        os.makedirs(calibration_ws)
    logging.info('\nGIS Workspace:      {}'.format(gis_ws))
    logging.info('Project Workspace:  {}'.format(project_ws))
    logging.info('CropET Workspace:   {}'.format(crop_et_ws))
    logging.info('Bin Workspace:      {}'.format(bin_ws))
    logging.info('Calib. Workspace:   {}'.format(calibration_ws))

    # Check input files
    if not os.path.isfile(crop_params_path):
        logging.error('\nERROR: The crop parameters file does not exist'
                      '\n  {}'.format(crop_params_path))
        sys.exit()
    elif not os.path.isfile(cells_path):
        logging.error('\nERROR: The ET Cell shapefile does not exist'
                      '\n  {}'.format(cells_path))
        sys.exit()
    elif not os.path.isfile(stations_path) or not arcpy.Exists(stations_path):
        logging.error('\nERROR: The weather station shapefile does not exist'
                      '\n  {}'.format(stations_path))
        sys.exit()
    logging.debug('Crop Params Path:   {}'.format(crop_params_path))
    logging.debug('ET Cells Path:      {}'.format(cells_path))
    logging.debug('Stations Path:      {}'.format(stations_path))

    # For now, only allow calibration parameters in separate shapefiles
    ext = '.shp'
    # # Build output geodatabase if necessary
    # if calibration_ws.endswith('.gdb'):
    #     logging.debug('GDB Path:           {}'.format(calibration_ws))
    #     ext = ''
    #     if arcpy.Exists(calibration_ws) and overwrite_flag:
    #         try: arcpy.Delete_management(calibration_ws)
    #         except: pass
    #     if calibration_ws is not None and not arcpy.Exists(calibration_ws):
    #         arcpy.CreateFileGDB_management(
    #             os.path.dirname(calibration_ws),
    #             os.path.basename(calibration_ws))
    # else:
    #     ext = '.shp'

    # Field Name, Property, Field Type
    # Property is the string of the CropParameter class property value
    # It will be used to access the property using getattr
    dairy_cutting_field = 'Dairy_Cut'
    beef_cutting_field = 'Beef_Cut'
    param_list = [
        # ['Name', 'name', 'STRING'],
        # ['ClassNum', 'class_number', 'LONG'],
        # ['IsAnnual', 'is_annual', 'SHORT'],
        # ['IrrigFlag', 'irrigation_flag', 'SHORT'],
        # ['IrrigDays', 'days_after_planting_irrigation', 'LONG'],
        # ['Crop_FW', 'crop_fw', 'LONG'],
        # ['WinterCov', 'winter_surface_cover_class', 'SHORT'],
        # ['CropKcMax', 'kc_max', 'FLOAT'],
        ['MAD_Init', 'mad_initial', 'LONG'],
        ['MAD_Mid', 'mad_midseason', 'LONG'],
        # ['RootDepIni', 'rooting_depth_initial', 'FLOAT'],
        # ['RootDepMax', 'rooting_depth_max', 'FLOAT'],
        # ['EndRootGrw', 'end_of_root_growth_fraction_time', 'FLOAT'],
        # ['HeightInit', 'height_initial', 'FLOAT'],
        # ['HeightMax', 'height_max', 'FLOAT'],
        # ['CurveNum', 'curve_number', 'LONG'],
        # ['CurveName', 'curve_name', 'STRING'],
        # ['CurveType', 'curve_type', 'SHORT'],
        # ['PL_GU_Flag', 'flag_for_means_to_estimate_pl_or_gu', 'SHORT'],
        ['T30_CGDD', 't30_for_pl_or_gu_or_cgdd', 'FLOAT'],
        ['PL_GU_Date', 'date_of_pl_or_gu', 'FLOAT'],
        ['CGDD_Tbase', 'tbase', 'FLOAT'],
        ['CGDD_EFC', 'cgdd_for_efc', 'LONG'],
        ['CGDD_Term', 'cgdd_for_termination', 'LONG'],
        ['Time_EFC', 'time_for_efc', 'LONG'],
        ['Time_Harv', 'time_for_harvest', 'LONG'],
        ['KillFrostC', 'killing_frost_temperature', 'FLOAT'],
        # ['InvokeStrs', 'invoke_stress', 'SHORT'],
        # ['CN_Coarse', 'cn_coarse_soil', 'LONG'],
        # ['CN_Medium', 'cn_medium_soil', 'LONG'],
        # ['CN_Fine', 'cn_fine_soil', 'LONG']
    ]
    # if calibration_ws.endswith('.gdb'):
    #     dairy_cutting_field = 'Dairy_Cuttings'
    #     beef_cutting_field = 'Beef_Cuttings'
    #     param_list  = [
    #        # ['Name', 'name', 'STRING'],
    #        # ['Class_Number', 'class_number', 'LONG'],
    #        # ['Is_Annual', 'is_annual', 'SHORT'],
    #        # ['Irrigation_Flag', 'irrigation_flag', 'SHORT'],
    #        # ['Irrigation_Days', 'days_after_planting_irrigation', 'LONG'],
    #        # ['Crop_FW', 'crop_fw', 'LONG'],
    #        # ['Winter_Cover_Class', 'winter_surface_cover_class', 'SHORT'],
    #        # ['Crop_Kc_Max', 'kc_max', 'FLOAT'],
    #        # ['MAD_Initial', 'mad_initial', 'LONG'],
    #        # ['MAD_Midseason', 'mad_midseason', 'LONG'],
    #        # ['Root_Depth_Ini', 'rooting_depth_initial', 'FLOAT'],
    #        # ['Root_Depth_Max', 'rooting_depth_max', 'FLOAT'],
    #        # ['End_Root_Growth', 'end_of_root_growth_fraction_time', 'FLOAT'],
    #        # ['Height_Initial', 'height_initial', 'FLOAT'],
    #        # ['Height_Maximum', 'height_max', 'FLOAT'],
    #        # ['Curve_Number', 'curve_number', 'LONG'],
    #        # ['Curve_Name', 'curve_name', 'STRING'],
    #        # ['Curve_Type', 'curve_type', 'SHORT'],
    #        # ['PL_GU_Flag', 'flag_for_means_to_estimate_pl_or_gu', 'SHORT'],
    #        ['T30_CGDD', 't30_for_pl_or_gu_or_cgdd', 'FLOAT'],
    #        ['PL_GU_Date', 'date_of_pl_or_gu', 'FLOAT'],
    #        ['CGDD_Tbase', 'tbase', 'FLOAT'],
    #        ['CGDD_EFC', 'cgdd_for_efc', 'LONG'],
    #        ['CGDD_Termination', 'cgdd_for_termination', 'LONG'],
    #        ['Time_EFC', 'time_for_efc', 'LONG'],
    #        ['Time_Harvest', 'time_for_harvest', 'LONG'],
    #        ['Killing_Crost_C', 'killing_frost_temperature', 'FLOAT'],
    #        # ['Invoke_Stress', 'invoke_stress', 'SHORT'],
    #        # ['CN_Coarse_Soil', 'cn_coarse_soil', 'LONG'],
    #        # ['CN_Medium_Soil', 'cn_medium_soil', 'LONG'],
    #        # ['CN_Fine_Soil', 'cn_fine_soil', 'LONG']
    #    ]

    crop_add_list = []
    if crop_str:
        try:
            crop_add_list = sorted(list(util.parse_int_set(crop_str)))
        # try:
        #     crop_test_list = sorted(list(set(
        #         crop_test_list + list(util.parse_int_set(crop_str)))
        except:
            pass
    # Don't build crop parameter files for non-crops
    crop_skip_list = sorted(list(set([44, 45, 46, 55, 56, 57])))

    # crop_test_list = sorted(list(set(crop_test_list + [46])))
    logging.info('\ncrop_add_list = {}'.format(crop_add_list))

    # Read crop parameters using ET Demands functions/methods
    logging.info('\nReading default crop parameters')
    sys.path.append(bin_ws)
    import crop_parameters
    crop_param_dict = crop_parameters.read_crop_parameters(crop_params_path)

    # arcpy.CheckOutExtension('Spatial')
    # arcpy.env.pyramid = 'NONE 0'
    arcpy.env.overwriteOutput = overwrite_flag
    arcpy.env.parallelProcessingFactor = 8


    # Get list of crops specified in ET cells
    # Currently this may only be crops with CDL acreage
    crop_field_list = [
        field.name for field in arcpy.ListFields(cells_path)
        if re.match('CROP_\d{2}', field.name)]
    logging.debug('Cell crop fields: {}'.format(', '.join(crop_field_list)))
    crop_number_list = [
        int(f_name.split('_')[-1]) for f_name in crop_field_list]

    crop_number_list = [
        crop_num for crop_num in crop_number_list
        if not (crop_skip_list and crop_num in crop_skip_list)]
    logging.info('Cell crop numbers: {}'.format(
        ', '.join(list(util.ranges(crop_number_list)))))

    # Get crop acreages for each cell
    crop_acreage_dict = defaultdict(dict)

    field_list = [cell_id_field] + crop_field_list
    with arcpy.da.SearchCursor(cells_path, field_list) as cursor:
        for row in cursor:
            for i, crop_num in enumerate(crop_number_list):
                # logging.info('{} {}'.format(crop_num, i))
                if crop_num in crop_add_list:
                    crop_acreage_dict[crop_num][row[0]] = 0
                else:
                    crop_acreage_dict[crop_num][row[0]] = row[i + 1]

    crop_number_list = sorted(list(set(crop_number_list) | set(crop_add_list)))

    # Make an empty template crop feature class
    logging.info('')
    crop_template_path = os.path.join(
        calibration_ws, 'crop_00_template' + ext)
    if overwrite_flag and arcpy.Exists(crop_template_path):
        logging.debug('Overwriting template crop feature class')
        arcpy.Delete_management(crop_template_path)
    if arcpy.Exists(crop_template_path):
        logging.info('Template crop feature class already exists, skipping')
    else:
        logging.info('Building template crop feature class')
        arcpy.CopyFeatures_management(cells_path, crop_template_path)

        # Remove unneeded et cell fields
        for field in arcpy.ListFields(crop_template_path):
            if (field.name not in keep_field_list and
                field.editable and not field.required):
                logging.debug('  Delete field: {}'.format(field.name))
                arcpy.DeleteField_management(crop_template_path, field.name)
        field_list = [f.name for f in arcpy.ListFields(crop_template_path)]

        # Add crop acreage field
        if crop_acres_field not in field_list:
            logging.debug('  Add field: {}'.format(crop_acres_field))
            arcpy.AddField_management(
                crop_template_path, crop_acres_field, 'Float')
            arcpy.CalculateField_management(
                crop_template_path, crop_acres_field, '0', 'PYTHON_9.3')

        # Add crop parameter fields if necessary
        for param_field, param_method, param_type in param_list:
            logging.debug('  Add field: {}'.format(param_field))
            if param_field not in field_list:
                arcpy.AddField_management(
                    crop_template_path, param_field, param_type)
        # if dairy_cutting_field not in field_list:
        #     logging.debug('  Add field: {}'.format(dairy_cutting_field))
        #     arcpy.AddField_management(crop_template_path, dairy_cutting_field, 'Short')
        #     arcpy.CalculateField_management(
        #          crop_template_path, dairy_cutting_field, dairy_cuttings, 'PYTHON')
        # if beef_cutting_field not in field_list:
        #     logging.debug('  Add field: {}'.format(beef_cutting_field))
        #     arcpy.AddField_management(crop_template_path, beef_cutting_field, 'Short')
        #     arcpy.CalculateField_management(
        #        crop_template_path, beef_cutting_field, beef_cuttings, 'PYTHON')

    # Add an empty/zero crop field for the field mappings below
    # if len(arcpy.ListFields(cells_path, 'CROP_EMPTY')) == 0:
    #     arcpy.AddField_management(cells_path, 'CROP_EMPTY', 'Float')
    #     arcpy.CalculateField_management(
    #        cells_path, 'CROP_EMPTY', '0', 'PYTHON_9.3')


    # Process each crop
    logging.info('\nBuilding crop feature classes')
    for crop_num in crop_number_list:
        try:
            crop_param = crop_param_dict[crop_num]
        except:
            continue
        logging.info('{:>2d} {}'.format(crop_num, crop_param.name))
        logging.debug('{}'.format(crop_param))
        # Replace other characters with spaces, then remove multiple spaces
        crop_name = re.sub('[-"().,/~]', ' ', str(crop_param.name).lower())
        crop_name = ' '.join(crop_name.strip().split()).replace(' ', '_')
        crop_path = os.path.join(calibration_ws, 'crop_{0:02d}_{1}{2}'.format(
            crop_num, crop_name, ext))
        # crop_field = 'CROP_{:02d}'.format(crop_num)

        # Don't check crops in add list
        if crop_num in crop_add_list:
            pass
        # Skip if all zone crop areas are below threshold
        elif all([v < area_threshold for v in
                  crop_acreage_dict[crop_num].values()]):
            logging.info('  All crop acreaeges below threshold, skipping crop')
            continue

        # Remove existing shapefiles if necessary
        if overwrite_flag and arcpy.Exists(crop_path):
            logging.debug('  Overwriting: {}'.format(
                os.path.basename(crop_path)))
            arcpy.Delete_management(crop_path)

        # Don't check skip list until after existing files are removed
        # if ((crop_test_list and crop_num not in crop_test_list) or
        #     _skip_list and crop_num in crop_skip_list)):
        #     .debug('  Skipping')

        # Copy ET cells for each crop if needed
        if arcpy.Exists(crop_path):
            logging.debug('  Shapefile already exists, skipping')
            continue
        else:
            # logging.debug('    {}'.format(crop_path))
            arcpy.Copy_management(crop_template_path, crop_path)
            # Remove extra fields
            # for field in arcpy.ListFields(crop_path):
            #     if field.name not in keep_field_list:
            #         # logging.debug('    {}'.format(field.name))
            #         arcpy.DeleteField_management(crop_path, field.name)

        # Add alfalfa cutting field
        if crop_num in [1, 2, 3, 4]:
            if len(arcpy.ListFields(crop_path, dairy_cutting_field)) == 0:
                logging.debug('  Add field: {}'.format(dairy_cutting_field))
                arcpy.AddField_management(
                    crop_path, dairy_cutting_field, 'Short')
                arcpy.CalculateField_management(
                    crop_path, dairy_cutting_field, dairy_cuttings, 'PYTHON')
            if len(arcpy.ListFields(crop_path, beef_cutting_field)) == 0:
                logging.debug('  Add field: {}'.format(beef_cutting_field))
                arcpy.AddField_management(
                    crop_path, beef_cutting_field, 'Short')
                arcpy.CalculateField_management(
                    crop_path, beef_cutting_field, beef_cuttings, 'PYTHON')

        # Write default crop parameters to file
        field_list = [p[0] for p in param_list] + [cell_id_field, crop_acres_field]
        with arcpy.da.UpdateCursor(crop_path, field_list) as cursor:
            for row in cursor:
                # Don't remove zero acreage crops if in add list
                if crop_num in crop_add_list:
                    pass
                # Skip and/or remove zones without crop acreage    
                elif crop_acreage_dict[crop_num][row[-2]] < area_threshold:
                    if remove_empty_flag:
                        cursor.deleteRow()
                    continue
                # Write parameter values
                for i, (param_field, param_method, param_type) in enumerate(param_list):
                    row[i] = getattr(crop_param, param_method)
                # Write crop acreage
                if crop_num not in crop_add_list:
                    row[-1] = crop_acreage_dict[crop_num][row[-2]]
                cursor.updateRow(row)

    # # Cleanup
    # # Remove the empty/zero crop field
    # arcpy.DeleteField_management(cells_path, 'CROP_EMPTY')
    # # Remove template feature class
    # arcpy.Delete_management(crop_template_path)


def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='ET-Demands Spatial Crop Parameters',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-i', '--ini', metavar='PATH',
        type=lambda x: util.is_valid_file(parser, x), help='Input file')
    parser.add_argument(
        '--zone', default='county', metavar='', type=str,
        choices=('huc8', 'huc10', 'county', 'gridmet'),
        help='Zone type [{}]'.format(
            ', '.join(['huc8', 'huc10', 'county', 'gridmet'])))
    parser.add_argument(
        '--area', default=10, type=float,
        help='Crop area threshold [acres]')
    parser.add_argument(
        '--dairy', default=5, type=int,
        help='Number of dairy hay cuttings')
    parser.add_argument(
        '--beef', default=4, type=int,
        help='Number of beef hay cuttings')
    parser.add_argument(
        '--empty', default=False, action='store_true',
        help='Remove empty features')
    parser.add_argument(
        '-c', '--crops', default='', type=str,
        help='Comma separated list or range of crops to compare')
    parser.add_argument(
        '-o', '--overwrite', default=False, action='store_true',
        help='Overwrite existing file')
    parser.add_argument(
        '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action="store_const", dest="loglevel")
    args = parser.parse_args()
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

    main(ini_path=args.ini, zone_type=args.zone, area_threshold=args.area,
         dairy_cuttings=args.dairy, beef_cuttings=args.beef,
         remove_empty_flag=args.empty, crop_str=args.crops,
         overwrite_flag=args.overwrite)
