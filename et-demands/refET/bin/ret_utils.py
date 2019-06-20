"""ret_utils.py
Defines meteorology, date, and logger functions
Called by met_nodes.py

"""

import sys
import os
import datetime
import logging
import pandas as pd
import numpy as np
import math
import refet

def valid_date(string_dt):
    """Check that date string is ISO format (YYYY-MM-DD)

    This function is used to check format of dates entered as command line arguments.

    Args:
        string_dt: input date string
    Returns:
        string_dt: output date string
    Raises:
        ArgParse ArgumentTypeError
    """
    try:
        input_dt = datetime.datetime.strptime(string_dt, "%Y-%m-%d")
        return string_dt
    except ValueError:
        msg = "Not valid date: '{0}'.".format(string_dt)
        raise argparse.ArgumentTypeError(msg)

def make_datetime_from_string(string_dt):
    """Makes datetime object from string

    This function is used to make datetime date from string of unknown format

    Args:
        string_dt: date string
    Returns:
        datetime
    """
    clean_string = string_dt.replace("-","").replace("/","").replace(" ","").replace("T","").strip()
    date_string = string_dt.replace("/","-").strip()
    if len(clean_string) < 7:
        try:
            the_date = datetime.datetime.strptime(date_string, '%Y-%m')
        except:
            try:
                the_date = datetime.datetime.strptime(date_string, '%m-%Y')
            except:
                the_date = None
    elif len(clean_string) < 9:
        try:
            the_date = datetime.datetime.strptime(date_string, '%Y-%m-%d')
        except:
            try:
                the_date = datetime.datetime.strptime(date_string, '%d-%m-%Y')
            except:
                the_date = None
    elif len(clean_string) < 11:
        try:
            the_date = datetime.datetime.strptime(date_string, '%Y-%m-%d-%H')
        except:
            try:
                the_date = datetime.datetime.strptime(date_string, '%d-%m-%Y-%H')
            except:
                try:
                    the_date = datetime.datetime.strptime(date_string, '%Y-%m-%d %H')
                except:
                    try:
                        the_date = datetime.datetime.strptime(date_string, '%d-%m-%Y %H')
                    except:
                        the_date = None
    else:
        the_date = None
    return the_date

def get_periods_given_dates_timedelta(start_dt, end_dt, time_delta):
    """ computes periods in date range

    Args:
        start_dt: starting datetime
        end_dt: ending datetime
        time_step: time_delta datetime.timedelta object
    Returns:
        np: integer number of periods
    """
    if time_delta.total_seconds() > 2678400:
        np = end_dt.year - start_dt.year
    else:
        if time_delta.total_seconds() > 86400:
            np = 12 * (end_dt.year - start_dt.year - 1) + end_dt.month - start_dt.month + 12
        else:
            np =  int((end_dt - start_dt).total_seconds() / time_delta.total_seconds())
    return np

def get_periods_given_dates_timestep(start_dt, end_dt, timestep, ts_quantity = 1):
    """ computes periods in date range

    Args:
        start_dt: starting datetime
        end_dt: ending datetime
        timestep: text DMI timestep as minute, hour, day, week, month, year
        ts_quantity: quantity of timestep - 15 for 15 minutes; 6 hour for 6 hours; 12 for 12 hours; otherwise 1
    Returns:
        np: integer number of periods
    """
    if 'year' in timestep.lower():
        np = end_dt.year - start_dt.year
    elif 'month' in timestep.lower():
            np = 12 * (end_dt.year - start_dt.year - 1) + end_dt.month - start_dt.month + 12
    elif 'day' in timestep.lower():
        time_delta = datetime.timedelta(days = 1)
        np =  int((end_dt - start_dt).total_seconds() / time_delta.total_seconds())
    elif 'hour' in timestep.lower():
        time_delta = datetime.timedelta(hours = 1) * ts_quantity
        np =  int((end_dt - start_dt).total_seconds() / time_delta.total_seconds())
    elif 'minute' in timestep.lower():
        time_delta = datetime.timedelta(days = 1) * ts_quantity
        np =  int((end_dt - start_dt).total_seconds() / time_delta.total_seconds())
    elif 'week' in timestep.lower():
        time_delta = datetime.timedelta(weeks = 1)
        np =  int((end_dt - start_dt).total_seconds() / time_delta.total_seconds())
    elif 'day' in timestep.lower():
        time_delta = datetime.timedelta(days = 1)
        np =  int((end_dt - start_dt).total_seconds() / time_delta.total_seconds())
    else:
        np = end_dt.year - start_dt.year
    return np

