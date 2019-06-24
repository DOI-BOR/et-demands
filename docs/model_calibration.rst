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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ETDemands utlizes crop specific parameters to determine crop growth and timing including growing season start and end dates, crop development rates, effective full cover, harvest timings, and killing frosts. Initial values for each of the control parameters are provided, however, users should customize these values for their input meterological data source and study area. Inherent bias in temperature data can lead to incorrect timing of the season start, effective full cover, and termination dates. A detailed decsiption of the various crop parameters can be found here: http://data.kimberly.uidaho.edu/ETIdaho/ETIdaho_Report_April_2007_with_supplement.pdf

The initial control parameters are located in the CropParams.txt file contained in the static folder. Note: Users should NOT modify the statics files found in the etemands model folder. Running the initial prep steps will build project specific static files that can be changed accordingly. ETDemands can be run with either spatially consistent or spatially varying calibration parameters. This mode is set in the model INI file via the spatial_cal_flag and spatial_cal_folder inputs.

  ## Spatially varying calibration
    spatial_cal_flag = True
    
    spatial_cal_folder= C:\\example\\calibration

Spatially Consistent Calibration Mode (Default)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Spatially consistent calibration mode applies the same crop parameter information to every ETZone in your model. The parameters are read directly from your project specific CropParams.txt file. This mode should be utilized for when the study zones are located in relatively simliar environments and your supplied weather data is consistent from zone to zone.

Spatially Varying Calibration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Spatially varying calibration mode applies different crop parameter information to every ETZone in your model. These varying parameters are orgnaized in crop specific .shp. To create the crop specific calibration .shp, run the build_spatial_crop_params.py script:
python ..\et-demands\et-demands\prep\build_spatial_crop_params.py --ini example.ini 

Running this script creates and populates the calibration folder with crop specific calibration .shp. Each .shp contains an attribute table with rows for each ETZone that contains that crop. The columns or fields of the attribute table are initially populated with the default crop parameters from the CropParams.txt. Users can now assign specific crop paramters from each ETZone and crop. 

Calibration Process
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Calibrating the ETDemands model is an iterative process that requires users to perform complete runs followed by adjustments to the CropParam.txt or crop paramater .shp. The user re-runs the model after adjusting the crop parameter until the they are satistified with the timing and shape of the crop development curves. Literature review should be performed to determine typical planting, effective full cover, and harvest dates. Throughout the calibration process, users can limit the cells and/or crops being processed by the model by setting the 'crop_test_list' and 'cell_test_list' variblies in the [CROP ET] section of the model .ini file. For example, setting the parameters below in the model .ini will run 'crop 07' in 'cell 529813' and skip all other cells/crop combinations. 

  crop_test_list = 07
  cell_test_list = 529813


Interpolation of Spatial Crop Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
For model runs with a large number of ETZones, users may prefer to spatially interpolate crop parameters from a set of preliminary calibration zones. To set-up and interpolate crop parameters from a set of preliminary zones, users should first run the ETDemands model with a subset of cells that are representative of spatial extent and crops selection throughout the larger study area. Once you've finalized the crop parameter .shp for the subset run, you will copy the crop specific .shp to the "preliminary_calibration" folder in the calibration folder of your complete model. Users should run the build_spatial_crop_params.py script to create the calibration folder and crop specific .shp before building the preliminary calibration folder. Note that if the "preliminary_calibration" folder will need to be created if it doesn't already exist. 

python ..\et-demands\et-demands\prep\interpolate_spatial_crop_params.py --ini UC_2018.ini






