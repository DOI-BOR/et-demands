CropET Prep Example
===================

Clone the repository
--------------------
Ensure you have the latest version of the et-demands repository from GitHub. To get started, or for instructions on pulling
the latest version see Getting Started.

.. note::
   For this example, it is assumed that the repository was cloned directly to the C: drive (i.e. C:\\et-demands).

Command prompt / Terminal
-------------------------
All of the CropET prep scripts should be run from the command prompt or terminal window.  In Windows, to open the command prompt, press the "windows" key and "r" and type "cmd" or click the "Start" button, "Accessories", and then "Command Prompt".

Within the command prompt or terminal, change to the target drive if necessary::

    > C:

Then change directory to the et-demands folder::

    > cd C:\et-demands

You may need to build the common folder if it doesn't exist::

    > mkdir common

Building the Example
--------------------
.. note::
   For this example, all scripts and tools will be executed from the "example" folder.

Change directory into the example folder::

    > cd example

Cropland Data Layer (CDL)
-------------------------
The et-demands model requires information about the type and spatial extent of crops grown in the study area. A standard dataset containing this information is the Cropland Data Layer (CDL), a product of the USDA National Agricultural Statistics Service (NASS). The CDL is a crop-specific land cover classification product of more than 100 crop categories grown in the United States derived from remotely-sensed data (`Boryan et al. 2011 <https://doi.org/10.1080/10106049.2011.562309>`_). The CDL has been produced for every year from 1997-Present and is hosted on NASS's _`CropScape <https://nassgeodata.gmu.edu/CropScape/>`_. 

Download the CONUS CDL raster. The CONUS CDL rasters should be downloaded to the "common" folder so that they can be used for other projects. For this example we will be using the 2010 CDL raster. ::

    > python ..\et-demands\prep\download_cdl_raster.py --cdl ..\common\cdl --years 2010

If the download script doesn't work, please try downloading the `2010_30m_cdls.zip <ftp://ftp.nass.usda.gov/download/res/2010_30m_cdls.zip>`_ file directly from your browser or using a dedicated FTP program.

Study Area
----------
The et-demands model requires a shapefile defining the study area. 

For this example, the study area is a single HUC 8 watershed (12090105) in Texas that was extracted from the full `USGS Watershed Boundary Dataset <http://nhd.usgs.gov/wbd.html>`_ (WBD) geodatabase.

.. image:: https://cfpub.epa.gov/surf/images/hucs/12090105l.gif
   :target: https://cfpub.epa.gov/surf/huc.cfm?huc_code=12090105
.. image:: https://cfpub.epa.gov/surf/images/hucs/12090105.gif
   :target: https://cfpub.epa.gov/surf/huc.cfm?huc_code=12090105

Project the study area shapefile to the CDL spatial reference and then convert to a raster::

    > python ..\et-demands\prep\build_study_area_raster.py -shp gis\huc8\wbdhu8_albers.shp --cdl ..\common\cdl --year 2010 --buffer 300 --stats -o

Weather Stations
----------------
The example station is the centroid of a single 4km cell from the `University of Idaho Gridded Surface Meteorological Data <http://metdata.northwestknowledge.net/>`_ that is located in the study area.

Cropland Data Layer (CDL)
-------------------------
Clip the CDL raster to the study area::

    > python ..\et-demands\prep\clip_cdl_raster.py --cdl ..\common\cdl --years 2010 --stats -o

Mask the non-agricultural CDL pixels::

    > python ..\et-demands\prep\build_ag_cdl_rasters.py --years 2010 --mask -o --stats

Soils
-----

.. note::
   For this example, the soils shapefiles have already been converted to raster and are located in the example\\gis\\soils folder.  It is not necessary to run the "rasterize_soil_polygons.py step below.

Optional:
The following commands can be used to produce the required soils information from the soils data
Rasterize the soil shapefiles to match the CDL grid size and spatial reference::

    > python ..\et-demands\prep\rasterize_soil_polygons.py --soil ..\common\statsgo -o --stats

Extract the soil values for each CDL ag pixel::

    > python ..\et-demands\prep\build_ag_soil_rasters.py --years 2010 --mask -o --stats

Zonal Stats
-----------
Compute the soil properties and crop acreages for each feature/polygon. ::

    > python ..\et-demands\prep\et_demands_zonal_stats.py --year 2010 -o --zone huc8

Static Text Files
-----------------
Build the static text files from the templates in "et-demands\\static". ::

    > python ..\et-demands\prep\build_static_files.py --ini example.ini --zone huc8 --acres 10 -o
