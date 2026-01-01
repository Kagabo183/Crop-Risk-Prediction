"""
Model training script for crop risk prediction using XGBoost and a simple Neural Network (MLP).
This script demonstrates data prep, training, evaluation, and model saving for both models.
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
import joblib

# XGBoost
from xgboost import XGBClassifier
# Neural Net (MLP)
from sklearn.neural_network import MLPClassifier

# Mock feature data (replace with real data for production)
data = {
    'ndvi_trend': np.random.normal(0, 0.1, 100),
    'ndvi_anomaly': np.random.normal(0, 0.2, 100),
    'rainfall_deficit': np.random.normal(-10, 5, 100),
    'heat_stress_days': np.random.randint(0, 10, 100),
    'crop_stress': np.random.randint(0, 2, 100)  # Binary label: 0=no stress, 1=stress
}
df = pd.DataFrame(data)

X = df[['ndvi_trend', 'ndvi_anomaly', 'rainfall_deficit', 'heat_stress_days']]
y = df['crop_stress']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# XGBoost Model
xgb_model = XGBClassifier(n_estimators=100, random_state=42, use_label_encoder=False, eval_metric='logloss')
xgb_model.fit(X_train, y_train)
y_pred_xgb = xgb_model.predict(X_test)
y_prob_xgb = xgb_model.predict_proba(X_test)[:, 1]
acc_xgb = accuracy_score(y_test, y_pred_xgb)
roc_xgb = roc_auc_score(y_test, y_prob_xgb)
print(f"XGBoost - Accuracy: {acc_xgb:.3f}, ROC-AUC: {roc_xgb:.3f}")
joblib.dump(xgb_model, 'crop_stress_xgb_model.pkl')
print("XGBoost model saved as crop_stress_xgb_model.pkl")

# Neural Net Model (MLP)
mlp_model = MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=500, random_state=42)
mlp_model.fit(X_train, y_train)
y_pred_mlp = mlp_model.predict(X_test)
y_prob_mlp = mlp_model.predict_proba(X_test)[:, 1]
acc_mlp = accuracy_score(y_test, y_pred_mlp)
roc_mlp = roc_auc_score(y_test, y_prob_mlp)
print(f"MLP Neural Net - Accuracy: {acc_mlp:.3f}, ROC-AUC: {roc_mlp:.3f}")
joblib.dump(mlp_model, 'crop_stress_mlp_model.pkl')
print("MLP model saved as crop_stress_mlp_model.pkl")
