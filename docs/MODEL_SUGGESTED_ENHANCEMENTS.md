# La Liga Linea — Model Suggested Enhancements

## Priority 1: Ensemble Improvements

### XGBoost Hyperparameter Tuning
- Run `Optuna` Bayesian optimisation on XGBoost, RandomForest, GradientBoosting separately.
- Current ensemble weights (XGB=2, RF=1.5, GB=1, LR=0.5) were set manually; tune via stacked cross-validation instead.

### Neural Network Baseline
- Add a simple `MLPClassifier(hidden_layer_sizes=(64,32), activation='relu')` as a fifth voter.
- May capture non-linear feature interactions the tree models miss.

### Calibration
- Apply `CalibratedClassifierCV` with isotonic regression over the full ensemble.
- Draw calibration curves per outcome class (H, D, A) to identify systematic bias.

## Priority 2: Feature Expansion

### xG Features
- FBref xG is already scraped (`fetch_fbref_xg.py`). Ensure `xg_l5_home` and `xga_l5_away` are in `FEATURE_COLS`.
- Add `xg_differential_l10` (attack quality − defence quality as a single signal).

### Copa del Rey Depth
- Current Copa flag is binary (played within 4 days). Extend to encode extra-time matches as higher fatigue cost.

### Player Availability Proxy
- La Liga publishes official squad lists. If a top-3 ranked squad member is absent, apply a calibrated downgrade to their team's attack and defence features.

### Referee Aggression Score
- Spanish referee data is sparse in English, but carding rates differ. Scrape `sofascore` or `fbref` referee pages for La Liga referees and add `ref_yellow_avg` as a feature.

## Priority 3: Betting Intelligence

### Draw Specialist Filter
- La Liga has a higher draw rate (~26%) than EPL. Add a dedicated draw probability boost for teams that historically share draw-prone head-to-head records.

### Closing Line Value Tracking
- Record the model probability at prediction time vs. closing B365 odds. Track CLV weekly.

## Priority 4: Infrastructure

- Delete `models/ensemble_model.pkl` in GitHub Actions after a full season to force retraining on new data.
- Add an automatic model version tag so the app shows which season's data the model was trained on.
