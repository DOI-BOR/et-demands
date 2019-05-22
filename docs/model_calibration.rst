.. _model-calibration:

Model Calibration
=================

.. _model-calibration-refet:

RefET
------

.. _model-calibration-refet-tr:

Thornton and Running Coefficients
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _model-calibration-cropet:

CropET
------
ETDemands utlizes daily temperature information to determine the start and duration of each crops growing season. Initial values for each of the control parameters are provided, however, users should customize these values depending on their input meterological data source and study area. Inherent biases in temperature data can lead to incorrect timing of the season start, effective full cover, and termination dates. A detailed decsiption of the various crop parameters can be found here: http://data.kimberly.uidaho.edu/ETIdaho/ETIdaho_Report_April_2007_with_supplement.pdf

The initial control parameters are located in the CropParams.txt file contained in the static folder. Note: Users should not modify the statics files found in the etdemands model folder. Running the initial prep steps will build project specific static files that can be changed accordingly. ETDemands can be run with either spatially consistent or spatially varying calibration parameters. This mode is set in the model INI file via the spatila_cal_flag and spatial_cal_folder inputs.

  ## Spatially varying calibration
  spatial_cal_flag = True
  spatial_cal_folder= C:\example\calibration

Spatially Consistent Calibration Mode (Default)
Spatially consistent calibration mode applies the same crop parameter information to every ETZone in your model. The parameters are read directly from your project specific CropParams.txt file. 

Spatially Varying Calibration 
Spatially consistent calibration mode applies different crop parameter information to every ETZone in your model. These varying parameters are orgnaized in crop specific .shp. To create the crop specific calibration .shp. Run the build_spatial_crop_params.py script:
  python ..\et-demands\et-demands\prep\build_spatial_crop_params.py --ini example.ini 

Running this script creates and populates the calibration folder with crop specific calibration .shp. Each .shp contains an attribute table with rows for each ETZone that contains that crop. The columns of the attribute table are initially populated with the default crop parameters from the CropParams.txt. Users can now assign specific crop paramters from each ETZone and crop. 

Interpolation of Spatial Crop Parameters

