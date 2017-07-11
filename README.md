# et-demands

# Python Penman-Monteith ET Model Use Instructions

The Bureau of Reclamation’s Technical Services Center, in conjunction with the Desert Research Institute has completed the coding of the Penman-Monteith Model (PM) into Python for use in crop evapotranspiration (ET) and water use calculations.  Previously, a version of the same was cast into the VB.net framework and utilized in the calculation of ET demands for the West-Wide Climate Risk Assessment (WWCRA).  The current Python version was compared against the previous VB.net version with good results.
This paper is intended to provide a quick “How To” in running the Python version of the PM model.  The model is robust in that various input and output formats are allowed.  This paper concentrates on the use of Excel workbooks (both xlsx and csv formats) for input and output, with .ini files providing the basic model run parameters.

# Introduction
The Python PM model is a collection of scripts designed to estimate crop ET water consumption using the, well established, FAO-56 (Allen, R.G. et al, 1998) approach.  The system is modular in design in that there are several scripts associated with the model, each of which has a specific, well defined use.  Three main components are required to fully compute ET: Reference ET, Crop ET, and Area ET.
The Reference ET module is the first step in the computation of ET estimates in a basin.  This algorithm utilizes meteorological data in computing the ET of a reference crop (the PM model described herein is able to use a grass or alfalfa reference, at the users discretion).  This reference value is then scaled by the Crop ET module to estimate the ET requirement of the specific crops simulated.  These crop ET values are then combined with the acreages of each in the Area ET module to determine an estimate of the basin total water requirement.
Additional utilities and tools are also included in the Python PM package.  These include tools to assist the user in basin parameter setup (soils properties, etc), solar radiation estimates, calibration, and meteorological timeseries creation.  These features will not be covered in this paper, but will be available in a future publication.

# Methods
This section describes the Python scripts and support files needed to execute the model.  An example basin study, the Upper Red River (located at: T:\WaterResources\PlanningOperations\D8500\apps\pythonApps\bortsc\example\UpperRed), recently concluded using this system, is included for reference.  Detailed directory and file information is presented.  To help in clarification, the reader is encouraged to open specific example files as they are presented in this paper.

## Directory Structure
The directory structure is specific to the example, and follows the directory structure adopted for the WWCRA.  It includes a directory identified by the basin within the fieldprojects directory off of the root (C:) disk.  All of the configuration files associated with the execution of the PM model use this directory structure.  If a different structure is required, care must be taken to ensure all references to the C:\fieldprojects\BasinName structure are adjusted in the configuration files.   

Under the C:\fieldprojects\BasinName directory, additional directories are used.  The Data directory is used for input and output files used by the PM model.  The runScripts directory is used to locate the basin configuration *.ini files used to inform the Python code of directories and parameters.  The et-demands directory is a copy of the full Python PM code taken from the T: drive archive.  Each directory is discussed in more detail below.
   
### Data directory and example files   
   
The data directory is used to collect all crop-specific input and output information as well as meteorological data.  The distinction between crop-specific and Python control is subtle but important.  Crop-specific data is that data that informs the model on cropping and area parameters: acreages, crop names, meteorology stations for specific cropping areas, soil conditions, etc.  Python control is included in .ini files and includes details such as file names, directory structures, parameter units, etc.  
   
The primary crop-specific input file used is located in the data\static directory, and is called RedRiverMetaData.xlsx.  This file contains several worksheets that provide cropping types and acreages, meteorological and soil properties in the study basin, and PM model calibration parameters.  
   
The meteorological input data are located in the data\climatechange\daily_in_met directory.  In the example, maximum temperature, minimum temperature and precipitation are included as user supplied meteorological parameters.  These data represent the minimum amount of time series inputs the PM model requires.  In addition to these data, solar radiation, wind run and dew point temperatures can be either provided as a time series (in the same meteorological files in the data\climatechange\daily_met_in directory) or estimated by the model.  In the Red River example, estimation of solar radiation is accomplished using the Thornton-Running equation in conjunction with 3 coefficients provided by the user.  Estimation of wind and dew point is in the form of monthly averages, provided by the user in the RedRiverMetadata.xlsx file.  Estimation of the Thornton-Running coefficients is available through another set of Python scripts, but is beyond the scope of this paper.
The other directories shown in the data\climatechange folder are output folders created and populated during the execution of the PM model.

### runScripts directory
The runScripts folder contains the .ini files used to control the basic functions of the Python PM model code.  Three .ini files are required.  csv_ret_csv.ini is used to configure and control the Reference ET portion of the PM model.  csv_cet_dri_cp.ini is the files that is used to configure and control the Crop ET functionality of the model.  Finally, dri_aet_csv.ini configures and controls the Area ET portion of the model.  It is in these three .ini files that the PM model is informed of meteorological inputs and file names, crop-specific workbook and worksheet names, etc.
   
### et-demands directory
     
The et-demands directory is copied directly from the network archive location: T:\WaterResources\PlanningOperations\D8500\apps\pythonApps\bortsc directory.  Currently the Python code uses relative addressing to access support scripts and utilities during execution.  The relative addressing points directly to the et-demands directory within the basin directory structure.  If the user were interested in creating a version of the code that could be accessed from any place local to the computer, adjustments to the Python code would be required, adjusting it from relative addressing to point at a specific location on the user’s computer disk.
   
### Python PM model execution
    
