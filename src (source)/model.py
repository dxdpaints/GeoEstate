import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import joblib

def train_model(df, target="price"):
    features = ["road_density", "dist_metro", "greenery_index"]
    X = df[features]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print("R2 Score:", r2_score(y_test, preds))
    print("MAE:", mean_absolute_error(y_test, preds))

    joblib.dump(model, "model.pkl")
    return model
