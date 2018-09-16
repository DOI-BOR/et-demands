# CropET Standard Data

## Weather Data

## Study Area
HUC8 and HUC10 features can be extracted from the full - [USGS Watershed Boundary Dataset](http://nhd.usgs.gov/wbd.html) (WBD) geodatabase. A subset of the WBD HUC polygons can downloaded using the [USDA Geospatial Data Gateway](https://gdg.sc.egov.usda.gov/) or the full dataset can be downloaded using the [USGS FTP](ftp://rockyftp.cr.usgs.gov/vdelivery/Datasets/Staged/WBD/).

County features can be downloaded from the [USDA Geospatial Data Gateway](https://gdg.sc.egov.usda.gov/). For the zonal stats prep tool to work, the shapefile must have a field called "COUNTYNAME".  Other county features (such as the [US Census Cartographic Boundary Shapefiles](https://www.census.gov/geo/maps-data/data/tiger-cart-boundary.html) could eventually be supported (or the name field could be manually changed to COUNTYNAME).

The GRIDMET grid cells can be constructed how?
## Crop Type Data

### Cropland Data Layer (CDL)

The Cropland Data Layer (CDL) is a product of the USDA National Agricultural Statistics Service (NASS) with the mission “to provide timely, accurate and useful statistics in service to U.S. agriculture”
([Boryan et al 2011](https://doi.org/10.1080/10106049.2011.562309)). The CDL is a crop-specific land cover classification product of more than [100 crop categories](cdl_crop_types.md) grown in the United States developed using remote sensing.
The CDL can be downloaded using NASS’s [CropScape](https://nassgeodata.gmu.edu/CropScape/) tool. Updates about and references for the CDL can be found at [NASS](https://www.nass.usda.gov/Research_and_Science/Cropland/SARS1a.php).
A version of the CDL has been released annually from 1994-Present.

## Soils Data
