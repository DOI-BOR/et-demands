Analysis Tools
==============
ETDemands provides post-processing tools to assist with summarizing and viewing
the raw daily, monthly, and annual .csv datasets. In general, there are two
types of outputs: Timeseries Plots and Summary Shapefiles

The timeseries scripts analyze specific crops and years to create interactive
.html plots that can be used to visualize temporal patterns or changes in the
data. Each .html plot contains all the data used to generate the plot and can be
easily shared with team members and stakeholders.

The shapefile scripts batch the output .csv files into spatial summaries that can be
visualized with any standard GIS software (e.g. ArcGIS, QGIS). Each output
shapefile will contain summary statistics for each ET Zone for the crop and
year(s) of interest.

Note: Many of these tools offer options to process single or multiple
years. Passing the "-h" argument to each script will display input argument
options.

Timeseries Tools
==============
Daily Timeseries (plot_crop_daily_timeseries.py)
---------
This analysis tool creates an .html time series figure from the daily
ETact/ETbas/ETr, Kc/Kcb, PPT/Irrigation datasets. A figure is generated for
each ET Zone/Crop combination. Input arguments for start/end date and crop
allow the user to only process specific date ranges and crops. Output figures
can be found in the 'daily_plots' subfolder.

Average Annual Timeseries (plot_crop_daily_groupstats.py)
---------
The groupstats timeseries script averages daily input data from multiple years
and creates a single average annual timeseries plot of ETact/ETr, Kc,
and Kcb information for each ET Zone/crop combination. This timeseries plot
includes 25th, 50th, 75th percentile information. Output figures
can be found in the 'daily_plots' subfolder.


Shapefile Summary Tools
==============
Summary Shapefiles (summary_shapefiles_gpd.py)
---------
This analysis tool converts the daily output .csv files into crop specific
summary shapefiles for viewing and analysis of the spatial distribution of
evaporation. Specific Time periods can be specified to process statistics for
annual,growing season (as defined by ETDemands), or custom day of year ranges.
The output shapefiles contain 'ET (ETo or ETr)', 'ETact', 'ETpot',
'ETbas', 'Kc', 'Kcb', 'PPT', 'Irr', 'Runoff', 'DPerc', 'NIWR', 'Season'
information for each ET Zone containing the crop of interest.

Summary shapefiles can be created for a specific year of interest or for
a range of years using "year filter" input argument. Note that both mean ('_mn')
and median ('_mdn') statistics are output for each variable. If only one year
is specified, mean and median statistics are the identical. Output files can be found
in the 'summary_shapefiles' folder where 'summary_YYYYtoYYYY' specifies the
minimum and maximum years included in the analysis. The following
input arguments can be specified to customize the summary output:

-i, --ini
        ini_path (str): file path of the project INI file
-y, -year
        year_filter (list): include specific years in summary
        (single YYYY or range YYYY:YYYY)
-t, --time_filter
        time_filter (str): 'annual' (default), 'growing_season', 'doy'
-s, --start_doy
        start_doy (int): starting julian doy (inclusive)
-e, --end_doy
        end_doy (int): ending julian doy (inclusive)
       
*start and end doy of year must be included when using the 
'doy' time_filter


Cropweighted Summary Shapefile (cropweighted_summary_shapefiles.py)
---------
The cropweighted script generates a shapefile of crop area weighted average ET
rates and NIWR for each ET Zone. Information for a single year or an average of
multiple years can be output. Options to process annual or growing season totals
are available. Single or multiple years can be included in the output statistic.
Output files can be found in the 'cropweighted_shapefile' folder. 

Miscellaneous Summary Tools
==============

Growing Season Summary (compute_growing_season.py)
---------
This script processing the daily output files to summarize growing season
length and cutting information for each ET Zone/crop combination. Two summary
.csv files are generated:

  'growing_season_full_summary.csv' contains information for ET Zone/crop growing
  season information for each year included in the analysis.

  'growing_season_mean_annual.csv' contains averages of all years included in the
  analysis.
Both .csv files can be found in the 'growing_season_stats' folder.








