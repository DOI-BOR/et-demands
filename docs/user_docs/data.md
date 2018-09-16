# CropET Input Data

## Weather Data

### Timeseries Data
The user must provide daily weather and reference ET data for each weather station. This includes:

* Date
* TMax - Daily maximum temperature
* TMin - Daily minimum temperature
* Precip - Daily total precipitation
* Snow - Daily total snowfall
* SDep - Daily snow depth
* EstRs - Daily incoming solar radiation
* EsTDew - Daily dewpoint
* ASCEr - Daily reference ET from Penman–Monteith
* ASCEg - Daily reference ET from Penman–Monteith

#### File Format

* Format: **.csv**

* Structure:

| Date   | TMax   | TMin   | Precip   | Snow     | SDep | EstRs   | EsWind | EsTDew | Penm48   | PreTay   | ASCEr    | ASCEg    | 85Harg   |
| -------| ------ | ------ | -------- | -------- | ---- | ------- | ------ | ------ | -------- | -------- | -------- | -------- | -------- |
| Units  | [C]    | [C]    | [In*100] | [In*100] | [In] | [MJ/m2] | [m/s]  | [C]    | [mm/day] | [mm/day] | [mm/day] | [mm/day] | [mm/day] |


### Location Shapefile
A shapefile containing the locations of eath weather station is also required and is used to generate the static input files. The shapefile must contain the following attributes:

* STATION_ID - Weather station id
* *ZONE_ID* - Zone id. This can include HUC8, HUC10, COUNTRYNAME, OR GRIDMET_ID
* LAT - Weather station latitude
* LON - Weather station longitude
* [*optional*] *ELEV* [ELEV_FT; ELEV_M] - Weather station elevation in feet or meters. This field is optional and only required if running the RefET model to estimate reference ET.

#### File Format

* Format: **.shp**

* Attribute Table Structure:

| STATION_ID   | *ZONE_ID* [HUC8; HUC10; COUNTRYNAME; GRIDMET_ID]   | LAT   | LON   | *ELEV* [ELEV_FT; ELEV_M]   |
| ------------ | -------------------------------------------------- | ----- | ----- | -------------------------- |


## Study Area
The user must provide a study area polygon shapefile with at least one feature.  Each feature in the study area shapefile will become a separate ET cell/unit.  Currently, only HUC8, HUC10, county, and gridmet cell shapefiles are fully supported by the prep tools.



## Crop Type Data

The CDL raster is used to determine the acreage of crops in each ET cell/unit.  Crops with very low acreages (that were likely misclassified) can be excluded in the zonal stats prep tool.  A single CDL raster is used since the CropET module can only be run for a static set of crops.  Active crops will be set to 1 in the ETCellsCrops.txt static input file.

The CDL raster is also used to mask out non-agricultural areas when computing the average soil conditions.  The CDL raster is used as the "snap raster" or reference raster for all subsequent operations.  This means that the prep tools will project, clip and align the study area raster and soil rasters to the CDL raster.

## Soils Data
The average agricultural area available water capacity (AWC) and hydrologic soils group are needed for each ET cell/unit.  The hydrologic soils group can be estimated based on the percent sand and clay for each ET cell/unit.

The AWC, percent clay, and percent sand data cannot (currently) be directly downloaded. The easiest way to obtain these soils data is to download the [STATSGO] (http://www.nrcs.usda.gov/wps/portal/nrcs/detail/soils/survey/geo/?cid=nrcs142p2_053629) database for the target state(s) using the [USDA Geospatial Data Gateway](https://gdg.sc.egov.usda.gov/).  Shapefiles of the soil properties can be extracted using the [NRCS Soil Data Viewer](http://www.nrcs.usda.gov/wps/portal/nrcs/detailfull/soils/home/?cid=nrcs142p2_053620) The [SURGO](http://www.nrcs.usda.gov/wps/portal/nrcs/detail/soils/survey/geo/?cid=nrcs142p2_053627) databases can also be used, but these typically cover a smaller area and may have areas of missing data.  It may also be possible to used the gridded SSRUGO data, but this has not been tested.

*Add additional details about which options were used in the Soil Data Viewer*

To use the soil prep tools, the soils data must be provided as separate shapefiles for each product.  The names of the soil shapefiles are hard coded in the rasterize_soil_polygons.py script as "{}_WTA_0to152cm_statsgo.shp", where {} can be "AWC", "Clay", or "Sand" (see [Model Structure](structure.md)).  For each shapefile, the value field name is hardcoded as the upper case of the property (i.e. "AWC", "CLAY", or "SAND").
