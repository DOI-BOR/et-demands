=================
Model Description
=================
The ET-Demands package

-----
RefET
-----

Reference evapotranspiration is calculated according to the ASCE Standardized Reference Evapotranspiration Equation `(ASCE, 2005) <https://doi.org/10.1061/9780784408056>`_.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ASCE Standardized Reference Evapotranspiration Equation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. math::

   ET_{sz} =\frac{0.408 \Delta (R_n-G) + \gamma \frac{C_n}{T_{avg} + 273}u_2 (e_s-e_a)}{\Delta + \gamma(1+C_d u_2)}

where:

ET\ :sub:`sz` = standardized reference crop evapotranspiration for short ET\ :sub:`os` or tall ET\ :sub:`rs` surfaces (mm d\ :sup:`-1` for daily time steps or mm h\ :sup:`-1` for hourly time steps)

R\ :sub:`n` = calculated net radiation at the crop surface (MM m\ :sup:`-2` d\ :sup:`-1` for daily time steps or MM m\ :sup:`-2` h\ :sup:`-1` for hourly time steps)

G = soil heat flux density at the soil surface (MM m\ :sup:`-2` d\ :sup:`-1` for daily time steps or MM m\ :sup:`-2` h\ :sup:`-1` for hourly time steps)

T\ :sub:`avg` = mean daily or hourly air temperature at 1.5 to 2.5-m height (°C)

u\ :sub:`2` = calculated net radiation at the crop surface

e\ :sub:`s` = saturation vapor pressure at 1.5 to 2.5-m height (kPa)

e\ :sub:`a` = mean actual vapor pressure at 1.5 to 2.5-m height (kPa)

Δ = slope of the saturation vapor pressure-temperature curve (kPa °C\ :sup:`-1`)

γ = psychrometric constant (kPa °C\ :sup:`-1`)

C\ :sub:`n` = numerator constant that changes with reference type and calculation time step (K mm s\ :sup:`3` Mg\ :sub:`-1` d\ :sup:`-1` for daily time steps or K mm s\ :sup:`3` Mg\ :sub:`-1` h\ :sup:`-1` for hourly time steps)

C\ :sub:`d` = denominator constant that changes with reference type and calculation time step (s m\ :sup:`-1`)

Units for the 0.408 coefficient are m\ :sup:`2` mm MJ\ :sup:`-1`.

^^^^^^^^^^^^
Air Pressure
^^^^^^^^^^^^