def read_average_monthly_wb_data(wbname, wsname, skip_lines = 1):
    """read average monthly data from a workbook
    Args:
        wbname: workbook name
        wsname: worksheet name
        skip_lines: rows of file to skip
    Returns:
        boolean: sucess flag
        d: average monthly values by site
    """
    d = {}
    try:
        df = pd.read_excel(wbname, sheet_name = wsname, index_col = 0, header = None,
                skiprows = skip_lines, na_values = ['NaN'])
        df.drop(list(df.columns)[0], axis = 1, inplace = True)

        # move data into a dictionary    (Unable to get df.to_dict to work)

        for node_id, row in df.iterrows():
            d[node_id] = row.values.tolist()
        return True, d
    except:
        logging.error('\nERROR: ' + str(sys.exc_info()[0]) + ' occurred reading average monthly data from worksheet ' +  wsname + ' of workbook ' + wbname + '\n')
        return False, d

def read_average_monthly_csv_data(fn, skip_lines = 1, delimiter = ","):
    """read average monthly data from a delimited text file
    Args:
        fn: file name
        skip_lines: rows of file to skip
        delimiter: values separator
    Returns:
        boolean: sucess flag
        d: average monthly values by site
    """
    d = {}
    try:
#        df = pd.read_csv(fn, engine = 'python', index_col = 0, header = None,
        df = pd.read_csv(fn, engine = 'python', index_col=0, header=None,
                skiprows=skip_lines, sep=delimiter)
        df.drop(list(df.columns)[0], axis = 1, inplace = True)

        # move data into a dictionary    (Unable to get df.to_dict to work)

        for node_id, row in df.iterrows():
            d[node_id] = row.values.tolist()
        return True, d
    except:
        logging.error('\nERROR: ' + str(sys.exc_info()[0]) + ' occurred reading average delimited text data from ' + fn + '\n')
        return False, d

def read_average_monthly__text_data(fn, skip_lines = 1, delimiter = ","):
    """read average monthly data from a delimited text file
    Args:
        fn: file name
        skip_lines: rows of file to skip
        delimiter: values separator
    Returns:
        boolean: sucess flag
        d: average monthly values by node_id
    """
    d = {}
    try:
        for i, line in enumerate(open(fn)):
            if i < skip_lines: continue
            line_values = line.split(delimiter)
            node_id = line_values[0]
            d[node_id] = [float(i) for i in line_values[2:14]]
        return True, d
    except: return False, d

def fill_from_avg_monthly(daily_value, avg_monthly_value):
    """file daily values from average monthly values
    Args:
        daily_value: existing daily value
        avg_monthly_value: average monthly value
    Returns:
        daily_value: filled daily value
    """
    if pd.isnull(daily_value):
        return avg_monthly_value
    else:
        return daily_value

def is_winter(et_cell, foo_day):
    """Determine if input day is in winter month

    Args:
        et_cell (): ETCell object
        foo_day (): Placeholder object

    Returns:
        boolean that is True if input day is in winter month
    """
    if et_cell.stn_lat > 0 and (foo_day.month < 4 or foo_day.month > 10):
        ## Northern hemisphere
        return True
    else:
        ## Southern hemisphere
        return False

def max_max_temp(max_temp):
    """Adjust maximum temperature to be less than 120F"""
    return min(max_temp, (120.0 - 32.0) * 5.0 / 9.0)

