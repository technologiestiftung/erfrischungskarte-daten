# Erfrischungskarte Daten

This repository containts the original data for the Erfrischungskarte, as well as the code used to estimate hourly values for cold wind volume and temperature.

- The Wind_Temperature folder contains the raw (values for specific hours) and clean data (quantiles for all hours from 9:00 to 21:00), in a Geojson format, for wind and temperature. The folder also encompasses a R code (Kaltluftvolum_Lufttemperatur.R) used to compute the estimates and quantiles for all hours.

- The POI's folder contains the raw point data (pools, green areas, picnic tables, etc.) as well as a Geojson file containing all data points (erfrischungskarte_poi.geojson).