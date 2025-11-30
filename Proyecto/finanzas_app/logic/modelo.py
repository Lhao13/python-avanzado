"""Modelo ligero para predecir gastos con series históricas."""

from __future__ import annotations

from calendar import month_name
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

from ..db.connection import DatabaseConnection

MIN_RECORDS_FOR_TRAINING = 12


def _fetch_transactions() -> pd.DataFrame:
    # Recupera todas las transacciones con sus categorías desde la base de datos.
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


def _prepare_monthly_records(df: pd.DataFrame) -> pd.DataFrame:
    # Llena campos faltantes y agrega año/mes para agrupar por periodo.
    df = df.copy()
    df["cantidad"] = df["cantidad"].fillna(0)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["year"] = df["fecha"].dt.year
    df["month"] = df["fecha"].dt.month
    df = df[df["tipo"].str.lower() == "gasto"]
    if df.empty:
        return pd.DataFrame()
    # Agrupa por año, mes y categoría para calcular totales y promedios.
    records = (
        df.groupby(["year", "month", "categoria", "periodicidad", "tipo"], dropna=False)
        .agg(
            total_monto=("monto", "sum"),
            avg_cantidad=("cantidad", "mean"),
            transactions=("monto", "count"),
        )
        .reset_index()
    )
    # Evita valores nulos antes de entrenar.
    records["avg_cantidad"] = records["avg_cantidad"].fillna(0.0)
    records["transactions"] = records["transactions"].fillna(0.0)
    return records


def _category_baseline(records: pd.DataFrame) -> pd.DataFrame:
    # Calcula promedios por categoría para poder recrear el perfil en los meses futuros.
    baseline = (
        records.groupby(["categoria", "periodicidad", "tipo"], dropna=False)
        .agg(avg_cantidad=("avg_cantidad", "mean"), transactions=("transactions", "mean"))
        .reset_index()
    )
    baseline["transactions"] = baseline["transactions"].fillna(0.0)
    baseline["avg_cantidad"] = baseline["avg_cantidad"].fillna(0.0)
    return baseline


def _build_features(records: pd.DataFrame, required_columns: List[str] | None = None) -> pd.DataFrame:
    # Conservamos columnas numéricas que representan la fecha y el comportamiento promedio.
    base = records[["year", "month", "avg_cantidad", "transactions"]].copy()
    categorical = pd.get_dummies(records[["categoria", "periodicidad", "tipo"]].astype(str))
    features = pd.concat([base, categorical], axis=1)
    # Muestra por consola una vista previa para verificar el one-hot encoding.
    print("[modelo] head de features tras one-hot encoding:\n", features.head(5))
    print("[modelo] columnas de features:", features.columns.tolist())
    if required_columns is not None:
        for column in required_columns:
            if column not in features.columns:
                features[column] = 0.0
        features = features[required_columns]
    return features


def _train_model(records: pd.DataFrame) -> Tuple[RandomForestRegressor, List[str], float, pd.DataFrame]:
    if len(records) < MIN_RECORDS_FOR_TRAINING:
        raise ValueError(
            f"Se necesitan al menos {MIN_RECORDS_FOR_TRAINING} registros de gastos para entrenar el modelo."
        )
    features = _build_features(records)
    target = records["total_monto"].astype(float)
    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)
    # Entrena el RandomForest con una partición simple y mide R² en la porción de prueba.
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    baseline = _category_baseline(records)
    return model, features.columns.tolist(), score, baseline


def _future_periods(months: int) -> List[Tuple[int, int]]:
    today = datetime.now()
    periods: List[Tuple[int, int]] = []
    # Genera una lista de períodos futuros en función del número de meses especificado.
    for offset in range(1, months + 1):
        total_month = today.month - 1 + offset
        year = today.year + total_month // 12
        month = (total_month % 12) + 1
        periods.append((year, month))
    return periods


def _build_future_template(baseline: pd.DataFrame, months: int) -> pd.DataFrame:
    # Replica el perfil histórico por cada combinación de categoría/periocidad para los meses siguientes.
    rows: List[Dict[str, float]] = []
    for year, month in _future_periods(months):
        for _, entry in baseline.iterrows():
            rows.append(
                {
                    "year": year,
                    "month": month,
                    "categoria": entry["categoria"],
                    "periodicidad": entry["periodicidad"],
                    "tipo": entry["tipo"],
                    "avg_cantidad": entry["avg_cantidad"],
                    "transactions": entry["transactions"],
                }
            )
    if not rows:
        return pd.DataFrame()
    template = pd.DataFrame(rows)
    template["avg_cantidad"] = template["avg_cantidad"].fillna(0.0)
    template["transactions"] = template["transactions"].fillna(0.0)
    return template


def predict_future_expenses(months: int = 3) -> Tuple[pd.DataFrame, float]:
    transactions = _fetch_transactions()
    if transactions.empty:
        raise ValueError("No se encontraron transacciones para entrenar el modelo.")
    records = _prepare_monthly_records(transactions)
    if records.empty:
        raise ValueError("No se encontraron gastos bastantes para entrenar el modelo.")
    model, feature_cols, score, baseline = _train_model(records)
    
    # Genera la grilla futura con base en el perfil promedio de cada categoría.
    future_template = _build_future_template(baseline, months)
    if future_template.empty:
        raise ValueError("No hay categorías con datos suficientes para generar predicciones.")
    future_features = _build_features(future_template, required_columns=feature_cols)
    predictions = model.predict(future_features)
    future_template["predicted_monto"] = predictions
    detail = future_template.copy()
    detail["segment"] = detail["periodicidad"].str.lower().apply(lambda value: "Variable" if value == "variable" else "Fijo")
    pivot = (
        detail.groupby(["year", "month", "segment"], as_index=False)["predicted_monto"].sum()
        .pivot_table(index=["year", "month"], columns="segment", values="predicted_monto", fill_value=0)
        .reset_index()
    )
    pivot["Fijo"] = pivot.get("Fijo", 0.0)
    pivot["Variable"] = pivot.get("Variable", 0.0)
    pivot["total"] = pivot["Fijo"] + pivot["Variable"]
    pivot["period"] = [f"{month_name[int(row[1])]} {int(row[0])}" for row in zip(pivot["year"], pivot["month"])]
    pivot = pivot.sort_values(["year", "month"]).reset_index(drop=True)
    return pivot[["period", "Fijo", "Variable", "total"]], score
