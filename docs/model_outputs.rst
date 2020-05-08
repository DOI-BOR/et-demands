.. _model-outputs:

Model Outputs
=============

.. _model-outputs-refet:

RefET
-----

CropETPrep
----------

CropET
------
ETDemands is capable of outputting both raw daily files as well as monthly, annual, and growing season summary files. All model output files are saved in .csv format. Model output files are controlled by the stat flags and folder names in the [CROP_ET] section of the model .ini file. Output files are enabled by setting the specific stat_flag =True.

  Stats flags
    daily_stats_flag = True
    
    monthly_stats_flag = False
    
    annual_stats_flag = False
    
    growing_season_stats_flag = False


Statistic subfolders are created for each of the enabled stat flags above and will be located in the Project Folder

  ET sub-folder names
    daily_output_folder = daily_stats
    
    monthly_output_folder = monthly_stats
    
    annual_output_folder = annual_stats
    
    gs_output_folder = growing_season_stats


In addition to date information, each stat file contains the following results:

:PMeto/PMetr: Input reference evapotranspiration (ET)
:ETact: Actual Crop ET including stress adjustments
:ETpot: Crop Specific Potential ET 
:ETbas: Basal evaporation component of ET
:Kc:  Crop Coefficient  
:Kcb: Basal crop coefficient
:PPT: Precipitation
:Irrigation:  Irrigation
:Runoff:  Runoff
:DPerc: Deep Percolation from the root zone
:P_rz:  Precipitation residing in the root zone
:P_eft: Effective Precipitation (precipitation residing in the root zone available for transpiration)
:NIWR:  Net Irrigation Water Requirement
:Season:  Growing Season Flag (1 = True, 0 = False)
:Cutting: Cutting Flag (applies to crops that harvested via cutting cycles (e.g. alfalfa))
  
Monthly, annual, and growing season statistics are aggregated from the daily output files according to the statistics in the list below:

:PMeto/PMetr:    sum
:ETact:          sum
:ETpot:          sum
:ETbas:          sum
:Kc:             mean
:Kcb:            mean
:PPT:           sum
:Irrigation:     sum
:Runoff:         sum
:DPerc:          sum
:P_rz:          sum
:P_eft:          sum
:NIWR:           sum
:Season:         sum
:Cutting:        sum

AreaET
------

PostProcessing
