Analysis Tools
==============
ETDemands provides post-processing tools to assist with summarizing and viewing
the raw daily, monthly, and annual .csv datasets. In general, there are two types
of outputs: Timeseries Plots and Summary Shapefiles

The timeseries scripts analyze specific crops and years to create interactive
.html plots that can be used to visualize temporal patterns or changes in the
data. Each .html plot contains all the data used to generate the plot and can be
easily shared.

The shapefile scripts batch the output files into spatial summaries that can be
visualized with any standard GIS software (e.g. ArcGIS, QGIS). Each output
shapefile will contain summary statistics for each ET Zone for the crop(s) and
year(s) of interest.

Note: Many of these tools offer options to process single years or multiple
years. Passing the "-h" argument to each script will display input argument
options.


ET Zone Raw Timeseries (plot_crop_daily_timeseries.py)
---------
This analysis tool creates an .html time series figure from the daily
ETact/ETbas/ETr, Kc/Kcb, PPT/Irrigation datasets. A figure is generated for
each ET Zone/Crop combination. Input arguments for start/end date and crop
allow the user to only process specific date ranges and crops. Output figures
can be found in the 'daily_plots' subfolder.

plot_crop_daily_groupstats.py
---------



Shapefile Summary Tools
==============
Annual Summary Shapefiles (annual_summary_shapefiles_gpd.py)
---------
This analysis tool converts the annual output .csv files into crop specific summary shapefiles for viewing and analysis of the spatial distribution of evaporation. The output shapefiles contain 'ET (ETo or ETr)', 'ETact', 'ETpot', 'ETbas', 'Kc', 'Kcb', 'PPT', 'Irr', 'Runoff', 'DPerc', 'NIWR', 'Season' information for each ET Zone containing the crop of interest.

Annual summary shapefiles can be created for a specific year of interest or for a range of years using "year filter" input argument. Note that both mean ('_mn') and median ('_mdn') statistics are output for each variable. If only one year is specified, mean and median statistics are the same. Output files can be found in the 'annual_stats' folder where 'summary_shapefiles_YYYYtoYYYY' specifies the minimum and maximum years included in the analysis.

Growing Season Summary Shapefiles (gs_summary_shapefiles_gpd.py)
---------
Similar to the annual summary shapefile script, the growing season summary shapefile script creates a summary shapefile for each crop containing growing seasons statistics for the year(s) specified. If a single year is specified, the statistics represent totals and averages for each day during the growing season. If multiple years are specified, the statistics represent an average of the yearly totals. 

Output files can be found in the 'growing_season_stats' folder where 'gs_summary_shapefiles_YYYYtoYYYY' specifies the minimum and maximum years included in the analysis.

cropweighted_summary_shapefiles.py
---------

Miscellaneous Summary Tools
==============

compute_growing_season.py
---------








