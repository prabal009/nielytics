# Multi-Source Climate Data Harmonization Specification

## 1. Motivation & Standard Schema
Climate intelligence across India is sourced from diverse agencies (IMD, CWC, NRSC, ERA5, NASA), each employing disparate column naming conventions, physical units, and administrative spellings.

NIElytics normalizes incoming records into canonical `StandardClimateRecord` entries:
- `date`: ISO string `YYYY-MM-DD`
- `state`: Canonical Indian State or Union Territory name
- `district`: Canonical Indian District name
- `latitude`: WGS84 decimal degrees `[-90, 90]`
- `longitude`: WGS84 decimal degrees `[-180, 180]`
- `hazard`: One of `"heatwave"`, `"flood"`, `"drought"`, `"landslide"`, `"cyclone"`
- `metric`: Measurement identifier (`"tmax"`, `"tmin"`, `"rainfall"`, `"wind_speed"`, `"discharge"`)
- `value`: Finite numeric measurement
- `unit`: Standardized physical unit (`"C"`, `"mm"`, `"km/h"`, `"m3/s"`, `"hPa"`)
- `source`: Attribution identifier (e.g. `"IMD_DAILY_STATION"`)
- `data_quality`: `"verified"`, `"unverified"`, `"modeled"`, `"proxy"`
- `observation_type`: `"ground_station"`, `"reanalysis"`, `"nwp_forecast"`, `"event_catalog"`

---

## 2. Indian Administrative Normalization Mapping

### 2.1 States & Union Territories
Canonical spelling follows Government of India gazettes. Historical and colloquial variants are normalized automatically:
- `"Orissa"` -> `"Odisha"`
- `"Uttaranchal"` -> `"Uttarakhand"`
- `"Pondicherry"` -> `"Puducherry"`
- `"Mysore"` -> `"Karnataka"`
- `"Madras"` -> `"Tamil Nadu"`
- `"United Provinces"` -> `"Uttar Pradesh"`
- `"Bombay"` -> `"Maharashtra"`
- `"NCT of Delhi"` / `"New Delhi"` -> `"Delhi"`
- `"Jammu & Kashmir"` / `"J&K"` -> `"Jammu and Kashmir"`
- `"Andaman & Nicobar"` -> `"Andaman and Nicobar Islands"`

### 2.2 Key District Aliases
- `"Bangalore"` -> `"Bengaluru Urban"`
- `"Gurgaon"` -> `"Gurugram"`
- `"Calcutta"` -> `"Kolkata"`
- `"Allahabad"` -> `"Prayagraj"`
- `"Banaras"` / `"Benares"` -> `"Varanasi"`
- `"Faizabad"` -> `"Ayodhya"`
- `"Baroda"` -> `"Vadodara"`
- `"Cochin"` / `"Kochi"` -> `"Ernakulam"`
- `"Trivandrum"` -> `"Thiruvananthapuram"`
- `"Calicut"` -> `"Kozhikode"`
- `"Poona"` -> `"Pune"`

---

## 3. Unit Conversions Supported
- **Temperature**: Celsius (`C`), Fahrenheit (`F`), Kelvin (`K`).
- **Precipitation**: Millimeters (`mm`), Centimeters (`cm`), Meters (`m`), Inches (`inch`).
- **Wind**: Kilometers per hour (`km/h`), Meters per second (`m/s`), Knots (`knots`), Miles per hour (`mph`).
- **Pressure**: Hectopascals (`hPa`), Millibars (`mbar`), Bars (`bar`), Atmospheres (`atm`), Pascals (`Pa`).
