# Forecast Model Evaluation & Skill Metrics

## 1. Verification Metrics
Forecast verification evaluates point prediction error across chronological holdout origins:
- **Mean Absolute Error (MAE)**:
  $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |y_i - \hat{y}_i|$$
- **Root Mean Squared Error (RMSE)**:
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (y_i - \hat{y}_i)^2}$$
- **Mean Bias Error (MBE)**:
  $$\text{MBE} = \frac{1}{N} \sum_{i=1}^N (\hat{y}_i - y_i)$$
- **Median Absolute Error (MedAE)**:
  $$\text{MedAE} = \text{median}(|y_i - \hat{y}_i|)$$

---

## 2. Baseline-Relative Skill Scores
Forecast skill evaluates improvement over reference baselines:
$$\text{Skill} = 1 - \frac{\text{MAE}_{\text{model}}}{\text{MAE}_{\text{baseline}}}$$
- $\text{Skill} > 0$: Forecaster outperforms the reference baseline.
- $\text{Skill} = 0$: Performance equal to baseline.
- $\text{Skill} < 0$: Forecaster performs worse than baseline.

Baselines evaluated:
1. `PersistenceBaseline`: $\hat{y}_{T+h} = y_T$.
2. `SeasonalClimatologyBaseline`: Historical day-of-year mean.

---

## 3. Chronological Backtesting Protocol
- Expanding window: training set expands chronologically origin by origin.
- Zero future observation leakage: origin $T$ has access strictly to $t \le T$.
- Backtesting evaluates horizons $h=1$, $h=3$, and $h=7$ days independently.
