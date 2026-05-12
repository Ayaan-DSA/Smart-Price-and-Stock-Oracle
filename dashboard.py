import streamlit as st
import requests
import pandas as pd

# Base URL of your FastAPI server
# Make sure uvicorn is running before opening this dashboard
API = "http://127.0.0.1:8000"

st.title("Price Oracle Dashboard")


# SECTION 1: ALL TRACKED PRODUCTS
st.header("Tracked Products")

response = requests.get(f"{API}/products")

if response.status_code == 200:
    products = response.json()["products"]

    if not products:
        st.info("No products found. Add one below.")
    else:
        # Show products in a clean table
        df = pd.DataFrame(products)
        st.dataframe(df, use_container_width=True)
else:
    st.error("Could not fetch products. Is FastAPI running?")
    st.stop()


st.divider()


# SECTION 2: ADD A NEW PRODUCT
st.header("Add New Product")

title      = st.text_input("Product Name")
url       = st.text_input("Product URL")
threshold = st.number_input("Alert Threshold (₹)", min_value=0.0, value=45000.0, step=500.0)

if st.button("Add Product"):
    if not title or not url:
        st.warning("Please fill in both name and URL.")
    else:
        res = requests.post(f"{API}/products", json={
            "title":      title,
            "url":       url,
            "threshold": threshold
        })
        if res.status_code == 200:
            st.success(f"Product added! ID: {res.json()['product_id']}")
            st.rerun()
        else:
            st.error("Failed to add product.")


st.divider()


# SECTION 3: PRICE HISTORY CHART
st.header("Price History")

product_id_hist = st.number_input("Enter Product ID for History", min_value=1, step=1, key="hist")

if st.button("Load History"):
    res = requests.get(f"{API}/history/{product_id_hist}")

    if res.status_code == 200:
        history = res.json()["history"]
        df_hist = pd.DataFrame(history)
        df_hist["scraped_at"] = pd.to_datetime(df_hist["scraped_at"])
        df_hist = df_hist.sort_values("scraped_at")

        # Simple line chart — scraped_at on x axis, price on y axis
        st.line_chart(df_hist.set_index("scraped_at")["price"])
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.error(res.json().get("detail", "No history found."))


st.divider()


# SECTION 4: ORACLE PREDICTION
st.header("Price Prediction (Oracle)")

product_id_pred = st.number_input("Enter Product ID to Predict", min_value=1, step=1, key="pred")

if st.button("Run Prediction"):
    res = requests.get(f"{API}/predict/{product_id_pred}")

    if res.status_code == 200:
        data = res.json()

        # Show prediction results as simple metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Best Buy Date",  data["best_buy_date"])
        col2.metric("Predicted Price", f"₹{data['best_buy_price']:,}")
        col3.metric("Daily Change",    f"₹{data['daily_change']}/day")

        st.write(f"Trend: **{data['trend'].capitalize()}**")
        st.write(f"MAE (avg prediction error): ₹{data['mae']}")
        st.write(f"Records used: {data['records_used']}")
    else:
        st.error(res.json().get("detail", "Prediction failed."))


st.divider()


# SECTION 5: MANUAL ALERT CHECK
st.header("Trigger Alert Check")

product_id_alert = st.number_input("Enter Product ID for Alert", min_value=1, step=1, key="alert")

if st.button("Check & Send Alert"):
    res = requests.get(f"{API}/alert/{product_id_alert}")

    if res.status_code == 200:
        st.success(res.json()["message"])
    else:
        st.error(res.json().get("detail", "Alert check failed."))


st.divider()


# SECTION 6: UPDATE ALERT THRESHOLD
st.header("Update Alert Threshold")

product_id_thresh = st.number_input("Enter Product ID", min_value=1, step=1, key="thresh")
new_threshold     = st.number_input("New Threshold (₹)", min_value=0.0, value=45000.0, step=500.0, key="new_thresh")

if st.button("Update Threshold"):
    res = requests.put(f"{API}/products/{product_id_thresh}/threshold", json={
        "threshold": new_threshold
    })

    if res.status_code == 200:
        st.success(res.json()["message"])
    else:
        st.error(res.json().get("detail", "Update failed."))


st.divider()


# SECTION 7: DELETE A PRODUCT
st.header("Delete Product")

product_id_del = st.number_input("Enter Product ID to Delete", min_value=1, step=1, key="del")

if st.button("Delete Product", type="primary"):
    res = requests.delete(f"{API}/products/{product_id_del}")

    if res.status_code == 200:
        st.success(res.json()["message"])
        st.rerun()
    else:
        st.error(res.json().get("detail", "Delete failed."))