def max_min_temp(min_temp):
    """Adjust minimum temperature to be less than 90F"""
    return min(min_temp, (90.0 - 32.0) * 5.0 / 9.0)

def avg_two_arrays(c1, c2):
    """Computes average of two NumPy arrays or df columns

    Args:
        c1: column 1 values
        c2: column 2 values

    Returns:
        NumPy array of average values
    """
    return 0.5 * (c1 + c2)

def rs_daily(doy, tmax, tmin, tdew, elev, latitude, montmax, montmin, TR_b0, TR_b1, TR_b2):
    """Estimated incident solar radiation

    Parameters
    ----------
    doy : scalar or array_like of shape(M, )
        Day of year.
    tmax : scalar or array_like of shape(M, )
        Daily maximum air temperature [C].
    tmin : scalar or array_like of shape(M, )
        Daily minimum air temperature [C].
    elev : scalar or array_like of shape(M, )
        Elevation [m].
    latitude : scalar or array_like of shape(M, )
        Latitude [radians]                           # currently in deg. also, name change to lat throws error - fix both
    montmax : scalar or array_like of shape(M, )
        Monthly mean maximum air temperature [C].
    montmin : scalar or array_like of shape(M, )
        Monthly mean minimum air temperature [C].
    TR_b0 : scalar or array_like of shape(M, )
        Thronton and Running b0 coefficient.
    TR_b1 : scalar or array_like of shape(M, )
        Thronton and Running b1 coefficient.
    TR_b2 : scalar or array_like of shape(M, )
        Thronton and Running b2 coefficient.

    Returns
    -------
    rs : ndarray
        Estimated incident solar radiation [MJ m-2 d-1].

    """

    # Latutude in radians
    latRad = latitude * math.pi / 180.0  # Lat is station latitude in degrees

    # Extraterrestrial radiation
    ra = refet.calcs._ra_daily(latRad, doy, method="refet")

    # Saturation vapor pressure
    es = refet.calcs._sat_vapor_pressure(tdew)

    # Air pressure from elevation
    pair = refet.calcs._air_pressure(elev, method="refet")

    # Clear sky solar radiation
    rso = refet.calcs._rso_daily(ra, es, pair, doy, latRad)

    # Temperature difference
    tdiff = tmax - tmin          # temp difference in C

    # Monthly mean temperature difference
    montdiff = montmax - montmin # long term monthly temp difference in C

    # Temperature difference of at least 0.1
    tdiff = max(0.1, tdiff)
    montdiff = max(0.1, montdiff)

    # Thornton and Running parameter
    BTR = TR_b0 + TR_b1 * math.exp(TR_b2 * montdiff)

    rs = rso * (1 - 0.9 * math.exp(-BTR * tdiff ** 1.5))
    return rs

def tdew_from_avg_monthly_Ko(daily_tdew, daily_tmin, avg_monthly_Ko):
    """Computes dewpoint temperature from daily minimum temperature and average monthly Ko (dew point depression)

    Parameters
    ---------
    daily_tdew :
        existing daily tdew
    daily_tmin :
        daily tmin
    avg_monthly_Ko :
        average monthly Ko

    Returns
    -------
    daily_value :
        filled daily tdew

    """

    if pd.isnull(daily_tdew):
        return daily_tmin - avg_monthly_Ko
    else:
        return daily_tdew

def _dewpoint_temperature(ea):
    """Dew point temperature (Eq. 8)

    Parameters
    ----------
    ea : ndarray
        Actual vapor pressure [kPa].

    Returns
    -------
    tdew : scalar or array_like of shape(M, )
        Dew point temperature [C].

    """

    return (237.3 * np.log(ea / 0.6108)) / (17.27 - np.log(ea / 0.6108))

# renamed from q_from_ea
def _specific_humidity(ea, pair):
    """"Specific humidity from actual vapor pressure

    Parameters
    ----------
    ea : ndarray
        Actual vapor pressure [kPa].
    pair : scalar or array_like of shape(M, )
        Air pressure [kPa].

    Returns
    -------
    q : scalar or array_like of shape(M, )
        Specific humidity [kg/kg].

    Notes
    -----
    ea = q * pair / (0.622 + 0.378 * q)

    """

    return 0.622 * ea / (pair - 0.378 * ea)

