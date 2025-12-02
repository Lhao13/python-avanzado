"""Modelo ligero para predecir gastos con series históricas."""

# Módulo corregido para predicción de gastos con validación temporal
# Incluye:
# - TimeSeriesSplit en vez de KFold
# - Eliminación de train_test_split para evitar inconsistencias
# - Validación realista: predicción de últimos n meses
# - Agrupación de categorías raras
# - Construcción coherente de features
# - Pipeline más limpio y sin fuga temporal

from __future__ import annotations

from calendar import month_name
from datetime import datetime
from math import sqrt
from typing import Dict, List, Tuple

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
import numpy as np

from ..db.connection import DatabaseConnection

MIN_RECORDS_FOR_TRAINING = 12
RARE_CATEGORY_THRESHOLD = 5  # categorías con menos de 5 apariciones se agrupan


###############################################
# 1. Carga de transacciones desde BD
###############################################
def _fetch_transactions() -> pd.DataFrame:
    query = """
    SELECT
        t.monto,
        t.cantidad,
        t.fecha,
        c.nombre AS categoria,
        c.periodicidad,
        c.tipo
    FROM transaccion t
    JOIN categoria c ON t.Categoria_Id_Categoria = c.Id_Categoria
    WHERE t.fecha IS NOT NULL
    """
    with DatabaseConnection().get_connection() as connection:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


