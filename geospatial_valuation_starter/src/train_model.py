"""
Train a baseline price model with engineered features.
USAGE:
  python src/train_model.py --in_csv data/processed/enriched.csv --target_col price_lakh
"""

import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from xgboost import XGBRegressor
import matplotlib.pyplot as plt
import joblib

def main(in_csv: str, target_col: str):
    df = pd.read_csv(in_csv)

    # Minimal cleaning / feature engineering
    # Convert BHK from text if needed
    if "bhk" in df.columns:
        df["bhk"] = pd.to_numeric(df["bhk"], errors="coerce")
    elif "bhk_text" in df.columns:
        df["bhk"] = df["bhk_text"].str.extract(r'(\d+)').astype(float)

    # Area
    if "area_sqft" not in df.columns and "area_text" in df.columns:
        df["area_sqft"] = df["area_text"].str.replace(",","", regex=False).str.extract(r'(\d+\.?\d*)').astype(float)

    # Price
    y = pd.to_numeric(df[target_col], errors="coerce")

    # Select numeric features
    candidates = [
        "bhk","area_sqft","lat","lon",
        "dist_school_m","dist_hospital_m","dist_metro_m"
    ]
    X = df[candidates].copy()
    for c in candidates:
        if c not in X.columns:
            X[c] = np.nan
    # Drop rows with missing target or too many NaNs
    ok = (~y.isna()) & (X.notna().sum(axis=1) >= 4)
    X, y = X[ok], y[ok]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBRegressor(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        n_jobs=4
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    rmse = mean_squared_error(y_test, pred, squared=False)
    r2 = r2_score(y_test, pred)
    print(f"RMSE: {rmse:.2f} | R2: {r2:.3f} | N={len(y_test)}")

    # Feature importances
    importances = model.feature_importances_
    fig = plt.figure(figsize=(6,4))
    order = np.argsort(importances)[::-1]
    plt.bar(range(len(importances)), importances[order])
    plt.xticks(range(len(importances)), [X.columns[i] for i in order], rotation=45, ha="right")
    plt.title("Feature Importance")
    plt.tight_layout()
    Path("models").mkdir(exist_ok=True, parents=True)
    fig_path = "models/feature_importance.png"
    plt.savefig(fig_path, dpi=160)
    print("Saved feature importance ->", fig_path)

    # Save model
    joblib.dump(model, "models/model.pkl")
    print("Saved model -> models/model.pkl")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_csv", required=True)
    ap.add_argument("--target_col", default="price_lakh")
    args = ap.parse_args()
    main(args.in_csv, args.target_col)
