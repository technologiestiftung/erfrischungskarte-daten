![](https://img.shields.io/badge/Build%20with%20%E2%9D%A4%EF%B8%8F-at%20Technologiesitftung%20Berlin-blue)

# Erfrischungskarte Daten

This repository contains the original data for the [Erfrischungskarte](https://github.com/technologiestiftung/erfrischungskarte-frontend), as well as the code used to estimate hourly values for cold wind volume and temperature.

- The Wind_Temperature folder contains the raw (values for specific hours) and clean data (quantiles for all hours from 9:00 to 21:00), in a Geojson format, for wind and temperature. The folder also encompasses a R code (Kaltluftvolum_Lufttemperatur.R) used to compute the estimates and quantiles for all hours.

- The POI's folder contains the raw point data (pools, green areas, picnic tables, etc.) as well as a Geojson file containing all data points (erfrischungskarte_poi.geojson).

## Original data sources

The information on temperature and cold air is based on processed [climate model data](https://www.berlin.de/umweltatlas/klima/klimaanalyse/2014/karten/)  from the Berlin Senatsverwaltung für Stadtentwicklung und Wohnen. For both topics, data is available for different times of the day. These data were interpolated to obtain data for each hour of the day. The shadows were calculated from a [digital terrain model](https://fbinter.stadt-berlin.de/fb/index.jsp?loginkey=zoomStart&mapId=k_dom@senstadt&bbox=387046,5818588,391547,5821400). The map is supplemented by points of interests, i.e. places that could be interesting in connection with the data. These come from various sources: The coordinates of the [green spaces](https://daten.berlin.de/datensaetze/grünanlagenbestand-berlin-einschl-der-öffentlichen-spielplätze-grünanlagen-wfs) were created from a data set on the public green space inventory. This is maintained by the district street and green space offices and made available on the Berlin geodata portal. The locations of the [fountains](https://daten.berlin.de/datensaetze/atkis-sonstiges-bauwerk-oder-sonstige-einrichtung-punkte-wfs) can also be found in the geodata portal and are part of the extensive ATKIS dataset, which is regularly updated by the district surveying offices. The locations of [bathing places](https://daten.berlin.de/datensaetze/liste-der-badestellen) come from the State Office for Health and Social Affairs (LaGeSo). The information on outdoor [swimming pools and indoor swimming pools](https://www.berlin.de/special/sport-und-fitness/schwimmen/schwimmbad/a-z/) is currently only available as a list via Berlin.de. They were transferred into a geodata set by means of webscraping. [Benches, picnic tables and drinking fountains](https://overpass-turbo.eu) were exported from Open Street Map, a freely accessible collection of geodata.

## Contributors

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/Lisa-Stubert"><img src="https://avatars.githubusercontent.com/u/61182572?v=4?s=64" width="64px;" alt=""/><br /><sub><b>Lisa-Stubert</b></sub></a><br /><a href="#data-Lisa-Stubert" title="Data">🔣</a></td>
    <td align="center"><a href="https://github.com/evelynebrie"><img src="https://avatars.githubusercontent.com/u/32559774?v=4?s=64" width="64px;" alt=""/><br /><sub><b>evelynebrie</b></sub></a><br /><a href="#data-evelynebrie" title="Data">🔣</a></td>
    <td align="center"><a href="https://vogelino.com/"><img src="https://avatars.githubusercontent.com/u/2759340?v=4?s=64" width="64px;" alt=""/><br /><sub><b>Lucas Vogel</b></sub></a><br /><a href="https://github.com/technologiestiftung/erfrischungskarte-daten/commits?author=vogelino" title="Documentation">📖</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!


## Data Licencing

Please respect the licenses of inidividual datasets. See section original data sources above for more details. 

## Credits

<table>
  <tr>
    <td>
      Made by <a src="https://odis-berlin.de/">
        <br />
        <br />
        <img width="200" src="https://raw.githubusercontent.com/technologiestiftung/erfrischungskarte-frontend/main/docs/odis-logo.svg" />
      </a>
    </td>
    <td>
      Toghether with <a src="https://citylab-berlin.org/de/start/">
        <br />
        <br />
        <img width="200" src="https://citylab-berlin.org/wp-content/uploads/2021/05/citylab-logo.svg" />
      </a>
    </td>
    <td>
      A project by <a src="https://www.technologiestiftung-berlin.de/">
        <br />
        <br />
        <img width="150" src="https://citylab-berlin.org/wp-content/uploads/2021/05/tsb.svg" />
      </a>
    </td>
    <td>
      Supported by <a src="https://www.berlin.de/">
        <br />
        <br />
        <img width="150" src="https://berlinopensource.de/assets/images/senweb-logo.svg" />
      </a>
    </td>
  </tr>
</table>

