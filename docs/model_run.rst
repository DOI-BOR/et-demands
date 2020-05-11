Running the Model
=================

RefET
-----

CropETPrep
----------
The CropET Prep workflow is designed to help users assemble ancillary data and create static files for input and running of the CropET module. Ancillary data includes crop type and coverage data as well as soil data including available water capacity (AWC) and percent clay and sand. By default, the preperation workflow utilizes the USDA Cropland Data Layer (CDL) and the NRCS STATSGO soils dataset. Use of other crop and soil datasets is possible, but should only be implemented by advanced users. An example preperation workflow is shown below: 

Run Prep
  Scripts A1-A3 are only needed if user does not have a crop shapefile. The CDL clip script is only needed if storage space is an issue.

A1: Download CDL Raster
  python ..\..\et-demands\prep\download_cdl_raster.py --ini example_prep.ini

A2: Clip CDL Raster - Only needed to save storage space
  python ..\..\et-demands\prep\clip_cdl_raster.py --ini example_prep.ini

A3: Build CDL Shapefile
  python ..\..\et-demands\prep\build_ag_cdl_shapefile.py --ini example_prep.ini

1: Download Soils Files
  python D:\et-demands\et-demands\prep\download_statsgo_shapefiles.py --ini example_prep.ini

2: Calculate Zonal Statistics
  python D:\et-demands\et-demands\prep\et_demands_zonal_stats.py --ini example_prep.ini

NOTE: Crop Crosswalk File: prep/cdl_crosswalk_default.csv
By default, ETDemands includes a crop crosswalk file to convert CDL crop codes to their corresponding
ETDemands crop code. This file is specified using the 'crosswalk_path' variable in the prep .ini file.
When not using the USDA CDL layers, users should develop a custom crosswalk file that relates crop codes 
in their custom file to crop layer. The shapefile field name containing crop codes is also specified in the prep_ini. 

3: Build Static Files
  python D:\et-demands\et-demands\prep\build_static_files.py --ini example_prep.ini --acres 0 -o

Steps 4 and 4b are only needed if running spatially varying cablibration mode

4: Build Spatial Crop Parameter Files 
  python C:\et-demands\et-demands\prep\build_spatial_crop_params.py --ini example_prep.ini --area 0

4b:  Interpolate spatial crop params from preliminary calibration .shp
  python ..\et-demands\et-demands\prep\interpolate_spatial_crop_params.py --ini example_prep.ini
  
NOTE: Interpolate spatial crop parameters is utilized for large study areas that wish to interpolate 
crop parameter information from a few calibration cells to the entire study domain.




CropET
------

AreaET
------

PostProcessing
--------------
