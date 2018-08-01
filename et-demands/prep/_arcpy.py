from collections import defaultdict
import glob
import logging
import os
import re
# import shutil

from osgeo import gdal, ogr, osr

import _gdal_common as gdc


def add_field(input_path, name, type, width=None, precision=None):
    """Add a new field/column

    Parameters
    ----------
    input_path : str
    field_name : str
    field_type : int
    field_width : int

    Notes
    -----
    Field type details:
    http://www.gdal.org/ogr__core_8h.html
    http://www.gdal.org/ogr__core_8h.html#a787194bea637faf12d61643124a7c9fc

    """
    input_driver = get_ogr_driver(input_path)

    fields = list_fields(input_path)
    if name in fields:
        logging.debug('The field already exists')

    input_ds = input_driver.Open(input_path, 1)
    input_lyr = input_ds.GetLayer()

    field = ogr.FieldDefn(name, type)
    if width is not None:
        field.SetWidth(width)
    if precision is not None:
        field.SetPrecision(precision)

    # if field_width is None and field_type in [ogr.OFTString]:
    #     raise ValueError('the field_width must be set for {} fields '
    #                      'types'.format(field_type))
    # elif field_width is not None:
    #     field_def.SetWidth(field_width)

    input_lyr.CreateField(field)
    input_ds = None


def calculate_field(input_path, field_name, calc_expr):
    """

    Parameters
    ----------
    input_path : str
    field_name : str
    expr : str

    """
    input_driver = get_ogr_driver(input_path)
    # input_fields = list_fields(input_path)

    # Extract expression fields
    expr_fields = re.findall('\!\w+\!', calc_expr)

    input_ds = input_driver.Open(input_path, 1)
    input_lyr = input_ds.GetLayer()
    for input_ftr in input_lyr:
        input_fid = input_ftr.GetFID()
        # logging.debug('  FID: {}'.format(input_fid))
        ftr_expr = calc_expr[:]
        for f in expr_fields:
            f_value = input_ftr.GetField(f.replace('!', ''))
            try:
                ftr_expr = ftr_expr.replace(f, str(f_value))
            except Exception as e:
                logging.info('Error building calculate field expression')
                logging.info('  {}'.format(e))
                logging.info('  {}'.format(calc_expr))
                logging.info('  {}'.format(ftr_expr))
        try:
            input_ftr.SetField(field_name, eval(ftr_expr))
        except Exception as e:
            logging.info('Error writing calculate field value')
            logging.info('  {}'.format(e))
            logging.info('  {}'.format(calc_expr))
            logging.info('  {}'.format(ftr_expr))
        input_lyr.SetFeature(input_ftr)

    input_ds = None


def copy(input_path, output_path):
    """

    Parameters
    ----------
    input_path : str
    output_path : str

    """
    if is_shapefile(input_path):
        input_driver = ogr.GetDriverByName('ESRI Shapefile')
        input_ds = input_driver.Open(input_path, 0)
        output_ds = input_driver.CopyDataSource(input_ds, output_path)
        output_ds, input_ds = None, None

    # # Brute force approach for copying a file and all sidecars
    # input_ws = os.path.dirname(input_path)
    # input_name = os.path.splitext(input_path)[0]
    # output_name = os.path.splitext(output_path)[0]
    # for file_name in glob.glob(input_name + ".*"):
    #     shutil.copyfile(
    #         os.path.join(input_ws, file_name),
    #         os.path.join(input_ws, file_name.replace(input_name, output_name)))


def delete(input_path):
    """Remove a shapefile/raster and all of its ancillary files

    Parameters
    ----------
    input_path : str
        File path of a dataset, shapefile, or file to be deleted.

    """
    file_ws = os.path.dirname(input_path)
    for file_name in glob.glob(os.path.splitext(input_path)[0] + ".*"):
        # logging.debug('Remove: {}'.format(os.path.join(file_ws, file_name)))
        os.remove(os.path.join(file_ws, file_name))

    # if is_shp(input_path):
    #     driver = ogr.GetDriverByName("ESRI Shapefile")
    #     if os.path.exists(dataset):
    #         driver.DeleteDataSource(dataset)


