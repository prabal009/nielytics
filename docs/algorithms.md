# Implemented core methodology

## Missing observations and cleaning

Pandas missing markers (`NaN`, `NaT`, `None`, nullable `NA`) are counted with `isna`. Missing percentage is `100 * missing_count / row_count`; zero-row inputs return zero percentages. Statistical imputation ignores missing measurements and fails if no observations support the requested estimate. Mode ties use pandas ordering. Constant filling is explicit. No missing climate record is automatically interpreted as zero rainfall, zero exposure, or absence of an event.

Duplicate removal uses selected-column equality, retaining the first or last occurrence or removing all repeated groups as explicitly requested. Surviving indices remain unchanged. Cleaning histories record transformations, not a claim that the data are scientifically validated.

## Descriptive statistics

Mean is the arithmetic mean of observed values. Sample variance divides squared deviations by `N - ddof` (default `ddof=1`); population variance uses `ddof=0`. Standard deviation is its square root. Insufficient samples produce missing results. Quantiles use linear interpolation; skewness and Fisher/excess kurtosis use pandas estimators. Floating-point precision follows NumPy/pandas, and nonfinite values are not silently replaced before analysis.

Covariance uses the observations present in each pair and applies `N - ddof` separately to that pair, including when missing values are present. Correlations support Pearson, Spearman, and Kendall methods; constants and insufficient pairs have undefined correlations. Correlation does not establish causation. Grouped summaries retain missing group keys and omit unobserved categorical groups.

## Serialization

Profiles convert undefined/nonfinite statistics to null and date coverage to ISO strings. Table records use pandas JSON serialization, omit the index, encode timestamps at millisecond precision, and convert nonfinite/missing values to null. These nulls must not be treated as zero by consuming applications.

## Time series and outlier screening

Rolling means sort unique dates and count observed rows within each window; irregular calendar gaps are **not** interpolated. Missing dates are computed against a daily calendar. Monthly anomalies subtract the mean of an explicitly selected baseline for the corresponding calendar month; months absent in the baseline remain null. A sufficiently representative climatology is the caller's responsibility.

IQR outliers fall outside Q1 − 1.5×IQR or Q3 + 1.5×IQR; population z-score uses the sample's mean and `ddof=0` standard deviation with absolute score >3; modified z-score uses `0.6745 × |value − median| / MAD` with cutoff 3.5; percentile flags values outside the 1st/99th quantiles. Constant-score samples have no z/MAD flags, and missing observations are not flagged. The mask does not drop observations or prove measurements are erroneous.

## Hazard interpretation and pending methods

Heat and rainfall spells require consecutive recorded calendar days; missing measurements break spells. Temperature and rainfall period-mean differences are unadjusted, not seasonally corrected unless explicitly specified. Cyclone track distance uses a spherical-Earth great-circle (haversine) approximation, not a landfall test. Landslide rainfall/slope screening uses caller-supplied cutoffs rather than fitted probabilities. SPI, multi-hazard normalization, validated predictive models, long-term trend estimation, and automatic reporting remain pending. SPI needs documented distribution fitting, zero-precipitation treatment, accumulation windows, seasonal baseline sufficiency, and trusted reference validation; a generic Z-score is not a substitute.
