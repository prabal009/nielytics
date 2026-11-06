# Operational Temperature Forecasting Architecture

## 1. Design & Purpose
The `TemperatureForecaster` delivers operational short-term daily temperature forecasts (lead times $h \in \{1, \dots, 14\}$ days).

---

## 2. Feature Matrix & Zero Leakage Guarantee
At forecast origin $T$, only observations $\le T$ are accessible:
1. **Lags**: $y_T, y_{T-1}, y_{T-2}, y_{T-6}, y_{T-13}$.
2. **Rolling Statistics**:
   - 7-day past mean, standard deviation, min, max over $[T-6, T]$.
   - 14-day past mean over $[T-13, T]$.
3. **Harmonic Encodings**:
   - $\sin(2\pi \cdot \text{doy} / 365.25)$, $\cos(2\pi \cdot \text{doy} / 365.25)$ for target date $T+h$.
   - Monthly cyclical encodings $\sin(2\pi \cdot \text{month} / 12)$, $\cos(2\pi \cdot \text{month} / 12)$.
4. **Historical Day-of-Year Baseline**:
   - Climatological expected value computed exclusively over training years.

---

## 3. Direct Horizon Multi-Step Strategy
Rather than recursively compounding single-step errors, `TemperatureForecaster` uses direct multi-step forecasting:
- A dedicated Closed-Form Ridge Regressor is trained independently for each horizon $h \in \{1, 3, 7, 14\}$.
- Minimizes loss directly at the target lead time.

---

## 4. Uncertainty Intervals
- Calibrated using empirical validation residuals per horizon $h$.
- Outputs symmetric and quantile-based 80% and 95% prediction intervals.
- Models horizon-dependent error growth ($\sigma_h \propto \sqrt{h}$).
