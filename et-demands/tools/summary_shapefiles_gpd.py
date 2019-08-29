import argparse
import datetime as dt
import geopandas as gpd
import logging
import numpy as np
import os
import pandas as pd
import re
import sys

# Eventually rename util.py to _util.py
import util as util

def main(ini_path, time_filter, start_doy, end_doy, year_filter=''):

    """Create Median NIWR Shapefiles from annual_stat files

    Args:
        ini_path (str): file path of the project INI file
        year_filter (list): only include certain years for summary
            (single YYYY or range YYYY:YYYY)
        time_filter (str): 'annual', 'growing_season', 'doy'
        start_doy (int): starting julian doy (inclusive)
        end_doy (int): ending julian doy (inclusive)
    Returns:
        None
    """
    #  INI path
    config = util.read_ini(ini_path, section='CROP_ET')
    try:
        project_ws = config.get('CROP_ET', 'project_folder')
    except:
        logging.error(
            'project_folder parameter must be set in the INI file, exiting')
        return False
    try:
        gis_ws = config.get('CROP_ET', 'gis_folder')
    except:
        logging.error(
            'gis_folder parameter must be set in the INI file, exiting')
        return False
    try:
        et_cells_path = config.get('CROP_ET', 'cells_path')
    except:
        logging.error(
            'et_cells_path parameter must be set in the INI file, exiting')
        return False

    try:
        daily_output_path = config.get('CROP_ET', 'daily_output_folder')
    except:
        logging.error(
            'ERROR: daily_output_folder ' +
            'parameter is not set inINI file')
        sys.exit()

    try:
        etref_field = config.get('REFET', 'etref_field')
    except:
        logging.error(
            'etref_field parameter must be set in the INI file, exiting')
        return False
    
    # Year Filter
    year_list = None
    if year_filter:
        try:
            year_list= sorted(list(util.parse_int_set(year_filter)))
            # logging.info('\nyear_list = {0}'.format(year_list))
        except:
            pass

    # Sub folder names
    daily_ws = os.path.join(project_ws, daily_output_path)
    output_ws = os.path.join(project_ws, 'summary_shapefiles')
    if not os.path.exists(output_ws):
        os.makedirs(output_ws)

    # Check input folders
    if not os.path.exists(daily_ws):
        logging.critical('ERROR: The daily_stat folder does not exist.'
                         ' Check .ini settings')
        sys.exit()

    # Check input folders
    if not os.path.isdir(project_ws):
        logging.critical(('ERROR: The project folder ' +
                          'does not exist\n  {}').format(project_ws))
        sys.exit()
    elif not os.path.isdir(gis_ws):
        logging.critical(('ERROR: The GIS folder ' +
                          'does not exist\n  {}').format(gis_ws))
        sys.exit()
    logging.info('\nGIS Workspace:      {0}'.format(gis_ws))

    # Regular expressions
    data_re = re.compile('(?P<CELLID>\w+)_crop_(?P<CROP>\d+).csv$', re.I)
    #data_re = re.compile('(?P<CELLID>\w+)_daily_crop_(?P<CROP>\d+).csv$', re.I)
    
    # Build list of all data files
    data_file_list = sorted(
        [os.path.join(daily_ws, f_name) for f_name in os.listdir(daily_ws)
         if data_re.match(f_name)])
    if not data_file_list:
        logging.error(
            '  ERROR: No daily files were found\n' +
            '  ERROR: Check the folder_name parameters\n')
        sys.exit()

    # Start with empty lists
    stations = []
    crop_nums = []

    # Process each file
    for file_path in data_file_list:
        file_name = os.path.basename(file_path)
        logging.debug('')
        # logging.info('  {0}'.format(file_name))

        #station, crop_num = os.path.splitext(file_name)[0].split('_daily_crop_')
        station, crop_num = os.path.splitext(file_name)[0].split('_crop_')
        stations.append(station)
        crop_num = int(crop_num)
        crop_nums.append(crop_num)

    # Find unique crops and station ids
    unique_crop_nums = list(set(crop_nums))
    unique_stations = list(set(stations))

    # Loop through each crop and station list to build summary dataframes for
    # variables to include in output (if not in .csv skip)
    var_list = ['ETact', 'ETpot', 'ETbas', 'Kc', 'Kcb',
                'PPT', 'Irrigation', 'Runoff', 'DPerc', 'NIWR', 'Season',
                'Start', 'End']
    pmet_field = 'PM{}'.format(etref_field)
    var_list.insert(0, pmet_field)
    
    # Arc fieldnames can only be 10 characters. Shorten names to include _stat
    # field name list will be based on etref_field ETr, ETo, or ET (not ETo/ETr)
    if 'ETr' in etref_field:
        var_fieldname_list = ['ETr', 'ETact', 'ETpot', 'ETbas', 'Kc',
                   'Kcb', 'PPT', 'Irr', 'Runoff', 'DPerc', 'NIWR', 'Season',
                              'Start', 'End']

    elif 'ETo' in etref_field:
        var_fieldname_list = ['ETo', 'ETact', 'ETpot', 'ETbas', 'Kc',
                   'Kcb', 'PPT', 'Irr', 'Runoff', 'DPerc', 'NIWR', 'Season',
                              'Start', 'End']

    else:
        var_fieldname_list = ['ET', 'ETact', 'ETpot', 'ETbas', 'Kc',
                   'Kcb', 'PPT', 'Irr', 'Runoff', 'DPerc', 'NIWR', 'Season',
                              'Start', 'End']


    # Testing (should this be an input option?)
    # unique_crop_nums = [86]
    # unique_stations = [608807]
    print('\nCreating summary shapefiles.')
    if year_list:
        logging.info('\nIncluding years {} to {}.'.format(min(year_list),
                                                         max(year_list)))
    # Apply Time Filter (annual, etd growing season, doy (start/end))
    if time_filter == 'annual':
        logging.info('\nIncluding January-December data.')
    if time_filter == 'growing_season':
        logging.info(
            '\nFiltering data using ETDemands defined growing season.')
    if time_filter == 'doy':
        logging.info('\nFiltering data using doy inputs. Start doy: {:03d}'
            '  End doy: {:03d}'.format(start_doy, end_doy))
    for crop in unique_crop_nums:
        print('\nProcessing Crop: {:02d}'.format(crop))

        # Initialize df variable to check if pandas df needs to be created
        output_df = None
        for station in unique_stations:
            #Build File Path
            file_path = os.path.join(daily_ws,
                                     '{}_crop_{:02d}.csv').format(station,
                                                                  crop)
            # Only process files that exists (crop/cell combinations)
            if not os.path.exists(file_path):
                continue

            # Read file into df
            daily_df = pd.read_csv(file_path, skiprows=1)
            # Add more DOY columns to simplify start/end DOY agg below
            daily_df['Start'] = daily_df.DOY.copy()
            daily_df['End'] = daily_df.DOY.copy()
            # Replace Non-growing season DOY values with nan
            daily_df.loc[daily_df.Season == 0, ['Start', 'End']] = np.nan

            # Apply Year Filter (inclusive)
            if year_list:
                daily_df = daily_df[
                    (daily_df['Year'] >= min(year_list)) &
                    (daily_df['Year'] <= max(year_list))]
                # logging.info('Including Years: {}'.format(year_list))

            # Apply Time Filter (annual, etd growing season, doy (start/end))
            if time_filter == 'growing_season':
                daily_df = daily_df[(daily_df['Season'] == 1)]
            if time_filter == 'doy':
                daily_df = daily_df[
                    (daily_df['DOY'] >= start_doy) &
                    (daily_df['DOY'] <= end_doy)]

            if daily_df.empty:
                logging.info(' Growing Season never started. Skipping cell {}'
                             ' for crop {}.'.format(station, crop))
                continue

            # Dictionary to control agg of each variable
            a = {
            'ETact': 'sum',
            'ETpot': 'sum',
            'ETbas': 'sum',
            'PPT': 'sum',
            'Irrigation': 'sum',
            'Runoff': 'sum',
            'DPerc': 'sum',
            'NIWR': 'sum',
            'Season': 'sum',
            'Start': 'min',
            'End': 'max',
            'Kc': 'mean',
            'Kcb': 'mean'}
            # Add etref_field to dictionary
            a[pmet_field] = 'sum'
            
            # GroupStats by Year of each column follow agg assignment above
            yearlygroup_df = daily_df.groupby('Year',
                                                as_index=True).agg(a)
            # Take Mean of Yearly GroupStats
            mean_df = yearlygroup_df.mean(axis=0)
            mean_fieldnames = [v + '_mn' for v in var_fieldname_list]

            # Take Median of Yearly GroupStats
            median_df = yearlygroup_df.median(axis=0)
            median_fieldnames =[v + '_mdn' for v in var_fieldname_list]

            # Create df if it doesn't exist
            if output_df is None:
                output_df = pd.DataFrame(index=unique_stations,
                                 columns=mean_fieldnames + median_fieldnames)

            # Write data to each station row
            output_df.loc[station] = list(mean_df[var_list]) + \
                              list(median_df[var_list])

            # Cast summary objects to floats
            output_df = output_df.astype(float)

            # Grab min/max year for output folder naming
            min_year = min(daily_df['Year'])
            max_year = max(daily_df['Year'])

        # Create station ID column from index (ETCells GRIDMET ID is int)
        output_df['Station'] = output_df.index.map(int)

        # Remove rows with Na (is this the best option?)
        # Write all stations to index and then remove empty
        output_df = output_df.dropna()

        # Output file name
        out_name = "{}_crop_{:02d}.shp".format(time_filter, crop)
        if time_filter == 'doy':
            out_name = "{}_{:03d}_{:03d}_crop_{:02d}.shp".format(
                time_filter, start_doy, end_doy, crop)

        # output folder
        output_folder_path = os.path.join(output_ws, 'summary_{}to{}'.format(
                                                  min_year, max_year))
        if min_year == max_year:
            output_folder_path = os.path.join(output_ws,
                                              'summary_{}'.format(
                                                  min_year))

        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)

        # Copy ETCELLS.shp and join summary data to it
        data = gpd.read_file(et_cells_path)

        # Data keep list (geometry is needed to write out as geodataframe)
        # keep_list = ['geometry','CELL_ID', 'LAT', 'LON', 'ELEV_M', 'ELEV_FT',
        #              'COUNTYNAME', 'STATENAME', 'STPO', 'HUC8',
        #              'AG_ACRES', 'CROP_{:02d}'.format(crop)]
        keep_list = ['geometry', 'CELL_ID', 'LAT', 'LON',
                     'AG_ACRES', 'CROP_{:02d}'.format(crop)]

        # Filter ETCells using keep list
        data = data[keep_list]

        # UPDATE TO NEWER ETCELLS STATION_ID FORMAT !!!!!
        merged_data = data.merge(output_df, left_on='CELL_ID',
                                 right_on='Station')
        # Remove redundant Station column
        merged_data = merged_data.drop(columns='Station')
        # Write output .shp
        merged_data.to_file(os.path.join(output_folder_path, out_name),
                            driver='ESRI Shapefile')

