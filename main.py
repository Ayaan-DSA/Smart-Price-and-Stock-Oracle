from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_connection
from oracle import predict_price
from alert import check_and_alert

# FastAPI() creates the app instance
# title and description show up in the auto-generated docs at /docs
app = FastAPI(
    title="Price Oracle API",
    description="Track product prices and predict best buy dates",
    version="1.0.0"
)


# Pydantic model for adding a new product
# FastAPI uses this to validate incoming JSON body automatically
class ProductIn(BaseModel):
    title: str
    url: str
    threshold: float    # alert will fire if predicted price drops below this


# Pydantic model for setting a custom alert threshold
class ThresholdIn(BaseModel):
    threshold: float


# GET /
# Health check endpoint — just confirms the API is alive
@app.get("/")
def root():
    return {"status": "Price Oracle API is running"}


# GET /products
# Returns all products currently being tracked in the database
@app.get("/products")
def get_products():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch every product row
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return {"products": products}


# POST /products
# Adds a new product to track
# Expects JSON body: { "name": "...", "url": "...", "threshold": 45000 }
@app.post("/products")
def add_product(product: ProductIn):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO products (title, url, threshold) VALUES (%s, %s, %s)",
        (product.title, product.url, product.threshold)
    )
    conn.commit()

    # lastrowid gives us the auto-incremented id of the row just inserted
    new_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return {"message": "Product added successfully", "product_id": new_id}


# GET /history/{product_id}
# Returns all scraped price records for a product
# Used by Streamlit later to draw the price history chart
@app.get("/history/{product_id}")
def get_history(product_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT price, stock_status, scraped_at FROM price_logs WHERE product_id = %s ORDER BY scraped_at",
        (product_id,)
    )
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    if not rows:
        # 404 means "not found" — standard HTTP convention
        raise HTTPException(status_code=404, detail=f"No price history found for product {product_id}")

    return {"product_id": product_id, "history": rows}


# GET /predict/{product_id}
# Runs the oracle and returns the 30-day price prediction
# This is the core endpoint — Streamlit will call this to show the prediction card
@app.get("/predict/{product_id}")
def get_prediction(product_id: int):
    result = predict_price(product_id)

    # If oracle returned an error (not enough data etc), pass it as 400
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


# GET /alert/{product_id}
# Manually trigger an alert check for a product
# Checks if predicted price is below threshold, and fires Gmail if yes
@app.get("/alert/{product_id}")
def trigger_alert(product_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch the threshold set for this product
    cursor.execute("SELECT threshold FROM products WHERE id = %s", (product_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    threshold = row["threshold"]

    # check_and_alert handles everything:
    # runs oracle, compares to threshold, sends email if needed
    check_and_alert(product_id=product_id, threshold=threshold)

    return {"message": f"Alert check done for product {product_id} with threshold ₹{threshold}"}


# PUT /products/{product_id}/threshold
# Update the alert threshold for a product
# Expects JSON body: { "threshold": 42000 }
@app.put("/products/{product_id}/threshold")
def update_threshold(product_id: int, body: ThresholdIn):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE products SET threshold = %s WHERE id = %s",
        (body.threshold, product_id)
    )
    conn.commit()

    # rowcount = 0 means no row was updated, so product doesn't exist
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    cursor.close()
    conn.close()

    return {"message": f"Threshold updated to ₹{body.threshold} for product {product_id}"}


# DELETE /products/{product_id}
# Removes a product and all its price history from the database
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    # Delete price logs first (foreign key constraint)
    cursor.execute("DELETE FROM price_logs WHERE product_id = %s", (product_id,))

    # Then delete the product itself
    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    cursor.close()
    conn.close()

    return {"message": f"Product {product_id} and all its history deleted"}
