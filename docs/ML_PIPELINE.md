# ML Pipeline Documentation

## Overview

The FraudWatch ML pipeline orchestrates feature engineering, model training, prediction, and monitoring.

## Prediction Pipeline

### Flow
```
Transaction → Feature Extractor → ML Model → Rule Engine → Score Combiner → Prediction → Alert
```

### Components

1. **Feature Engineering**
   - Transaction features (amount, currency, type, channel)
   - Customer features (behavior, history, risk profile)
   - Merchant features (risk tier, history, patterns)
   - Device features (fingerprint, reputation, history)
   - Velocity features (frequency, patterns)

2. **ML Model Inference**
   - Loads production model from registry
   - Returns probability score (0-1)
   - Tracks inference latency

3. **Rule Engine**
   - Rule-based scoring
   - Real-time rule evaluation
   - Configurable severity thresholds

4. **Score Combination**
   - Weighted average (ML: 60%, Rules: 40%)
   - Rule score acts as floor
   - Final score determines classification

## Model Registry

### Model Types
- Fraud detection models
- Anomaly detection models
- Classification models

### Deployment Environments
- `PRODUCTION` - Live for inference
- `STAGING` - Testing environment
- `DEVELOPMENT` - Development/testing

## Training Pipeline

### Dataset Builder
- Features extracted from transaction history
- Labels from historical predictions and cases
- Train/validation/test splits

### Model Training
- Scikit-learn based models
- Hyperparameter tuning
- Cross-validation
- Metrics tracking (accuracy, precision, recall, F1, ROC-AUC, PR-AUC)

## Model Monitoring

### Metrics Tracked
- Prediction volume
- Average latency
- Confidence distribution
- Failure rate
- Drift indicators

### Drift Detection
- Feature drift (PSI, population stability)
- Prediction drift (distribution changes)
- Confidence shift monitoring

## Explainability

### Methods Supported
- SHAP values (when available)
- Feature importance
- Rule explanations
- Counterfactual explanations

### Explanation Format
```json
{
  "prediction": { "id": "...", "label": "fraud", "confidence": 0.87 },
  "explanation": {
    "summary": "Human-readable explanation",
    "top_features": ["feature1", "feature2"],
    "methods_used": ["shap", "feature_importance"]
  }
}