###############################################
# 2. Preparación mensual agregada
###############################################
def _prepare_monthly_records(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["cantidad"] = df["cantidad"].fillna(0)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["year"] = df["fecha"].dt.year
    df["month"] = df["fecha"].dt.month

    df = df[df["tipo"].str.lower() == "gasto"]
    if df.empty:
        return pd.DataFrame()

    # Agrupar categorías raras
    counts = df["categoria"].value_counts()
    rare = counts[counts < RARE_CATEGORY_THRESHOLD].index
    df["categoria"] = df["categoria"].replace(rare, "OTRAS")

    records = (
        df.groupby(["year", "month", "categoria", "periodicidad", "tipo"], dropna=False)
        .agg(
            total_monto=("monto", "sum"),
            avg_cantidad=("cantidad", "mean"),
            transactions=("monto", "count"),
        )
        .reset_index()
    )

    records["avg_cantidad"] = records["avg_cantidad"].fillna(0)
    records["transactions"] = records["transactions"].fillna(0)

    return records


###############################################
# 3. Baseline por categoría para predicciones
###############################################
def _category_baseline(records: pd.DataFrame) -> pd.DataFrame:
    baseline = (
        records.groupby(["categoria", "periodicidad", "tipo"], dropna=False)
        .agg(
            avg_cantidad=("avg_cantidad", "mean"),
            transactions=("transactions", "mean"),
        )
        .reset_index()
    )
    return baseline


###############################################
# 4. Construcción de features (One-hot + numéricos)
###############################################
def _build_features(records: pd.DataFrame, required_columns: List[str] | None = None) -> pd.DataFrame:
    base = records[["year", "month", "avg_cantidad", "transactions"]].copy()
    categorical = pd.get_dummies(records[["categoria", "periodicidad", "tipo"]].astype(str))
    features = pd.concat([base, categorical], axis=1)

    if required_columns is not None:
        # Añadir columnas faltantes con valor 0
        for col in required_columns:
            if col not in features.columns:
                features[col] = 0
        features = features[required_columns]

    return features


###############################################
# 5. Entrenamiento con VALIDACIÓN TEMPORAL REAL
###############################################
def _train_model(records: pd.DataFrame, forecast_horizon: int = 6):
    if len(records) < MIN_RECORDS_FOR_TRAINING:
        raise ValueError(
            f"Se necesitan al menos {MIN_RECORDS_FOR_TRAINING} registros para entrenar el modelo."
        )

    features = _build_features(records)
    target = records["total_monto"].astype(float)

    # Separar los últimos `forecast_horizon` meses como test de predicción realista
    train_X = features.iloc[:-forecast_horizon]
    train_y = target.iloc[:-forecast_horizon]

    test_X = features.iloc[-forecast_horizon:]
    test_y = target.iloc[-forecast_horizon:]

    # Entrenar modelo final
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(train_X, train_y)

    # Evaluación real (pasado -> futuro)
    preds = model.predict(test_X)

    metrics_real = {
        "MAE": mean_absolute_error(test_y, preds),
        "MSE": mean_squared_error(test_y, preds),
        "RMSE": sqrt(mean_squared_error(test_y, preds)),
    }

    # Cross-validation temporal
    tscv = TimeSeriesSplit(n_splits=5)
    cv_preds = np.zeros(len(target))
    for train_idx, test_idx in tscv.split(features):
        cv_model = RandomForestRegressor(n_estimators=200, random_state=42)
        cv_model.fit(features.iloc[train_idx], target.iloc[train_idx])
        cv_preds[test_idx] = cv_model.predict(features.iloc[test_idx])

    metrics_cv = {
        "CV_MAE": mean_absolute_error(target, cv_preds),
        "CV_MSE": mean_squared_error(target, cv_preds),
        "CV_RMSE": sqrt(mean_squared_error(target, cv_preds)),
    }

    importance_df = (
        pd.DataFrame({"feature": features.columns, "importance": model.feature_importances_})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )

    baseline = _category_baseline(records)

    return model, features.columns.tolist(), metrics_real, metrics_cv, baseline, importance_df


###############################################
# 6. Generar períodos futuros
###############################################
def _future_periods(months: int) -> List[Tuple[int, int]]:
    today = datetime.now()
    periods = []
    for offset in range(1, months + 1):
        total_month = today.month - 1 + offset
        year = today.year + total_month // 12
        month = (total_month % 12) + 1
        periods.append((year, month))
    return periods


###############################################
# 7. Plantilla futura basada en categorías
###############################################
def _build_future_template(baseline: pd.DataFrame, months: int) -> pd.DataFrame:
    rows = []
    for year, month in _future_periods(months):
        for _, entry in baseline.iterrows():
            rows.append({
                "year": year,
                "month": month,
                "categoria": entry["categoria"],
                "periodicidad": entry["periodicidad"],
                "tipo": entry["tipo"],
                "avg_cantidad": entry["avg_cantidad"],
                "transactions": entry["transactions"],
            })
    return pd.DataFrame(rows)


###############################################
# 8. Predicción final para meses futuros
###############################################
def predict_future_expenses(months: int = 6):
    transactions = _fetch_transactions()
    if transactions.empty:
        raise ValueError("No se encontraron transacciones para entrenar el modelo.")

    records = _prepare_monthly_records(transactions)
    if records.empty:
        raise ValueError("No hay datos suficientes para entrenar gastos.")

    model, feature_cols, metrics_real, metrics_cv, baseline, importance_df = _train_model(records)

    future_template = _build_future_template(baseline, months)

    future_features = _build_features(future_template, required_columns=feature_cols)

    preds = model.predict(future_features)
    future_template["predicted_monto"] = preds

    future_template["segment"] = future_template["periodicidad"].str.lower().apply(
        lambda x: "Variable" if x == "variable" else "Fijo"
    )

    pivot = (
        future_template.groupby(["year", "month", "segment"], as_index=False)["predicted_monto"].sum()
        .pivot_table(index=["year", "month"], columns="segment", values="predicted_monto", fill_value=0)
        .reset_index()
    )

    pivot["total"] = pivot.get("Fijo", 0) + pivot.get("Variable", 0)
    pivot["period"] = [f"{month_name[int(m)]} {int(y)}" for y, m in zip(pivot["year"], pivot["month"])]

    pivot = pivot.sort_values(["year", "month"]).reset_index(drop=True)

    return pivot[["period", "Fijo", "Variable", "total"]], metrics_real, metrics_cv, importance_df
