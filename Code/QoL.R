# Loading packages

library(geojsonsf)
library(sf)
library(ggplot2)
library(viridis)
library(ggrastr)
library(lsr)
library(rgdal)
library(geojsonR)

#### Kaltluftvolum ####

geo_sf_kaltluft <- geojsonsf::geojson_sf("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Geojson/Raw/Kaltluftvolumen_4AM.geojson")

# Measuring slopes

geo_sf_kaltluft$VOL0422HMEA_slope_day <- NA
geo_sf_kaltluft$VOL0422HMEA_slope_day <- (geo_sf_kaltluft$VOL22HMEA - geo_sf_kaltluft$VOL04HMEA)/18

geo_sf_kaltluft$VOL0422HMEA_slope_night <- NA
geo_sf_kaltluft$VOL0422HMEA_slope_night <- (geo_sf_kaltluft$VOL04HMEA - geo_sf_kaltluft$VOL22HMEA)/6

# Estimating values for each hour (including sanity check)

geo_sf_kaltluft$VOL04HMEA_test <- geo_sf_kaltluft$VOL22HMEA-(18*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL05HMEA <- geo_sf_kaltluft$VOL22HMEA-(17*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL06HMEA <- geo_sf_kaltluft$VOL22HMEA-(16*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL07HMEA <- geo_sf_kaltluft$VOL22HMEA-(15*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL08HMEA <- geo_sf_kaltluft$VOL22HMEA-(14*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL09HMEA <- geo_sf_kaltluft$VOL22HMEA-(13*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL10HMEA <- geo_sf_kaltluft$VOL22HMEA-(12*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL11HMEA <- geo_sf_kaltluft$VOL22HMEA-(11*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL12HMEA <- geo_sf_kaltluft$VOL22HMEA-(10*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL13HMEA <- geo_sf_kaltluft$VOL22HMEA-(9*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL14HMEA <- geo_sf_kaltluft$VOL22HMEA-(8*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL15HMEA <- geo_sf_kaltluft$VOL22HMEA-(7*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL16HMEA <- geo_sf_kaltluft$VOL22HMEA-(6*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL17HMEA <- geo_sf_kaltluft$VOL22HMEA-(5*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL18HMEA <- geo_sf_kaltluft$VOL22HMEA-(4*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL19HMEA <- geo_sf_kaltluft$VOL22HMEA-(3*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL20HMEA <- geo_sf_kaltluft$VOL22HMEA-(2*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL21HMEA <- geo_sf_kaltluft$VOL22HMEA-(1*geo_sf_kaltluft$VOL0422HMEA_slope_day)
geo_sf_kaltluft$VOL22HMEA_test <- geo_sf_kaltluft$VOL04HMEA-(6*geo_sf_kaltluft$VOL0422HMEA_slope_night)
geo_sf_kaltluft$VOL23HMEA <- geo_sf_kaltluft$VOL04HMEA-(5*geo_sf_kaltluft$VOL0422HMEA_slope_night)
geo_sf_kaltluft$VOL24HMEA <- geo_sf_kaltluft$VOL04HMEA-(4*geo_sf_kaltluft$VOL0422HMEA_slope_night)
geo_sf_kaltluft$VOL01HMEA <- geo_sf_kaltluft$VOL04HMEA-(3*geo_sf_kaltluft$VOL0422HMEA_slope_night)
geo_sf_kaltluft$VOL02HMEA <- geo_sf_kaltluft$VOL04HMEA-(2*geo_sf_kaltluft$VOL0422HMEA_slope_night)
geo_sf_kaltluft$VOL03HMEA <- geo_sf_kaltluft$VOL04HMEA-(1*geo_sf_kaltluft$VOL0422HMEA_slope_night)

# Measuring quantiles for each hour

geo_sf_kaltluft_noGeo <- geo_sf_kaltluft
geo_sf_kaltluft_noGeo$geometry <- NULL

vector <- tidyr::gather(geo_sf_kaltluft_noGeo)

table(quantileCut(vector$value, n=5)) # Gives us values for quantiles

geo_sf_kaltluft$VOL04HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL04HMEA_test, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))

geo_sf_kaltluft$VOL05HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL05HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL06HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL06HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL07HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL07HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL08HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL08HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL09HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL09HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL10HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL10HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL11HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL11HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL12HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL12HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL13HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL13HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL14HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL14HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL15HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL15HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL16HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL16HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL17HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL17HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL18HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL18HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL19HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL19HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL20HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL20HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL21HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL21HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL22HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL22HMEA_test, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL23HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL23HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL24HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL24HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL01HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL01HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL02HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL02HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))
geo_sf_kaltluft$VOL03HMEA_qt <- as.numeric(cut(geo_sf_kaltluft$VOL03HMEA, breaks=c(-0.3,25.3,37.3,52.7,79.6,359)))

# Keeping only columns of interest

geo_sf_kaltluft <- geo_sf_kaltluft[,16:66]

# Exporting .geojson


crs(geo_sf_kaltluft)

st_write(geo_sf_kaltluft, "/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Geojson/Clean/Kaltluftvolum.geojson")
idx <-  st_cast(geo_sf_kaltluft, "MULTIPOLYGON")
st_write(idx, "/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Geojson/Clean/Kaltluftvolum_Multiploygon.geojson")

# Writing .tiffs

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum4am.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL04HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum5am.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL05HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum6am.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL06HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum7am.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL07HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum8am.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL08HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum9am.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL09HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum10am.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL10HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum11am.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL11HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum12pm.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL12HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum1pm.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL13HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum2pm.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL14HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum3pm.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL15HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum4pm.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL16HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum5pm.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL17HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum6pm.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL18HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum7pm.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL19HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum8pm.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL20HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum9pm.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL21HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum10pm.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL22HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum11pm.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL23HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum12am.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL24HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum1am.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL01HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum2am.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL02HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Kaltluftvolum/Kaltluftvolum3am.tiff")

ggplot(geo_sf_kaltluft, aes(fill=VOL03HMEA_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()

#### Lufttemperatur ####

geo_sf_lufttemp_14h <- geojsonsf::geojson_sf("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Geojson/Raw/Lufttemperatur2pm.geojson")
colnames(geo_sf_lufttemp_14h)[2] <- "Lufttemp_14"

geo_sf_lufttemp_04h <- geojsonsf::geojson_sf("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Geojson/Raw/Lufttemperatur4am.geojson")
colnames(geo_sf_lufttemp_04h)[2] <- "Lufttemp_04"


# Measuring quantiles 

table(quantileCut(geo_sf_lufttemp_14h$Lufttemp_14, n=2)) # Gives us values for quantiles

geo_sf_lufttemp_14h$Lufttemp_14_qt <- as.numeric(cut(geo_sf_lufttemp_14h$Lufttemp_14, breaks=c(20,30,33)))

table(quantileCut(geo_sf_lufttemp_04h$Lufttemp_04, n=2)) # Gives us values for quantiles

geo_sf_lufttemp_04h$Lufttemp_04_qt <- as.numeric(cut(geo_sf_lufttemp_04h$Lufttemp_04, breaks=c(13,17,23)))

# Exporting .geojson

st_write(geo_sf_lufttemp_14h, "/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Geojson/Clean/Lufttemperatur_14h.geojson")
idx <-  st_cast(geo_sf_lufttemp_14h, "MULTIPOLYGON")
st_write(idx, "/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Geojson/Clean/Lufttemperatur_14h_Multiploygon.geojson")

st_write(geo_sf_lufttemp_04h, "/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Geojson/Clean/Lufttemperatur_04h.geojson")
idx <-  st_cast(geo_sf_lufttemp_04h, "MULTIPOLYGON")
st_write(idx, "/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Geojson/Clean/Lufttemperatur_04h_Multiploygon.geojson")

# Writing .tiffs

tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Lufttemperatur/Lufttemperatur2pm.tiff")

ggplot(geo_sf_lufttemp_14h, aes(fill=Lufttemp_14_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()


tiff("/Users/evelynebrie/Dropbox/CityLab/Projects/QoL/Code/Rasters/Lufttemperatur/Lufttemperatur4am.tiff")

ggplot(geo_sf_lufttemp_04h, aes(fill=Lufttemp_04_qt)) +
  #rasterise(geom_sf(lwd = 0)) + 
  geom_sf(lwd = 0) + 
  scale_fill_viridis() +
  theme_minimal() + 
  guides( fill = FALSE) 

dev.off()


