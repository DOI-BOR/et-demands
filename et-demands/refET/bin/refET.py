import math
import numpy as np
import refet

class refET:

    def __init__(self, b0, b1, b2):
        """ """

        # Thorton and Running Coefficients

        self.TR_b0 = b0
        self.TR_b1 = b1
        self.TR_b2 = b2

        # these were defined as 'static' variable within a Function in the VB.net version

        self._Tp3 = 0.0 # static
        self._Tp2 = 0.0 # static
        self._Tp1 = 0.0 # static
        self._ndays = 0 # static
        self._lastDay = 0 # static

    def _rs_daily(self, doy, tmax, tmin, tdew, elev, latitude, montmax, montmin):
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
        lat : scalar or array_like of shape(M, )
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
        ra = refet.calcs._ra_daily(latRad, doy, method='refet')

        # Saturation vapor pressure
        es = refet.calcs._sat_vapor_pressure(tdew)

        # Air pressure from elevation
        pair = refet.calcs._air_pressure(elev, method='refet')

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
        if TR_b0 is None: TR_b0 = self.TR_b0
        if TR_b1 is None: TR_b1 = self.TR_b1
        if TR_b2 is None: TR_b2 = self.TR_b2
        BTR = TR_b0 + TR_b1 * math.exp(TR_b2 * montdiff)

        rs = rso * (1 - 0.9 * math.exp(-BTR * tdiff ** 1.5))
        return rs

    def _et_hargreaves_samani(self, doy, tmax, tmin, latitude):
        """Hargreaves Samani reference ET (https://doi.org/10.13031/2013.26773)

        Parameters
        ----------
        doy : scalar or array_like of shape(M, )
            Day of year.
        tmax : scalar or array_like of shape(M, )
            Daily maximum air temperature [C].
        tmin : scalar or array_like of shape(M, )
            Daily minimum air temperature [C].
        latitude : scalar or array_like of shape(M, )
            Latitude [deg].

        Returns:
            hsRefET: Hargreaves Samani referencet ET
        """
        tmean = 0.5 * (tmax + tmin)

        # compute latent heat of vaporization

        lmbda = self._latent_heat_vapor(tmean)

        # Latutude in radians
        latRad = latitude * math.pi / 180.0  # Lat is station latitude in degrees

        # Extraterrestrial radiation
        ra = refet.calcs._ra_daily(latRad, doy, method='refet')

        if tmax < tmin:
            hsRefET = 0.0
        else:
            hsRefET = 0.0023 * (tmax - tmin)**0.5 * ra * (tmean + 17.8) # same units as Ra
        hsRefET = hsRefET / lmbda * 1000000.0 # mm/day
        return hsRefET

    def ComputePenmanRefETs(self, yr, mo, da, doy, time_step, tmax, tmin, tdew, rs, u24, elev, latitude):
        """ Compute reference ET by Penman methods

        Args:
            doy: day of year
            yr: year
            mo: month
            da: day
            time_step: time step
            tmax: maximum temperature
            tmin: minimum temperature
            Rs: incident solar radiation
            u24: wind
            elevm: elevation in meters
            latitude: latitude

        Returns:
            Penman, PreTay, KimbPeng, ASCEr, ASCEo, FAO56PM, KimbPen: Penman reference ET's
            hsRefET: Hargreaves Samani referencet ET
        """
        # Mean daily temperature
        tmean = 0.5 * (tmax + tmin)

        # Latent heat of vaporization
        lmbda = self._latent_heat_vapor(tmean)

        # Latutude in radians
        latRad = latitude * math.pi / 180.0

        # Extraterrestrial radiation
        ra = refet.calcs._ra_daily(latRad, doy, method='refet')

        # Slope of the saturation vapor pressure-temperature curve
        Delta = refet.calcs._es_slope(tmean, method='refet')
        es = refet.calcs._sat_vapor_pressure(tdew)
        pair = refet.calcs._air_pressure(elev, method='refet')
        psy = self._psychro_const(pair, lmbda) # kPa/C

        # Estimate clear sky radiation (Rso)
        rso = refet.calcs._rso_daily(ra, es, pair, doy, latRad)

        # compute net radiation

        # Rn82 was passed byRef

        Rn56, Rn82 = self._rn_fao56(elev, latitude, doy, ra, rs, rso, tmax, tmin, es)

        # If Ref <= 0.5 Then ht = GrassHt Else ht = AlfHt

        AlfHt = 0.5 # m
        GrassHt = 0.12 # m
        htr = AlfHt
        ht = GrassHt # assume default is grass

        # Assuming weather measurement surface is that of reference

        site_hto = ht
        site_htr = htr

        # set anemometer height

        anemom = 2 # m

        # Theorectical adjustment (Allen) over grass is:
        # d = .67 * GrassHt  'site_ht 'modified 12/21/99 to reflect wind required over grass in std eqns.
        # zom = .123 * GrassHt  'site_ht

        # U242 = U24 * Log((2 - d) / zom) / Log((anemom - 0.67 * site_hto) / (0.123 * site_hto))
        # for Consuse comp, all wind is at 2 m:

        u242 = u24
        U242r = u24

        # 1982 Kimberly Penman

        G82, G82o, GFAO, GFAOr = self.ComputeSoilHeat(da, time_step, tmean, Rn56, Rn82) # modified 6/24/99
        ea = (refet.calcs._sat_vapor_pressure(tmax) + refet.calcs._sat_vapor_pressure(tmin)) * 0.5
        penmans = self.Penmans(latitude, doy, pair, Rn56, Rn82, es, ea, lmbda, Delta, psy, tmean, G82, G82o, GFAO, GFAOr, u242)
        # Penman, PreTay, KimbPeng, ASCEPMstdr, ASCEPMstdo, FAO56PM, KimbPen = penmans
        return penmans

    def _latent_heat_vapor(self, tmean):
        """Latent heat of vaporization

        Parameters
        ----------
        tmean : scalar or array_like of shape(M, )
            mean daily temperature [C]

        Returns
        -------
            lmbda : ndarray
                latent heat of evaporation [J kg-1]

        Notes
        -----
        In ASCE-NWRI (2005):
            A constant value of lmbda = 2.45 MJ kg-1 is used

        """
        lmbda = 2500000.0 - 2360 * tmean  # J/Kg   Latent Heat of Vaporization
        return lmbda

    def _psychro_const(self, pair, lmbda):
        """Psychrometric constant (Eq.35 mod.)

        Parameters
        ----------
        pair : scalar or array_like of shape(M, )
        lambda : scalar or array_like of shape(M, )

        Returns
        -------
        psy : ndarray
            Psychrometric constant [kPa C-1].

        Notes
        -----
        In ASCE-NWRI (2005):
            This is modified from Eq. 35 as lmbda is not fixed

        """
        psy = 1013 * pair / 0.622 / lmbda # kPa/C  cp=1013 J/Kg/C
        return psy

    def _rn_fao56(self, elev, lat, doy, ra, rs, rso, tmax, tmin, es):
          """FAO 56 Net Radiation

          Parameters
          ----------
          elev : scalar or array_like of shape(M, )
              Elevation [m].
          lat : scalar or array_like of shape(M, )
              latitude [deg].
          doy : scalar or array_like of shape(M, )
              Day of year.
          ra : scalar or array_like of shape(M, )
              Daily extraterrestrial radiation [MJ m-2 d-1].
          rs : scalar or array_like of shape(M, )
              Measured solar radiation [MJ m-2 d-1].
          rso : scalar or array_like of shape(M, )
              Clear sky solar radiation [MJ m-2 d-1].
          tmax : scalar or array_like of shape(M, )
               Daily maximum air temperature [C].
          tmin : scalar or array_like of shape(M, )
               Daily minimum air temperature [C].
          es : scalar or array_like of shape(M, )
                Saturated vapor pressure [kPa].

          Returns
          -------

              FAO56NR: FA056 net radiation
              Rn82: Rn82 net radiation

         Notes
         -----

          """
          j = doy
          if lat < 0:
              j = doy - 182
              if j < 1:
                  j = j + 365
          Rna1 = 0.26 + 0.1 * math.exp(-(0.0154 * (j - 180)) ** 2)
          Rso75 = 0.75 * ra
          Rso56 = (0.75 + 0.00002 * elev) * ra # 4/6/94
          if rso > 0:
              RsRso = rs / rso # 24-hours
          else:
              RsRso = 0.7
          if Rso56:
              RsRso56 = rs / Rso56 # 24-hours
          else:
              RsRso56 = 0.7
          RsRso = max(0.2, min(RsRso, 1.0))
          RsRso56 = max(0.2, min(RsRso56, 1.0))
          RsRso2use = RsRso # useRso based on sun angle and water vapor as of 9/25/2000
          if RsRso2use > 0.7:
              Rna = 1.126
              Rnb = -0.07
          else:
              Rna = 1.017
              Rnb = -0.06
          Rbo = 0.000000004903 * 0.5 * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) * (Rna1 - 0.139 * math.sqrt(es))
          Rb = (Rna * RsRso2use + Rnb) * Rbo
          alpha = 0.29 + 0.06 * math.sin((j + 96) / 57.3)
          Rn82 = (1 - alpha) * rs - Rb

          # FAO 56 Net Radiation computation

          Rbo56 = 0.000000004903 * 0.5 * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) * (0.34 - 0.14 * math.sqrt(es))
          Rnl56 = (1.35 * RsRso2use - 0.35) * Rbo56
          FAO56NR = (1 - 0.23) * rs - Rnl56
          return FAO56NR, Rn82

    # soil heat flux

    def ComputeSoilHeat(self, da, time_step, tmean, Rn56, Rn82): # modified 6/24/99
        """ Computes soil heat flux

        Args:
            da: day
            time_step: time step
            tmean: average temperature
            Rn56: FAO56 net radiation
            Rn82: Rn82 net radiation

        Returns:
            G82:
            G82o:
            GFAO:
            GFAOr:
        """
        # ByRef G82 As Double, ByRef G82o As Double, ByRef GFAO As Double, ByRef GFAOr As Double
        # Static Tp3, Tp1, Tp2 As Double
        # Static ndays, lastDay As Long
        # --> 'Static' means value is persistant between calls, ie, retains its value
        # use class variable to make static
        if time_step == 'day':   # Daily or Monthly Time Step  ' added 10/13/90  start if1
            if self._lastDay < 1:  # start if2
                G82 = 0.0
                G82o = 0.0
                GFAO = 0.0
                GFAOr = 0.0
                self._Tp3 = 0.0
                self._Tp2 = 0.0
                self._Tp1 = 0.0
                self._ndays = 0
            else:
                if (self._lastDay == 15 and da == 15) or (self._lastDay == 0 and da == 0):
                    # monthly heat flux

                    G82 = 0.0 # assume monthly heat flux is zero
                    G82 = 0.14 * (tmean - self._Tp1) # added 3/28/94  (use prior month) (FAO)
                    GFAO = G82
                    G82o = G82
                    GFAOr = G82
                else:
                    if self._ndays > 0:
                        G82 = (tmean - (self._Tp3 + self._Tp2 + self._Tp1) / self._ndays) * 0.3768 # MJ/m2/d
                    else:
                        G82 = 0.0
                    GFAO = 0.0
                    G82o = G82
                    GFAOr = GFAO
                #  Tp3 = Tp2   ' moved after end of this end if 3/28/94
                #  Tp2 = Tp1
                #  Tp1 = tmean
                #  ndays = ndays + 1
                #  IF ndays > 3 THEN ndays = 3
            self._lastDay = da
            self._Tp3 = self._Tp2 # moved here 3/28/94
            self._Tp2 = self._Tp1
            self._Tp1 = tmean
            self._ndays = self._ndays + 1
            self._ndays = min(self._ndays, 3)
        else: # hourly time step (assumed)
            # changed Rn to Rn82 dlk 01/27/2016

            if Rn82 >= 0:  # added 10/13/90  (units are MJ/m2/day, but will be W/m2 on console.writeout)
                # If Ref < 0.5 Then
                G82o = 0.1 * Rn82 # Clothier (1986), Kustas et al (1989) in Asrar Remote Sens. Txt

                # for full cover alfalfa (but high for alfalfa. use for grass

                # Else
                G82 = 0.04 * Rn82 # for alfalfa reference based on Handbook Hydrol.
                # End If
            else:
                # If Ref < 0.5 Then
                G82o = Rn82 * 0.5 # R.Allen obersvations for USU Drainage Farm.  Alta Fescue

                # crop near full cover.  Adj. Soil heat flux assuming that
                # therm. cond. in top 100 mm was 2 MJ/m2/C.

                # Else
                G82 = Rn82 * 0.2 # alfalfa
                # End If
                # GFAO = G
            if Rn56 >= 0:      # added 10/13/90  (units are MJ/m2/day, but will be W/m2 on console.writeout)
                # If Ref < 0.5 Then
                GFAO = 0.1 * Rn56 # Clothier (1986), Kustas et al (1989) in Asrar Remote Sens. Txt

                # for full cover alfalfa (fits grass better than alfalfa.  use for grass)

                # Else
                GFAOr = 0.04 * Rn56 # alfalfa reference based on Handbook Hydrol.
                # End If
            else:
                # If Ref < 0.5 Then
                GFAO = Rn56 * 0.5 # R.Allen obersvations for USU Drainage Farm.  Alta Fescue

                # crop near full cover.  Adj. Soil heat flux assuming that
                # therm. cond. in top 100 mm was 2 MJ/m2/C.

                # Else
                GFAOr = Rn56 * 0.2 # alfalfa
                # End If
        return G82, G82o, GFAO, GFAOr

    def Penmans(self, lat, doy, pressure, Rn56, Rn82, ed, ea, lmbda, delta, gamma, tmean, G82, G82o, GFAO, GFAOr, U242):
        """ Compute Penman based reference ET's

        Args:
            lat: latitude
            doy: day of year
            pressure: air pressure
            Rn56: FAO56 net radiation
            Rn82: Rn82 net radiation
            ed: saturation vapor pressure
            latentHeat: latent heat of evaporation
            gamma:
            tmean: average temperature
            G82:
            G82o:
            GFAO:
            GFAOr:
            U242: wind

        Returns:
            Penman, PreTay, KimbPeng, ASCEr, ASCEo, FAO56PM, KimbPen: Penman reference ET's
        """
        zero = 0.0
        j = doy
        if lat < 0:
            j = doy - 182
            if j < 1:
                j = j + 365
        ea_tmean = refet.calcs._sat_vapor_pressure(tmean)
        Awk = 0.4 + 1.4 * math.exp(-((j - 173) / 58) ** 2)
        Bwk = (0.007 + 0.004 * math.exp(-((j - 243) / 80) ** 2)) * 86.4 # for m/s
        RnEq = Rn82
        GEq = G82

        # 1982 Kimberly Penman

        KimbPen = (delta * (RnEq - GEq) + gamma * 6.43 * (ea - ed) * (Awk + Bwk * U242)) / (delta + gamma)
        KimbPen = KimbPen / lmbda * 1000000.0
        KimbPen = max(KimbPen, zero)
        GEq = G82o
        awkg = 0.3 + 0.58 *  math.exp(-((j - 170) / 45) ** 2) # Wright(1996) for grass
        bwkg = 0.32 + 0.54 * math.exp(-((j - 228) / 67) ** 2) # for m/s
        KimbPeng = (delta * (RnEq - GEq) + gamma * 6.43 * (ea - ed) * (awkg + bwkg * U242)) / (delta + gamma)
        KimbPeng = KimbPeng / lmbda * 1000000.0
        KimbPeng = max(KimbPeng, zero)

        # FAO-56 Penman-Monteith

        gamma56 = 0.000665 * pressure # kPa/C   May 17 1999
        RnEq = Rn56
        GEq = GFAO
        FAO56PM = (0.408 * delta * (RnEq - GEq) + gamma56 * 900 / (tmean + 273) * U242 * (ea - ed)) / (delta + gamma56 * (1 + 0.34 * U242)) #  may 17 1999 move before ea=fnes(tmean)
        FAO56PM = max(FAO56PM, zero)

        # Priestley-Taylor added 1/3/08 by Justin Huntington

        PreTay = 1.26 * (delta / (delta + gamma56) * (RnEq - GEq)) / lmbda * 1000000.0
        PreTay = max(PreTay, zero)

        # Penman 1948 withorig wind Rome wind function added 8/17/09 by Justin Huntington

        # Penman = ((Delta / (Delta + gamma56) * (RnEq - GEq)) + 6.43 * gamma56 / (Delta + gamma56) * (1 + 0.537 * U242) * (ea - ed))
        Penman = (((delta / (delta + gamma56) * (RnEq - GEq))) / lmbda * 1000000.0) + ((gamma56 / (delta + gamma56) * (0.26 * (1 + 0.537 * U242)) * ((ea_tmean * 10) - (ed * 10))))
        Penman = max(Penman, zero)

        # Penman = Penman / latentHeat * 1000000!

        # Reduced Forms ofASCE-PM (standardized).

        GEq = GFAOr
        ASCEPMstdr = (0.408 * delta * (RnEq - GEq) + gamma56 * 1600 / (tmean + 273) * U242 * (ea - ed)) / (delta + gamma56 * (1 + 0.38 * U242))
        ASCEPMstdr = max(ASCEPMstdr, zero)
        GEq = GFAO
        ASCEPMstdo = (0.408 * delta * (RnEq - GEq) + gamma56 * 900 / (tmean + 273) * U242 * (ea - ed)) / (delta + gamma56 * (1 + 0.34 * U242))
        ASCEPMstdo = max(ASCEPMstdo, zero)
        return  (Penman, PreTay, KimbPeng, ASCEPMstdr, ASCEPMstdo, FAO56PM, KimbPen)
##
# REMOVED TESTS
# ADD IN TRAVIS-CI TESTS