# renamed from es_ice_from_t
def _es_ice(temperature):
    """Saturation vapor pressure over ice from temperature

    Parameters
    ----------
    temperature : scalar or array_like of shape(M, )
        Air temperature [C].

    Returns
    -------
    es_ice : ndarray
        Saturation vapor pressure [kPa].

    Notes
    -----
    Murray (1967) equation for sat. vap pressure over ice

    """

    return 0.6108 * np.exp((21.87 * t) / (t + 265.5))

def tdew_from_ea(ea):
    """Dew point temperature from vapor pressure

    Parameters
    -----------
        temperature: NumPy array of temperatures [C]

    Returns
    -------
        tdew : ndarray
            Dew point temperature [C].

    """

    return (237.3 * np.log(ea / 0.6108)) / (17.27 - np.log(ea / 0.6108))

def file_logger(logger = logging.getLogger(''), log_level = logging.DEBUG,
                output_ws = os.getcwd()):
    """Create file logger"""
    logger.setLevel(log_level)
    log_file = logging.FileHandler(
       os.path.join(output_ws, 'debug.txt'), mode = 'w')
    log_file.setLevel(log_level)
    log_file.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(log_file)
    return logger

def console_logger(logger = logging.getLogger(''), log_level = logging.INFO):
    """Create console logger"""
    import sys
    logger.setLevel(log_level)
    log_console = logging.StreamHandler(stream = sys.stdout)
    log_console.setLevel(log_level)
    log_console.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(log_console)
    return logger

def parse_int_set(nputstr = ""):
    """Return list of numbers given string of ranges

    http://thoughtsbyclayg.blogspot.com/2008/10/parsing-list-of-numbers-in-python.html
    """
    selection = set()
    invalid = set()
    # tokens are comma seperated values

    tokens = [x.strip() for x in nputstr.split(',')]
    for i in tokens:
        try:
            # typically tokens are plain old integers

            selection.add(int(i))
        except:
            # if not, then it might be range

            try:
                token = [int(k.strip()) for k in i.split('-')]
                if len(token) > 1:
                    token.sort()
                    # we have items seperated by dash
                    # try to build valid range
                    first = token[0]
                    last = token[len(token)-1]
                    for x in range(first, last+1):
                        selection.add(x)
            except:
                # not an int and not range...

                invalid.add(i)
    return selection

def is_leap_year(year_to_test):
    """Check if year is a leap year

        Parameters
        ---------
        year_to_test : int
            year to test

        Returns
        : boolean
            True
            False

        """

    if year_to_test % 4 == 0 and year_to_test %100 != 0 or year_to_test % 400 == 0:
        return True
    else:
        return False

def get_ts_freq(time_step, ts_quantity, wyem = 12):
    """ et pandas time frequency given time_step and ts_quantity

     Args:
        time_step: RiverWare style string timestep
        ts_quantity: Interger number of time_steps's in interval

    Returns:
        ts_freq: pandas time frequency
    """
    ts_freq = None
    if time_step == 'day':
        ts_freq = "D"
    elif time_step == 'year':
        ts_freq = water_year_agg_func(wyem)
    elif time_step == 'month':
        ts_freq = "M"
    elif time_step == 'hour':
        if ts_quantity == 1:
            ts_freq = "H"
        else:
            ts_freq = str(ts_quantity) + "H"
    elif time_step == 'minute':
        if ts_quantity == 1:
            ts_freq = "T"
        else:
            ts_freq = str(ts_quantity) + "T"
    elif time_step == 'week':
        ts_freq = "W"
    else:
        logging.error('\nERROR: Timestep {} and ts quantity {} are an invalid combination', format(time_step, ts_quantity))
    return ts_freq

