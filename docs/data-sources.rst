.. _data-sources:

Data Sources
============

RefET
-----
Meteorological data can be obtained from numerous sources.


Agricultural Weather Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------------------------------------+
| Network                                                                                           | Supporting Organization                                   | Coverage                                                                      |
+===================================================================================================+===========================================================+===============================================================================+
| `CoAgMet  <http://coagmet.colostate.edu/>`_                                                       | Colorado State University                                 | Colorado                                                                      |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------------------------------------+
| `AZMET  <https://cals.arizona.edu/azmet/>`_                                                       | University of Arizona                                     | Arizona                                                                       |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------------------------------------+
| `AgWeatherNet <https://weather.wsu.edu/>`_                                                        | Washington State University                               | Washington                                                                    |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------------------------------------+
| `ZiaMet <https://weather.nmsu.edu/ziamet/>`_                                                      | New Mexico State University                               | New Mexico                                                                    |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------------------------------------+
| `Montana Mesonet <http://climate.umt.edu/mesonet/>`_                                              | University of Montana                                     | Montana                                                                       |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------------------------------------+
| `AgriMet-GP <https://www.usbr.gov/gp/agrimet/index.html>`_                                        | Bureau of Reclamation Great Plains Regional Office        | Montana                                                                       |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------------------------------------+
| `AgriMet-PN <https://www.usbr.gov/pn/agrimet/>`_                                                  | Bureau of Reclamation Pacific Northwest Regional Office   | Washington, Oregon, California (northern), Nevada, Utah, Idaho, Montana       |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------------------------------------+
| `CIMIS <https://cimis.water.ca.gov/>`_                                                            | California Department of Water Resources                  | California                                                                    |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------------------------------------+
| `NICE Net <https://nicenet.dri.edu/>`_                                                            | Desert Research Institute                                 | Nevada                                                                        |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------------------------------------+
| `West Texas Mesonet <http://www.depts.ttu.edu/nwi/research/facilities/wtm/index.php>`_            | Texas Tech University                                     | Texas (western)                                                               |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------------------------------------+

Other Weather Networks
~~~~~~~~~~~~~~~~~~~~~~

+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------+
| Network                                                                                           | Supporting Organization                                   | Coverage                                        |
+===================================================================================================+===========================================================+=================================================+
| `TexMesonet <https://www.texmesonet.org/>`_                                                       | Texas Water Development Board                             | Texas                                           |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------+
| `Lower Colorado River Authority Hydromet <https://hydromet.lcra.org/>`_                           | Lower Colorado River Authority (TX)                       | Texas (Colorado River Basin)                    |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------+
| `Kansas Mesonet <http://mesonet.k-state.edu/>`_                                                   | Kansas State University                                   | Kansas                                          |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------+
| `Nebraska Mesonet <https://mesonet.unl.edu/>`_                                                    | University of Nebraska, Lincoln                           | Nebraska                                        |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------+
| `Mesonet <http://mesonet.org/>`_                                                                  | University of Oklahoma, Oklahoma State University         | Oklahoma                                        |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------+

Multi-Network Sources
~~~~~~~~~~~~~~~~~~~~~

+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------+
| Source                                                                                            | Supporting Organization                                   | Coverage                                        |
+===================================================================================================+===========================================================+=================================================+
| `MesoWest and SynopticLabs <https://synopticlabs.org/>`_                                          | University of Utah                                        | United States                                   |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------+
| `Integrated Surface Database <https://www.ncdc.noaa.gov/isd/>`_                                   | NOAA National Center for Environmental Information (NCEI) | Global                                          |
+---------------------------------------------------------------------------------------------------+-----------------------------------------------------------+-------------------------------------------------+

CropET
------

Study Area
^^^^^^^^^^

HUC8 and HUC10 features can be extracted from the full - [USGS Watershed Boundary Dataset](http://nhd.usgs.gov/wbd.html) (WBD) geodatabase. A subset of the WBD HUC polygons can downloaded using the [USDA Geospatial Data Gateway](https://gdg.sc.egov.usda.gov/) or the full dataset can be downloaded using the [USGS FTP](ftp://rockyftp.cr.usgs.gov/vdelivery/Datasets/Staged/WBD/).

County features can be downloaded from the [USDA Geospatial Data Gateway](https://gdg.sc.egov.usda.gov/). For the zonal stats prep tool to work, the shapefile must have a field called "COUNTYNAME".  Other county features (such as the [US Census Cartographic Boundary Shapefiles](https://www.census.gov/geo/maps-data/data/tiger-cart-boundary.html) could eventually be supported (or the name field could be manually changed to COUNTYNAME).

The GRIDMET grid cells can be constructed how?


Crop Type Data
^^^^^^^^^^^^^^

Cropland Data Layer (CDL)
~~~~~~~~~~~~~~~~~~~~~~~~~

The Cropland Data Layer (CDL) is a product of the USDA National Agricultural Statistics Service (NASS) with the mission
“to provide timely, accurate and useful statistics in service to U.S. agriculture”
`(Boryan et al 2011) <https://doi.org/10.1080/10106049.2011.562309>`_. The CDL is a crop-specific
land cover classification product of more than :ref:`100 crop categories <cdl-crop-types>` grown in 
the United States developed using remote sensing. The CDL can be downloaded using NASS’s
`CropScape tool <https://nassgeodata.gmu.edu/CropScape/>`_. Updates about and references for the
CDL can be found at `NASS <https://www.nass.usda.gov/Research_and_Science/Cropland/SARS1a.php>`_.
A version of the CDL has been released annually from 1994-Present.

## Soils Data