def delete_field(input_path, field_name):
    """Delete a field/column

    Parameters
    ----------
    input_path : str
    field_name : str

    """
    input_driver = get_ogr_driver(input_path)
    input_ds = input_driver.Open(input_path, 1)
    input_lyr = input_ds.GetLayer()
    input_field_def = input_lyr.GetLayerDefn()
    for n in range(input_field_def.GetFieldCount()):
        if field_name == input_field_def.GetFieldDefn(n).name:
            input_lyr.DeleteField(n)
            break
    input_ds = None


def exists(input_path):
    """Mimic ArcPy Exists function

    Parameters
    ----------
    input_path : str

    Returns
    -------
    bool

    """
    if not os.path.isfile(input_path):
        return False
    elif is_shapefile(input_path):
        shp_driver = ogr.GetDriverByName('ESRI Shapefile')
        try:
            input_ds = shp_driver.Open(input_path, 0)
        except:
            del input_ds
            return False
    elif os.path.splitext(input_path.lower())[-1] in ['.img', '.tif']:
        try:
            input_ds = gdal.Open(input_path)
        except:
            del input_ds
            return False
    else:
        raise Exception('unsupported file type')

    return True


def feature_to_raster(input_path, input_field, output_path, output_geo):
    """

    Parameters
    ----------
    input_path : str
    field : str
    output_path : str
    output_geo : tuple, list

    """
    logging.debug('Feature to Raster')
    logging.debug('  {}'.format(input_path))
    logging.debug('  {}'.format(input_field))
    logging.debug('  {}'.format(output_path))
    input_driver = get_ogr_driver(input_path)
    input_ds = input_driver.Open(input_path)
    input_lyr = input_ds.GetLayer()
    input_count = input_lyr.GetFeatureCount()
    input_osr = input_lyr.GetSpatialRef()
    # input_osr.MorphToESRI()
    input_extent = gdc.Extent(input_lyr.GetExtent())
    output_extent = input_extent.ogrenv_swap()
    output_cs = output_geo[1]
    output_extent.adjust_to_snap(snap_x=output_geo[0], snap_y=output_geo[3],
                                 cs=output_cs, method='EXPAND', )
    output_rows, output_cols = output_extent.shape(output_cs)
    if input_count < 255:
        output_gtype = gdal.GDT_Byte
        output_nodata = 255
    elif input_count < 65535:
        output_gtype = gdal.GDT_UInt16
        output_nodata = 65535
    # elif input_count < 4294967295:
    else:
        output_gtype = gdal.GDT_UInt32
        output_nodata = 4294967295

    output_driver = get_ogr_driver(output_path)
    output_ds = output_driver.Create(output_path, output_cols, output_rows, 1,
                                     output_gtype)
    output_ds.SetProjection(input_osr.ExportToWkt())
    output_ds.SetGeoTransform(output_extent.geo(output_cs))
    output_band = output_ds.GetRasterBand(1)
    output_band.Fill(output_nodata)
    output_band.SetNoDataValue(output_nodata)
    gdal.RasterizeLayer(output_ds, [1], input_lyr, burn_values=[1])
    input_ds = None
    output_ds = None


def get_count(input_path):
    """

    Parameters
    ----------
    input_path : str

    Returns
    -------
    int

    """
    input_driver = get_ogr_driver(input_path)
    input_ds = input_driver.Open(input_path, 0)
    input_lyr = input_ds.GetLayer()
    count = input_lyr.GetFeatureCount()
    input_ds = None
    return count


def get_ogr_driver(input_path):
    """

    Parameters
    ----------
    input_path

    Returns
    -------
    ogr.Driver

    Notes
    -----
    Eventually try and support reading ESRI GeoDatabases

    """
    if is_shapefile(input_path):
        return ogr.GetDriverByName('ESRI Shapefile')
    else:
        raise Exception('input must be a .shp type')