def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='ET-Demands Annual Stat Shapefiles',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-i', '--ini', metavar='PATH',
        type=lambda x: util.is_valid_file(parser, x), help='Input file')
    parser.add_argument(
        '-t', '--time_filter', default='annual', choices=['annual',
                                    'growing_season', 'doy'], type=str,
        help='Data coverage options. If "doy", -start_doy and'
             ' -end_doy required.')
    parser.add_argument(
        '-s', '--start_doy', type=int,
        help='Starting julian doy (inclusive)')
    parser.add_argument(
        '-e', '--end_doy', type=int,
        help='Ending julian doy (inclusive)')
    parser.add_argument(
        '-y', '--year', default='', type=str,
        help='Years to include, single year (YYYY) or range (YYYY-YYYY)')
    parser.add_argument(
        '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action="store_const", dest="loglevel")
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = arg_parse()
    if args.time_filter == 'doy' and \
            (args.start_doy is None or args.end_doy is None):
        logging.error(
            '\nstart/end doy must be input when using "doy" time filter.'
            '\nExiting.')
        sys.exit()

    logging.basicConfig(level=args.loglevel, format='%(message)s')
    logging.info('\n{}'.format('#' * 80))
    logging.info('{0:<20s} {1}'.format(
        'Run Time Stamp:', dt.datetime.now().isoformat(' ')))
    logging.info('{0:<20s} {1}'.format('Current Directory:', os.getcwd()))
    logging.info('{0:<20s} {1}'.format(
        'Script:', os.path.basename(sys.argv[0])))

    main(ini_path=args.ini, time_filter=args.time_filter,
         start_doy=args.start_doy, end_doy=args.end_doy, year_filter=args.year)
