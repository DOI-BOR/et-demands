import glob
import os
import shutil

from osgeo import gdal, ogr


def add_field(input_path, field_name, field_type, field_width=None):
    """Add a new field/column

    Parameters
    ----------
    input_path : str
    field_name : str
    field_type :
        http://www.gdal.org/ogr__core_8h.html
        http://www.gdal.org/ogr__core_8h.html#a787194bea637faf12d61643124a7c9fc
    field_width : int

    """
    if is_shapefile(input_path):
        driver = ogr.GetDriverByName("ESRI Shapefile")
    else:
        raise Exception('input must be a shapefile')

    input_ds = driver.Open(input_path)
    input_lyr = input_ds.GetLayer()
    field_def = ogr.FieldDefn(field_name, field_type)
    if field_width is None and field_type in [ogr.OFTString]:
        raise ValueError('the field_width must be set for {} fields '
                         'types'.format(field_type))
    elif field_width is not None:
        field_def.SetWidth(field_width)
    input_lyr.CreateField(field_def)
    input_ds = None


def calculate_field(input_path, field_name, expr):
    """

    Parameters
    ----------
    input_path : str
    field_name : str
    expr : str

    """
    if is_shapefile(input_path):
        driver = ogr.GetDriverByName("ESRI Shapefile")
    else:
        raise Exception('input must be a shapefile')

    input_ds = driver.Open(input_path)
    input_lyr = input_ds.GetLayer()

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
    if is_shapefile(input_path):
        driver = ogr.GetDriverByName("ESRI Shapefile")
    else:
        raise Exception('input must be a shapefile')

    input_ds = driver.Open(input_path)
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


def is_shapefile(input_path):
    """

    Parameters
    ----------
    input_path

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
    Different from the ArcPy function in that it returns a list of field names
    instead of Field objects.

    """
    if is_shapefile(input_path):
        driver = ogr.GetDriverByName('ESRI Shapefile')
    else:
        raise Exception('input must be a shapefile')

    input_ds = driver.Open(input_path, 0)
    input_lyr = input_ds.GetLayer()

    fields = []
    input_field_def = input_lyr.GetLayerDefn()
    for n in range(input_field_def.GetFieldCount()):
        input_field = input_field_def.GetFieldDefn(n)
        fields.append(input_field.name)
    input_ds = None

    return fields
