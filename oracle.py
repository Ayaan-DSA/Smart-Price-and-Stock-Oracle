import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from datetime import datetime, timezone, timedelta
from database import get_connection

def predict_price(product_id: int) -> dict:

    # ── STEP 1: Load price history from MySQL ──────────────────
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT price, scraped_at FROM price_logs WHERE product_id = %s ORDER BY scraped_at",
        (product_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # ── STEP 2: Need minimum 5 records to predict ──────────────
    if len(rows) < 5:
        return {
            "error": "Not enough data yet. Scrape the product more times first.",
            "records_found": len(rows)
        }

    # ── STEP 3: Load into Pandas DataFrame ────────────────────
    df = pd.DataFrame(rows)
    df["scraped_at"] = pd.to_datetime(df["scraped_at"])
    df = df.sort_values("scraped_at").reset_index(drop=True)
    df["price"] = df["price"].astype(float)

    # ── STEP 4: EMA smoothing ──────────────────────────────────
    # Removes flash sale spikes (e.g. 2hr Lightning Deal)
    # so they don't drag the regression line down falsely
    df["price_smooth"] = df["price"].ewm(span=7).mean()

    # ── STEP 5: Normalize timestamps to day index ──────────────
    # KEY FIX: MySQL DATETIME columns come in as timezone-naive.
    # Using .astype(np.int64) on naive datetimes gives wrong tiny numbers.
    # Instead we use (timestamp - first_timestamp).total_seconds() / 86400
    # which gives correct day offsets like 0, 1, 2, 3 ... regardless of timezone.
    first_ts = df["scraped_at"].iloc[0]
    df["day_index"] = df["scraped_at"].apply(
        lambda ts: (ts - first_ts).total_seconds() / 86400
    )

    X = df["day_index"].values.reshape(-1, 1)   # input:  day 0, 1, 2 ...
    y = df["price_smooth"].values                # output: smoothed price

    # ── STEP 6: Train Linear Regression ───────────────────────
    # price = a x day + b
    # 'a' = Rs change per day (slope)
    # 'b' = base price (intercept)
    model = LinearRegression()
    model.fit(X, y)

    # ── STEP 7: Compute MAE on training data ───────────────────
    # e.g. MAE = 120 means predictions are off by Rs 120 on average
    y_pred_train = model.predict(X)
    mae = mean_absolute_error(y, y_pred_train)

    # ── STEP 8: Predict next 30 days ──────────────────────────
    last_day = df["day_index"].max()
    future_days = np.array([
        last_day + i for i in range(1, 31)
    ]).reshape(-1, 1)

    predicted_prices = model.predict(future_days)

    # ── STEP 9: Find Best Buy Date ────────────────────────────
    # The day with the lowest predicted price
    min_index = np.argmin(predicted_prices)

    # Convert day offset back to a real date
    best_date = first_ts + timedelta(days=float(future_days[min_index][0]))
    best_buy_date = best_date.strftime("%Y-%m-%d")
    best_buy_price = round(float(predicted_prices[min_index]), 2)

    # model.coef_[0] = Rs per day (X was in days, so no extra conversion needed)
    daily_change = round(float(model.coef_[0]), 2)
    trend = "falling" if daily_change < 0 else "rising"

    # ── STEP 10: Return result ─────────────────────────────────
    return {
        "product_id":     product_id,
        "best_buy_date":  best_buy_date,
        "best_buy_price": best_buy_price,
        "mae":            round(mae, 2),
        "daily_change":   daily_change,   # Rs per day (negative = price falling)
        "trend":          trend,
        "records_used":   len(df)
    }


# ── TEST IT ───────────────────────────────────────────────────
if __name__ == "__main__":
    import json
    result = predict_price(product_id=2)  # change to your product's id
    print(json.dumps(result, indent=2))