def get_gdal_driver(input_path):
    """

    Parameters
    ----------
    input_path

    Returns
    -------
    gdal.Driver

    """
    if input_path.lower().endswith('.tif'):
        return gdal.GetDriverByName('GTiff')
    elif input_path.lower().endswith('.img'):
        return gdal.GetDriverByName('HFA')
    else:
        raise Exception('input must be a .img or .tif type')


def is_shapefile(input_path):
    """

    Parameters
    ----------
    input_path : str

    Returns
    -------
    bool

    """
    if input_path.lower().endswith('.shp'):
        return True
    else:
        return False


def list_fields(input_path):
    """

    Parameters
    ----------
    input_path : str

    Returns
    -------
    list of field names

    Notes
    -----
    Different from the ArcPy function:
    * Returns field names instead of field objects.
    * Does not currently accept a wildcard parameter to filter the list.
    * Does not return the geometry field.

    """
    driver = get_ogr_driver(input_path)
    input_ds = driver.Open(input_path, 0)
    input_lyr = input_ds.GetLayer()
    field_def = input_lyr.GetLayerDefn()
    # for n in range(field_def.GetFieldCount()):
    #     print(dir(field_def.GetFieldDefn(n)))
    #     print(field_def.GetFieldDefn(n).name)
    #     print(field_def.GetFieldDefn(n).type)
    #     print(field_def.GetFieldDefn(n).width)
    #     print(field_def.GetFieldDefn(n).precision)
    #     input('ENTER')
    # input('ENTER')
    fields = [
        field_def.GetFieldDefn(n).name
        for n in range(field_def.GetFieldCount())
    ]
    input_ds = None

    return fields


def project(input_path, output_path, output_osr):
    """Project a feature dataset to a new projection

    Parameters
    ----------
    input_path : str
    output_path : str
    output_osr :

    """
    driver = get_ogr_driver(input_path)

    # First make a copy of the dataset
    input_ds = driver.Open(input_path, 0)
    input_lyr = input_ds.GetLayer()
    input_osr = input_lyr.GetSpatialRef()
    # input_osr.MorphToESRI()
    output_ds = driver.CopyDataSource(input_ds, output_path)
    output_ds = None
    input_ds = None

    # Project the geometry of each feature
    output_ds = driver.Open(input_path, 1)
    output_lyr = output_ds.GetLayer()
    for output_ftr in output_lyr:
        output_fid = output_ftr.GetFID()
        logging.debug('  FID: {}'.format(output_fid))
        output_geom = output_ftr.GetGeometryRef()
        output_geom.Transform(
            osr.CoordinateTransformation(input_osr, output_osr))
        output_ftr.SetGeometry(output_geom)
        input_lyr.SetFeature(output_ftr)
    output_ds = None


def search_cursor(input_path, fields):
    """Mimic arcpy.da.SearchCursor() function

    Parameters
    ----------
    input_path : str
    fields : list

    Returns
    -------
    dict : values[fid][field]

    """
    input_driver = get_ogr_driver(input_path)
    input_ds = input_driver.Open(input_path, 0)
    input_lyr = input_ds.GetLayer()
    values = defaultdict(dict)
    for input_ftr in input_lyr:
        input_fid = input_ftr.GetFID()
        # logging.debug('  FID: {}'.format(input_fid))
        for f in fields:
            i = input_ftr.GetFieldIndex(f)
            values[input_fid][f] = input_ftr.GetField(i)

    input_ds = None
    return values


def update_cursor(output_path, values):
    """Mimic arcpy.da.UpdateCursor() function

    Parameters
    ----------
    output_path : str
    values : dict
        values[fid][field]

    """
    output_driver = get_ogr_driver(output_path)
    output_ds = output_driver.Open(output_path, 1)
    output_lyr = output_ds.GetLayer()
    for output_ftr in output_lyr:
        output_fid = output_ftr.GetFID()
        # logging.debug('  FID: {}'.format(output_fid))
        for k, v in values[output_fid].items():
            output_ftr.SetField(k, v)
        output_lyr.SetFeature(output_ftr)

    output_ds = None