def water_year_agg_func(wyem):
    """Sets annual aggregation function for water year end month
    Args:
        wyem: Water Year End Month
    Return; Water year aggregation function
    """
    ann_freqs = ['A-JAN', 'A-FEB', 'A-MAR', 'A-APR', 'A-MAY', 'A-JUN'] + \
                ['A-JUL', 'A-AUG', 'A-SEP', 'A-OCT', 'A-NOV', 'A-DEC']
    return ann_freqs[wyem - 1]

def make_dt_index(time_step, ts_quantity, start_dt, end_dt, wyem = 12):
    """ Make a pandas DatetimeIndex from specified dates, time_step and ts_quantity

     Args:
        time_step: RiverWare style string timestep
        ts_quantity: Interger number of time_steps's in interval
        start_dt: starting date time
        end_dt: ending date time
        wyem: Water Year End Month

    Returns:
        dt_index:pandas DatetimeIndex
    """
    dt_index = None
    if time_step == 'day':
        dt_index =pd.date_range(start_dt, end_dt, freq = "D", name = "date")
    elif time_step == 'year':
        dt_index = pd.date_range(start_dt, end_dt, freq = water_year_agg_func(wyem), name = "date")
    elif time_step == 'month':
        dt_index = pd.date_range(start_dt, end_dt, freq = "M", name = "date")
    elif time_step == 'hour':
        if ts_quantity == 1:
            dt_index =pd.date_range(start_dt, end_dt, freq = "H", name = "date")
        else:
            dt_index = pd.date_range(start_dt, end_dt, freq = str(ts_quantity) + "H", name = "date")
    elif time_step == 'minute':
        if ts_quantity == 1:
            dt_index = pd.date_range(start_dt, end_dt, freq = "T", name = "date")
        else:
            dt_index = pd.date_range(start_dt, end_dt, freq = str(ts_quantity) + "T", name = "date")
    elif time_step == 'week':
        dt_index = pd.date_range(start_dt, end_dt, freq = "W", name = "date")
    else:
        logging.error('\nERROR: Timestep {} and ts quantity {} are an invalid combination', format(time_step, ts_quantity))
    return dt_index

def make_ts_dataframe(time_step, ts_quantity, start_dt, end_dt, wyem = 12):
    """ Make a pandas dataframe from specified dates, time_step and ts_quantity

     Args:
        time_step: RiverWare style string timestep
        ts_quantity: Interger number of time_steps's in interval
        start_dt: starting date time
        end_dt: ending date time
        wyem: Water Year End Month

    Returns:
        Empty pandas datafame wihh indexed dates
    """
    ts_dataframe = None
    if time_step == 'day':
        ts_dataframe = pd.DataFrame(index = pd.date_range(start_dt, end_dt, freq = "D", name = "date"))
    elif time_step == 'year':
        ts_dataframe = pd.DataFrame(index = pd.date_range(start_dt, end_dt, freq = water_year_agg_func(wyem), name = "date"))
    elif time_step == 'month':
        ts_dataframe = pd.DataFrame(index = pd.date_range(start_dt, end_dt, freq = "M", name = "date"))
    elif time_step == 'hour':
        if ts_quantity == 1:
            ts_dataframe = pd.DataFrame(index = pd.date_range(start_dt, end_dt, freq = "H", name = "date"))
        else:
            ts_dataframe = pd.DataFrame(index = pd.date_range(start_dt, end_dt, freq = str(ts_quantity) + "H", name = "date"))
    elif time_step == 'minute':
        if ts_quantity == 1:
            ts_dataframe = pd.DataFrame(index = pd.date_range(start_dt, end_dt, freq = "T", name = "date"))
        else:
            ts_dataframe = pd.DataFrame(index = pd.date_range(start_dt, end_dt, freq = str(ts_quantity) + "T", name = "date"))
    elif time_step == 'week':
        ts_dataframe = pd.DataFrame(index = pd.date_range(start_dt, end_dt, freq = "W", name = "date"))
    else:
        logging.error('\nERROR: Timestep {} and ts quantity {} are an invalid combination', format(time_step, ts_quantity))
    return ts_dataframe