.. math::

   P = 101.3 \times \left(\frac{293.15 - 0.0065z}{ 293.15} \right)^{(9.80665 / (0.0065 \times 286.9)}

where:

P = mean atmospheric pressure at station elevation (kPa)

z = station elevation above mean sea level (m)

This equation differs slightly from ASCE 2005 as it reflects full precision per Dr. Allen (pers. comm.).

^^^^^^^^^^^^^^^^^^^^
Mean Air Temperature
^^^^^^^^^^^^^^^^^^^^
From ASCE (2005) it is preferable to use the mean of daily minimum and daily maximum temperature as the mean daily temperature as opposed to the mean of hourly temperatures.


.. math::

   T_{avg} = \frac{T_{min} + T_{max}}{2}

where:

T\ :sub:`avg` = mean daily air temperature (°C)

T\ :sub:`min` = minimum daily air temperature (°C)

T\ :sub:`max` = maximum daily air temperature (°C)


^^^^^^^^^^^^^^^^^^^^^^^^^
Saturation Vapor Pressure
^^^^^^^^^^^^^^^^^^^^^^^^^

.. math::

   e_s = 0.6108 \times \exp \left( \frac{17.27T_{avg}}{T_{avg} + 237.3} \right)


where:

^^^^^^^^^^^^^^^^^^^^^^^^^^^
Latent Heat of Vaporization
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. math::

   \lambda = 2500000 - 2360 \times T_{avg}

where:

λ = latent heat of vaporization (MJ MJ kg\ :sup:`-1`)

T\ :sub:`avg` = mean daily air temperature (°C)

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Slope of the Saturation Vapor Pressure-Temperature Curve
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. math::
   \Delta = 4098 \times \frac{0.6108 \times \exp \left( \frac{17.27T_{avg}}{T_{avg} + 237.3} \right)}{\left(T_{avg} + 237.3\right)^2}

where:

Δ = slope of the saturation vapor pressure-temperature curve (kPa °C\ :sup:`-1`)

T\ :sub:`avg` = mean daily air temperature (°C)

^^^^^^^^^^^^^^^^^^^^^
Actual Vapor Pressure
^^^^^^^^^^^^^^^^^^^^^

.. math::
   e_a =

where:

Δ = slope of the saturation vapor pressure-temperature curve (kPa °C\ :sup:`-1`)

T\ :sub:`avg` = mean daily air temperature (°C)



^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Thornton and Running Solar Radiation Estimate
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The calculation of ET\ :sub:`sz` requires net radiation at the crop surface. When this is not available, net radiation can be estimated using the approach presented by Thornton and Running `(Thornton and Running, 1999) <https://doi.org/10.1016/S0168-1923(98)00126-9>`_.

The calculation of clear sky radiation

.. math::

   inc_{Rs} =cs_{Rso} \times (1 - 0.9)


incRs = csRSo * (1 - 0.9 * math.exp(-BTR * dt ** 1.5))


This equation requires the parameter B, which

.. math::

   B = b_0 + b_1 \times \exp(-b_2 \times \overline{\Delta T})

For arid stations, [REFERENCE FOR THESE COEFFICIENTS]

b\ :sub:`0` = 0.023

b\ :sub:`1` = 0.1

b\ :sub:`2` = 0.2

b\ :sub:`0`, b\ :sub:`1`, and b\ :sub:`2` are provided by the user. [DISCUSSION OF THESE PARAMETERS, AND HOW TO GET THEM]


^^^^^^^^^^^^^^^^^^^^
Windspeed Adjustment
^^^^^^^^^^^^^^^^^^^^
The standardized reference crop evapotranspiration equation assumes a 2-m height windspeed. Windspeed measured at different heights can be approximated as

.. math::

   u_2 = u_z + \frac{4.87}{\ln\left(67.8 z_w - 5.42 \right)}

where:

u\ :sub:`2` = wind speed at 2 m above ground surface (m s\ :sup:`-1`)

u\ :sub:`z` = measured wind speed at z\ :sub:`w` m above ground surface (m s\ :sup:`-1`)

z\ :sub:`w` = height of wind measurement about ground surface (m)

^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Other Potential ET Estimates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The RefET module code can also calculate potential evapotranspiration using several different approaches. This provides a comparison with reference ET.


""""""
Penman
""""""

`(Penman, 1948) <https://doi.org/10.1098/rspa.1948.0037>`_.


"""""""""""""""""
Hargreaves-Samani
"""""""""""""""""

`(Hargreaves and Samani, 1985) <https://doi.org/10.13031/2013.26773>`_.

""""""""""""""""
Priestley-Taylor
""""""""""""""""

`(Priestley and Taylor, 1972) <https://doi.org/10.1175/1520-0493(1972)100//<0081:OTAOSH//>2.3.CO;2>`_ .



""""""""""""""
Blaney-Criddle
""""""""""""""
[THIS CURRENTLY ISN'T SUPPORTED]

`(Blaney and Criddle, 1950) <https://archive.org/details/determiningwater96blan>`_.

------
CropET
------
The CropET module of the ET Demands model is the FAO-56 dual crop coefficient model
`(Allen et al., 1998) <http://www.fao.org/docrep/X0490E/X0490E00.htm>`_ .

.. math::

   ET_{c} = (K_c K_{cb} + K_e)ET_o

ET\ :sub:`c` = crop evapotranspiration

K\ :sub:`c` = crop coefficient

K\ :sub:`cb` = Basal crop coefficient

K\ :sub:`e` = coefficient representing bare soil evaporation

ET\ :sub:`o` = reference crop evapotranspiration from a grass reference surface
