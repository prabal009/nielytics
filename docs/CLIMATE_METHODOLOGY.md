# Climate Hazard Analytical Methodology

## 1. Official IMD Criteria

### 1.1 Heatwave Classification
India Meteorological Department criteria define heatwave conditions based on departure from normal maximum temperature as well as absolute thresholds:
- **Plains**:
  - Baseline requirement: Maximum temperature must reach at least 40°C.
  - Departure Criteria:
    - Heatwave: Departure from normal is +4.5°C to +6.4°C.
    - Severe Heatwave: Departure from normal is >= +6.5°C.
  - Absolute Criteria (irrespective of normal):
    - Heatwave: Actual maximum temperature >= 45.0°C.
    - Severe Heatwave: Actual maximum temperature >= 47.0°C.
- **Hilly Regions**:
  - Base qualification: Maximum temperature >= 30.0°C.
  - Departure >= +4.5°C (Severe >= +6.5°C).
- **Coastal Regions**:
  - Base qualification: Maximum temperature >= 37.0°C.
  - Departure >= +4.5°C (Severe >= +6.5°C).

### 1.2 Rainfall Intensity Categories
Official IMD rainfall 24-hour accumulation categories:
- Very Light: 0.1 – 2.4 mm
- Light: 2.5 – 15.5 mm
- Moderate: 15.6 – 64.4 mm
- Heavy: 64.5 – 115.5 mm
- Very Heavy: 115.6 – 204.4 mm
- Extremely Heavy: >= 204.5 mm

### 1.3 Cyclone Intensity Scale
Official IMD classification based on 3-minute sustained maximum wind speed:
- Low Pressure Area: < 31 km/h
- Depression: 31 – 49 km/h
- Deep Depression: 50 – 61 km/h
- Cyclonic Storm: 62 – 88 km/h
- Severe Cyclonic Storm: 89 – 117 km/h
- Very Severe Cyclonic Storm: 118 – 167 km/h
- Extremely Severe Cyclonic Storm: 168 – 221 km/h
- Super Cyclonic Storm: >= 222 km/h

---

## 2. Standardized Precipitation Index (SPI)
The Standardized Precipitation Index (McKee et al., 1993; WMO 2012) quantifies precipitation deficit across rolling accumulation scales ($k \in \{1, 3, 6, 12\}$ months):
1. Rolling precipitation totals: $x_t = \sum_{i=0}^{k-1} P_{t-i}$.
2. Fit two-parameter Gamma probability density function to non-zero positive rainfall:
   $$g(x) = \frac{1}{\beta^\alpha \Gamma(\alpha)} x^{\alpha - 1} e^{-x / \beta}, \quad x > 0$$
   Maximum likelihood parameters:
   $$\alpha = \frac{1}{4A} \left(1 + \sqrt{1 + \frac{4A}{3}}\right), \quad A = \ln(\bar{x}) - \frac{\sum \ln(x)}{n}, \quad \beta = \frac{\bar{x}}{\alpha}$$
3. Incorporate zero-precipitation probability $q = m / n$:
   $$H(x) = q + (1 - q) G(x)$$
4. Transform cumulative probability $H(x)$ to standard normal variate $Z$:
   $$\text{SPI} = \Phi^{-1}(H(x))$$
5. Classification:
   - Extremely Wet: $\ge +2.0$
   - Very Wet: $+1.5$ to $+1.99$
   - Moderately Wet: $+1.0$ to $+1.49$
   - Near Normal: $-0.99$ to $+0.99$
   - Moderately Dry: $-1.0$ to $-1.49$
   - Severely Dry: $-1.5$ to $-1.99$
   - Extremely Dry: $\le -2.0$

---

## 3. Compound Hazard Triggers
- **Landslides**: Landslide risk escalates sharply when multi-day antecedent precipitation saturates slope material, followed by acute daily trigger rainfall exceedance.
- **Heat & Drought**: Simultaneous occurrence of high temperature anomalies and severe precipitation deficits accelerates evapotranspiration, desiccation, and soil degradation.
