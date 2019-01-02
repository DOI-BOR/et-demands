Analysis Tools
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

compute_growing_season.py
---------


plot_crop_daily_groupstats.py
---------


plot_crop_daily_timeseries.py
---------





