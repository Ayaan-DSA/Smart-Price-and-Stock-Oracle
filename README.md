# Smart Price Drop & Stock Oracle

A full-stack Python application that automatically tracks product prices on
Amazon.in and Flipkart.com, stores historical data, predicts future price
trends using Machine Learning, and sends real-time Gmail alerts when prices
drop below your target.

---

## What it does

- Scrapes product title, price, and stock status from Amazon & Flipkart
- Stores complete price history in MySQL database
- Predicts future prices using Linear Regression + EMA smoothing
- Suggests the Next Best Buy Date with MAE accuracy metric
- Sends formatted Gmail alerts when price drops below threshold
- Displays everything on an interactive Streamlit dashboard

---

## Project Structure
smart-price-oracle/
│
├── scrap.py          # Playwright scraper — Amazon & Flipkart
├── database.py       # MySQL connection and save functions
├── oracle.py         # ML price prediction (Linear Regression + EMA)
├── alert.py          # Gmail alert system
├── main.py           # FastAPI REST backend
├── dashboard.py      # Streamlit web dashboard
├── scheduler.py      # APScheduler for auto scraping
└── requirements.txt  # All dependencies

---

## Tech Stack

| Layer | Technology |
|---|---|
| Scraping | Python, Playwright (async) |
| Database | MySQL, mysql-connector-python |
| Machine Learning | Scikit-Learn, Pandas, NumPy |
| Backend | FastAPI, Pydantic, Uvicorn |
| Frontend | Streamlit, Plotly |
| Alerts | Gmail SMTP (smtplib) |

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/smart-price-oracle.git
cd smart-price-oracle
```

### 2. Create and activate virtual environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install playwright mysql-connector-python scikit-learn pandas numpy fastapi uvicorn streamlit requests
playwright install chromium
```

### 4. Set up MySQL database
Open MySQL Workbench and run:
```sql
CREATE DATABASE price_oracle;
USE price_oracle;

CREATE TABLE products (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    title       TEXT,
    url         VARCHAR(767) UNIQUE,
    platform    VARCHAR(20),
    threshold   DECIMAL(10,2) DEFAULT 50000.00,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE price_logs (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    product_id   INT,
    price        DECIMAL(10,2),
    stock_status VARCHAR(20),
    scraped_at   TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

### 5. Configure credentials
In `database.py` update:
```python
DB_USER     = "your_mysql_username"
DB_PASSWORD = "your_mysql_password"
```

In `alert.py` update:
```python
SENDER_EMAIL    = "your_gmail@gmail.com"
SENDER_PASSWORD = "your_16_char_app_password"
RECEIVER_EMAIL  = "receiver@gmail.com"
```

> For Gmail App Password: Google Account → Security → 2-Step Verification → App Passwords

---

## Running the Project

Open **three terminals** with venv activated:

**Terminal 1 — FastAPI backend:**
```bash
uvicorn main:app --reload
```

**Terminal 2 — Streamlit dashboard:**
```bash
streamlit run dashboard.py
```

**Terminal 3 — Scrape a product:**
```bash
python scrap.py
```

Then open `http://localhost:8501` in your browser.

---

## How it works
User URL → Playwright Scraper → MySQL Database → ML Oracle → Dashboard
→ Gmail Alert

1. Paste an Amazon product URL into the dashboard
2. Scraper launches headless Chromium and extracts price + stock
3. Data is saved to MySQL price_logs table with timestamp
4. Oracle loads history, applies EMA smoothing, trains Linear Regression
5. Predicts prices for next 30 days → finds Next Best Buy Date
6. If predicted price < threshold → Gmail alert is sent automatically

---

## ML Oracle Details

- **EMA (Exponential Moving Average):** Smooths out flash sale outliers
  before feeding data to the regression model
- **Linear Regression:** Finds the best-fit price trend line over time
- **MAE (Mean Absolute Error):** Measures prediction accuracy in ₹
- **Minimum 5 price records** required per product for prediction

---

## Academic Details

- **Course:** Python Programming (BCA-402)
- **Institution:** ITM University, Gwalior (M.P)
- **Department:** Computer Science & Application, SOET
- **Student:** Ayan Khan (BCAN1CA24043) — BCA-IV
- **Supervisor:** Mr. Shubham Dhakarey, Assistant Professor

---

## Future Enhancements

- Flipkart scraper support
- ARIMA / LSTM for advanced price forecasting
- Multi-user authentication
- Cloud deployment (AWS / GCP)
- Mobile app with push notifications
- Cross-platform price comparison
