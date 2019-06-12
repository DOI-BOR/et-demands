ETDemands Post-Processing Tools
===================
ETDemands offers multiple post-processing tools to help summarize and plot the daily, monthly, and annual output datasets.
The various tool scripts are located in the etdemands/tools folder. Below you will find a brief desciption of each tool:

Compute Growing Season (compute_growing_season.py)
--------------------
The compute growing season tool processesing each cells growing season information from the daily output files input summary .csv
that show the start, end, and cutting dates for each cell/crop combination. The growing_season_full_summary.csv contains information
for each unique cell/crop/year combination, while the growing season_mean_annual.csv computes an average of all years for each cell/crop
combination.
Here is an example of a typical command called from the the project folder: 
python ..\et-demands\et-demands\tools\compute_growing_season.py -i UC_2018.ini 

optional arguments:
  -h, --help            show this help message and exit
  -i PATH, --ini PATH   Input file (default: None)
  --start DATE          Start date (format YYYY-MM-DD) (default: None)
  --end DATE            End date (format YYYY-MM-DD) (default: None)
  -c CROPS, --crops CROPS
                        Comma separate list or range of crops to compare
                        (default: )
  --debug               Debug level logging (default: 20)
  
Summary Shapefiles (summary_shapefile_gpd.py)
--------------------
The summary shapefile tools builds a unique .shp for each crop containing ET and NIWR infromation based on the daily_stat
output files. This script can summarize statistics for different time periods including annual, growing season (based on etdemands estimate),
or by specific doy range. The summary .shp will contain the median and mean statistics for all years included in the analysis. A year range
filter will output summary statistics for specific time periods. Output will be saved to the summary_shapefile folder. 


python ..\et-demands\et-demands\tools\summary_shapefiles_gpd.py -i UC_2018.ini -y 2018 -t annual

optional arguments:
  -h, --help            show this help message and exit
  -i PATH, --ini PATH   Input file (default: None)
  -t {annual,growing_season,doy}, --time_filter {annual,growing_season,doy}
                        Data coverage options. If "doy", -start_doy and
                        -end_doy required. (default: annual)
  -s START_DOY, --start_doy START_DOY
                        Starting julian doy (inclusive) (default: None)
  -e END_DOY, --end_doy END_DOY
                        Ending julian doy (inclusive) (default: None)
  -y YEAR, --year YEAR  Years to include, single year (YYYY) or range (YYYY-
                        YYYY) (default: )
  --debug               Debug level logging (default: 20)