Execution of the model is done using a command line from within a DOS-Prompt command window.  To execute the model, the user must be sure that the 64bit version of the Anaconda Python version 2.7 or newer (available from http://www.consortium.io.downloads) is available and running.  The base directory for execution is the C:\fieldprojects\UpperRed\runScripts directory (in other words, the commands to execute the Python code must be executed after changing to the C:\fieldprojects\UpperRed\runScripts directory).  Each of the three modules are executed separately in the following order: Reference ET, Crop ET, Area ET.  Command line arguments for each are outlined below.  Note that the order of execution is important in that the Crop ET module relies on data calculated in the execution of the Reference ET module, and the Area ET module utilizes data calculated in the Reference ET and Crop ET modules.  Note that if meteorological data doesn’t change, the Reference ET module need only be executed once, as these data will not change unless weather parameters are adjusted.  Aslo note that the commands displayed below are also found in a text file located in the C:\fieldprojects\UpperRed\runScripts directory, called etargs.txt for readily available user reference.

### Reference ET
   
The command line is:
    
python ..\et-demands\refET\bin\run_ret.py -i csv_ret_csv.ini –mp
   
Command arguments are:
    
-h, --help : Show the help message then exit
-i PATH, --ini PATH: Intialization file path; If omitted, script will prompt
-d, --debug : Save debug level comments to debug.txt file
-m MetID, --metid MetID : Specify a particular single Met Node ID to run
-v, --verbose : Display information level comments
-mp num, --multiprocessing num : Execute using multiple processors, if not turned on, default to one, if num specified use that many, if num not specified use all
   
The model with execute the Reference ET module and operate for each meteorological station represented in the RedRiverMetaData.xlsx file on the ETCellsProperties worksheet in the Ref ET MET ID column (Column C).  After execution, several .csv files will be available in the data\climatechange\daily_ret directory, one for each meteorological station represented in the above worksheet.  In addition, several summaries are included, monthly in the data\climatechange\monthly_ret directory, and annual in the data\climatechange\annual_ret directory.
   
### Crop ET
   
The Crop ET module is executed next.  The command line is:
   
python ..\et-demands\cropET\bin\run_cet.py -i csv_cet_dri.ini –mp
   
Command arguments are:
   
-h, --help : Show the help message then exit
-i PATH, --ini PATH: Intialization file path; If omitted, script will prompt
-vb, --VB : Mimic calculations in VB code
-d, --debug : Save debug level comments to debug.txt file
-c CellID, --metid CellID : Specify a particular single ET Cell ID to run
-v, --verbose : Display information level comments
-mp num, --multiprocessing num : Execute using multiple processors, if not turned on, default to one, if num specified use that many, if num not specified use all
   
The model will execute the Crop ET module and operate for each ETCell represented in the RedRiverMetaData.xlsx file on the ETCerllsProperties worksheet in the ET Cell ID column (Column A).    After execution, several .csv files will be available in the data\climatechange\daily_cet directory, one for each ET Cell represented in the above worksheet.  In addition, several summaries are included, monthly in the data\climatechange\monthly_cet directory, and annual in the data\climatechange\annual_cet directory.
   
### Area ET
   
Finally, the Area ET module is executed.  The command line is:
   
python ..\et-demands\areaET\bin\run_aet.py -i dri_aet_csv.ini –mp
    
Command arguments are:
    
-h, --help : Show the help message then exit
-i PATH, --ini PATH: Intialization file path; If omitted, script will prompt
-d, --debug : Save debug level comments to debug.txt file
-c CellID, --metid CellID : Specify a particular single ET Cell ID to run
-v, --verbose : Display information level comments
-mp num, --multiprocessing num : Execute using multiple processors, if not turned on, default to one, if num specified use that many, if num not specified use all
   
The model will execute the Area ET module and operate for each ETCell represented in the RedRiverMetaData.xlsx file on the ETCerllsProperties worksheet in the ET Cell ID column (Column A).    After execution, several .csv files will be available in the data\climatechange\daily_out_aet directory, one for each ET Cell represented in the above worksheet.  In addition, several summaries are included, monthly in the data\climatechange\monthly_out_cet directory, and annual in the data\climatechange\annual_out_cet directory.
   
# Conclusion
   
The current version of the Python PM model is robust and well represents the current state of the art in ET estimation.  In addition to the model itself, several other activities are required to successfully execute a basin ET survey, including the acquisition of appropriate meteorological data, possible estimation of solar radiation data using the Thornton-Running equation (meaning the user needs to be able to accurately estimate the required coefficients), cropping data; including crop types and acreages and finally, the calibration of the model for accurate use in the area of interest.  The execution of the ET modules outlined herein in simple and takes advantage of multiple processors to make the calculations fast and easy.  For further information regarding the development and execution of the Python PM ET Model, please see the document: 
   
T:\WaterResources\PlanningOperations\D8500\apps\pythonApps\bortsc\docs\PythonETApplications.pdf

# References
Allen, Richard G., Pereira, Luis S., Raes, Dirk, Smith, Martin, 1998, [FAO Irrigation and Drainage Paper No. 56 – Crop Evapotranspiration] (https://github.com/usbr/et-demands/blob/master/references/Allen%20et%20al%20(2006)%20FAO%20Irrigation%20and%20Drainage%20Paper%20No.%2056%20-%20Crop%20Evapotranspiration.pdf) (guidelines for computing crop water requirements), 333pp.

