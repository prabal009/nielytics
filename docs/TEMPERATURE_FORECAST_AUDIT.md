# Temperature Forecasting & Climate Projection Audit

## 1. Problem Definition & Distinction
A core design requirement of NIElytics v2.0 is the clean separation of two distinct analytical regimes:
- **Short-Term Operational Weather Forecasting (1 to 14 days)**: Predicts specific day-level maximum/minimum temperatures using recent meteorological dynamics, historical autoregression, and Numerical Weather Prediction (NWP) model outputs.
- **Long-Term Climate Projections (2030 to 2050+)**: Estimates multi-decadal climatological shifts and warming anomalies under standardized greenhouse gas emission pathways (CMIP6 / IPCC Shared Socioeconomic Pathways: SSP1-2.6, SSP2-4.5, SSP5-8.5).

Mixing these regimes produces misleading claims (e.g., claiming to predict the daily weather for July 14, 2045).

---

## 2. Technical Audit of Forecasting Architecture

### 2.1 Feature Engineering & Strict Leakage Prevention
- **Invariance**: At forecast origin $T$, any calculation incorporating observations $t > T$ constitutes fatal data leakage.
- **Cyclical Encoding**: Day of year ($d \in [1, 365.25]$) encoded as harmonic trigonometric features $\sin(2\pi d / 365.25)$ and $\cos(2\pi d / 365.25)$.
- **Lagged Structures**: Strictly lagged values $y_{T}, y_{T-1}, y_{T-2}, y_{T-6}, y_{T-13}$ and rolling summary statistics computed exclusively over $[T-6, T]$ and $[T-13, T]$.
- **Climatological Reference**: Out-of-fold historical day-of-year means from training period only.

### 2.2 Model Strategies
1. **Baselines**:
   - `PersistenceBaseline`: $\hat{y}_{T+h} = y_T$
   - `SeasonalClimatologyBaseline`: $\hat{y}_{T+h} = \bar{y}_{\text{doy}(T+h)}$
   - `TrendSeasonalityBaseline`: Harmonic regression with linear slope.
2. **Autoregressive Regressors**:
   - Closed-form Ridge and Ordinary Least Squares implemented using pure NumPy/SciPy linear algebra (`numpy.linalg.lstsq` / regularized normal equations), with optional delegation to `scikit-learn` if present.
   - Recursive and direct multi-step forecasting across horizons $h \in \{1, 3, 7, 14\}$ days.

### 2.3 Chronological Backtesting & Evaluation
- Strict chronological expanding or rolling window splits.
- Verification metrics:
  - Mean Absolute Error (MAE)
  - Root Mean Squared Error (RMSE)
  - Mean Bias Error (MBE)
  - Climatology Skill Score: $\text{Skill} = 1 - \frac{\text{MAE}_{\text{model}}}{\text{MAE}_{\text{climatology}}}$.

### 2.4 Uncertainty Quantification
- Empirical residual calibration: quantiles and standard error of horizon-specific validation residuals.
- Formulates symmetric and empirical 80% and 95% prediction intervals $[\hat{y}_{\text{lower}}, \hat{y}_{\text{upper}}]$.

### 2.5 Climate Scenario Projections
- Mode A (Empirical Trend Extrapolation): Theil-Sen robust slope extrapolated to 2030, 2040, 2050 with clear disclaimers that linear trends do not capture non-linear tipping points or emission policy changes.
- Mode B (CMIP6 Regional Scenarios): Quantifies temperature anomaly ranges derived from IPCC AR6 regional projections for South Asia under SSP1-2.6 (sustainable), SSP2-4.5 (middle of the road), and SSP5-8.5 (fossil-fueled development).

### 2.6 Persistence & Security
- Zero use of Python `pickle` or `joblib` (untrusted execution vulnerability).
- Safe JSON artifact serialization containing model hyperparameters, coefficients, normalization scalers, and verification metadata.
