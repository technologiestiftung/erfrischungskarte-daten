#### Loading packages ####

library(geojsonsf)
library(sf)
library(ggplot2)
library(viridis)
library(ggrastr)
library(lsr)
library(rgdal)
library(geojsonR)

#### Loading dataset ####

geo_sf <- geojsonsf::geojson_sf("~/geographicalData.geojson")

#### Kaltluftvolum ####

# Measuring the slope during the day

geo_sf$VOL0422HMEA_slope_day <- NA
geo_sf$VOL0422HMEA_slope_day <- (geo_sf$VOL22HMEA - geo_sf$VOL04HMEA)/18

# Estimating values for each hour 

for (i in 9:21){

eval(parse(text=paste0("geo_sf$e_VOL",i,"HMEA <- geo_sf$VOL22HMEA-(",22-i,"*geo_sf$VOL0422HMEA_slope_day)")))
  
}

# Measuring quantile cuts

geo_sf_noGeo <- geo_sf[,18:30] 

geo_sf_noGeo$geometry <- NULL

geo_sf_noGeo[geo_sf_noGeo == 0] <- NA 

geo_sf_noGeo <- na.omit(geo_sf_noGeo)

vector <- tidyr::gather(geo_sf_noGeo)

table(quantileCut(vector$value, n=5))

# Assigning quantiles for each hour 

for (i in 9:21){
  
eval(parse(text=paste0("geo_sf$e_VOL",i,"HMEA_qt <- as.numeric(cut(geo_sf$e_VOL",i,"HMEA, breaks=c(4.59,25.2,35.5,49.5,73.7,338)))")))
  
}

#### Lutftemperatur ####

# Measuring slopes during the day

geo_sf$T2M0414HMEA_slope_day1 <- NA
geo_sf$T2M0414HMEA_slope_day1 <- (geo_sf$T2M14HMEA - geo_sf$T2M04HMEA)/10

geo_sf$T2M1422HMEA_slope_day2 <- NA
geo_sf$T2M1422HMEA_slope_day2 <- (geo_sf$T2M22HMEA - geo_sf$T2M14HMEA)/8

# Estimating values for each hour 

for (i in 9:14){
  
  eval(parse(text=paste0("geo_sf$e_T2M",i,"HMEA <- geo_sf$T2M14HMEA-(",14-i,"*geo_sf$T2M0414HMEA_slope_day1)")))
  
}

for (i in 15:21){
  
  eval(parse(text=paste0("geo_sf$e_T2M",i,"HMEA <- geo_sf$T2M22HMEA-(",22-i,"*geo_sf$T2M1422HMEA_slope_day2)")))
  
}

# Measuring quantile cuts

geo_sf_noGeo <- geo_sf[,46:58]

geo_sf_noGeo$geometry <- NULL

geo_sf_noGeo[geo_sf_noGeo == 0] <- NA

geo_sf_noGeo <- na.omit(geo_sf_noGeo)

vector <- tidyr::gather(geo_sf_noGeo)

table(quantileCut(vector$value, n=5))

# Assigning quantiles for each hour 

for (i in 9:21){
  
  eval(parse(text=paste0("geo_sf$e_T2M",i,"HMEA_qt <- as.numeric(cut(geo_sf$e_T2M",i,"HMEA, breaks=c(20.4,24.1,25.6,27,28.6,32.7)))")))
  
}

#### Exporting .geojson files ####

geo_sf_wind <- geo_sf[,31:43]

colnames(geo_sf_wind) <- c("9Uhr","10Uhr","11Uhr","12Uhr","13Uhr","14Uhr","15Uhr","16Uhr","17Uhr","18Uhr","19Uhr","20Uhr","21Uhr","geometry")

st_write(geo_sf_wind, "~/t_Wind_9bis21.geojson")

geo_sf_temperatur <- geo_sf[,59:71]

colnames(geo_sf_temperatur) <- c("9Uhr","10Uhr","11Uhr","12Uhr","13Uhr","14Uhr","15Uhr","16Uhr","17Uhr","18Uhr","19Uhr","20Uhr","21Uhr","geometry")

st_write(geo_sf_temperatur, "~/t_Temperatur_9bis21.geojson")
