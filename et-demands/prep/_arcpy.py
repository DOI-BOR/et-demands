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
    driver = get_driver(input_path)

    fields = list_fields(input_path)
    if name in fields:
        logging.debug('The field already exists')

    input_ds = driver.Open(input_path, 1)
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
    logging.debug('Calculate Field')
    driver = get_driver(input_path)

    input_fields = list_fields(input_path)

    # Extract expression fields
    expr_fields = re.findall('\!\w+\!', calc_expr)

    logging.debug('  Expression fields: {}'.format(', '.join(expr_fields)))

    input_ds = driver.Open(input_path, 1)
    input_lyr = input_ds.GetLayer()
    for input_ftr in input_lyr:
        input_fid = input_ftr.GetFID()
        logging.debug('  FID: {}'.format(input_fid))
        ftr_expr = calc_expr[:]
        logging.debug(ftr_expr)
        for f in expr_fields:
            f_value = input_ftr.GetField(f.replace('!', ''))
            logging.debug('  {} {}'.format(f, f_value))
            ftr_expr = ftr_expr.replace(f, f_value)
        logging.debug(ftr_expr)
        input_ftr.SetField(field_name, eval(ftr_expr))
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
        shp_driver = ogr.GetDriverByName('ESRI Shapefile')
        input_ds = shp_driver.Open(input_path, 0)
        output_ds = shp_driver.CopyDataSource(input_ds, output_path)
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
    driver = get_driver(input_path)

    input_ds = driver.Open(input_path, 1)
    input_lyr = input_ds.GetLayer()
    input_field_def = input_lyr.GetLayerDefn()
    for n in range(input_field_def.GetFieldCount()):
        input_field = input_field_def.GetFieldDefn(n)
        if input_field.name == field_name:
            input_lyr.DreateField(n)
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
    # elif is_raster(input_path):
    #     try:
    #         input_ds = gdal.Open(input_path)
    #     except:
    #         del input_ds
    #         return False
    else:
        raise Exception('unsupported file type')

    return True


def feature_to_raster(input_path, field, output_path, output_cs):
    """

    Parameters
    ----------
    input_path : str
    field : str
    output_path : str
    output_cs : float

    """
    input_driver = get_driver(input_path)
    input_ds = input_driver.Open(input_path)
    input_lyr = input_ds.GetLayer()
    input_osr = input_lyr.GetSpatialRef()
    # input_osr.MorphToESRI()
    input_extent = gdc.Extent(input_lyr.GetExtent())
    output_extent = input_extent.ogrenv_swap()
    # TODO: Need to adjust extent to snap geotransform also
    output_extent.adjust_to_snap('EXPAND', cs=output_cs)
    output_rows, output_cols = output_extent.shape(output_cs)

    output_driver = get_driver(output_path)
    output_ds = output_driver.Create(
        output_path, output_cols, output_rows, 1, gdal.GDT_Byte)
    output_ds.SetProjection(input_osr.ExportToWkt())
    output_ds.SetGeoTransform(output_extent.geo(output_cs))
    output_band = output_ds.GetRasterBand(1)
    # TODO: Need a nodata value
    # output_band.Fill(nodata_value)
    # output_band.SetNoDataValue(nodata_value)
    # TODO: What does burn_value need to be set to
    gdal.RasterizeLayer(
        output_ds, [1], input_lyr, burn_values=[burn_value])
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
    driver = get_driver(input_path)

    input_ds = driver.Open(input_path, 0)
    input_lyr = input_ds.GetLayer()
    count = input_lyr.GetFeatureCount()
    input_ds = None
    return count


def get_driver(input_path):
    """

    Parameters
    ----------
    input_path

    Returns
    -------


    """
    if is_shapefile(input_path):
        return ogr.GetDriverByName('ESRI Shapefile')
    elif input_path.lower().endswith('.tif'):
        return gdal.GetDriverByName('GTiff')
    elif input_path.lower().endswith('.img'):
        return gdal.GetDriverByName('HFA')
    else:
        raise Exception('input must be a .shp, .img, or .tif type')


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


def list_fields(input_path, wild_card=None):
    """

    Parameters
    ----------
    input_path : str
    wild_card : str
        Currently the wild_card must match a field name exactly.


    Returns
    -------
    list of field names

    Notes
    -----
    Different from the ArcPy function in that it returns a list of field names
    instead of Field objects.

    """
    driver = get_driver(input_path)

    input_ds = driver.Open(input_path, 0)
    input_lyr = input_ds.GetLayer()
    field_def = input_lyr.GetLayerDefn()
    fields = [
        field_def.GetFieldDefn(n).name
        for n in range(field_def.GetFieldCount())]
    input_ds = None

    if wild_card is not None:
        fields = [f for f in fields if f == wild_card]

    return fields


def project(input_path, output_path, output_osr):
    """

    Parameters
    ----------
    input_path : str
    output_path : str
    output_osr :

    """
    driver = get_driver(input_path)

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