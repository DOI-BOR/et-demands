#--------------------------------
# Name:         download_cdl_raster.py
# Purpose:      Download and extract national CDL
#--------------------------------

import argparse
import datetime as dt
import logging
import os
import sys
import zipfile

import _util as util


def main(cdl_ws, cdl_year='', overwrite_flag=False):
    """Download and extract CONUS CDL

    Args:
        cdl_ws (str): Folder/workspace path of the GIS data for the project
        cdl_year (str): Comma separated list and/or range of years
        overwrite_flag (bool): If True, overwrite existing files

    """
    logging.info('\nDownload and extract CONUS CDL rasters')
    site_url = 'ftp.nass.usda.gov'
    site_folder = 'download/res'

    cdl_format = '{}_30m_cdls.{}'

    for cdl_year in list(util.parse_int_set(cdl_year)):
        logging.info('Year: {}'.format(cdl_year))
        zip_name = cdl_format.format(cdl_year, 'zip')
        zip_url = '/'.join([site_url, site_folder, zip_name])
        zip_path = os.path.join(cdl_ws, zip_name)

        cdl_path = os.path.join(cdl_ws, cdl_format.format(cdl_year, 'img'))
        if not os.path.isdir(cdl_ws):
            os.makedirs(cdl_ws)

        if os.path.isfile(cdl_path) and not overwrite_flag:
            logging.info('\nCDL raster already exists, skipping')
            continue

        if not os.path.isfile(zip_path) or overwrite_flag:
            logging.info('\nDownload CDL files')
            logging.debug('  {}'.format(zip_url))
            logging.debug('  {}'.format(zip_path))
            util.ftp_download(site_url, site_folder, zip_name, zip_path)
        else:
            logging.info('\nCDL raster already downloaded')

        if os.path.isfile(zip_path):
            logging.info('\nExtracting CDL files')
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(cdl_ws)
        else:
            logging.info('\nCDL zip does not exist')


def arg_parse():
    """"""
    parser = argparse.ArgumentParser(
        description='Download CDL raster',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--cdl', metavar='FOLDER', required=True,
        # type=lambda x: util.is_valid_directory(parser, x),
        help='Common CDL workspace/folder')
    parser.add_argument(
        '-y', '--years', metavar='YEAR', required=True,
        help='Years, comma separate list and/or range')
    parser.add_argument(
        '-o', '--overwrite', default=None, action="store_true",
        help='Force overwrite of existing files')
    parser.add_argument(
        '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action="store_const", dest="loglevel")
    args = parser.parse_args()

    # Convert CDL folder to an absolute path
    if args.cdl and os.path.isdir(os.path.abspath(args.cdl)):
        args.cdl = os.path.abspath(args.cdl)
    return args


if __name__ == '__main__':
    args = arg_parse()

    logging.basicConfig(level=args.loglevel, format='%(message)s')
    logging.info('\n{0}'.format('#' * 80))
    logging.info('{0:<20s} {1}'.format(
        'Run Time Stamp:', dt.datetime.now().isoformat(' ')))
    logging.info('{0:<20s} {1}'.format('Current Directory:', os.getcwd()))
    logging.info('{0:<20s} {1}'.format(
        'Script:', os.path.basename(sys.argv[0])))

    main(cdl_ws=args.cdl, cdl_year=args.years, overwrite_flag=args.overwrite)
