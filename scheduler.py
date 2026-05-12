from apscheduler.schedulers.blocking import BlockingScheduler
from database import get_connection
from scrap import scrape
from alert import check_current_price_alert, check_and_alert
from datetime import datetime

scheduler = BlockingScheduler()


def scrape_all_products():
    """
    Fetches every product from the database and for each one:
      1. Scrapes the latest price and saves it to price_logs
      2. Checks if current live price is below threshold and sends alert if yes
      3. Runs oracle prediction and sends alert if predicted price is below threshold
    Runs automatically every 24 hours.
    """
    print(f"\n[{datetime.now()}] Starting scheduled scrape...")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, url, threshold FROM products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()

    if not products:
        print("No products found in database. Add some via the dashboard first.")
        return

    for product in products:
        product_id = product["id"]
        url        = product["url"]
        threshold  = product["threshold"]

        print(f"\nProcessing product #{product_id}...")

        try:
            # Step 1: scrape fresh price and save to DB
            scrape_product(product_id, url)
            print(f"Product #{product_id} scraped successfully.")

            # Step 2: check if live current price is already below threshold
            # sends email immediately if yes — "price is low RIGHT NOW"
            check_current_price_alert(product_id=product_id, threshold=threshold)

            # Step 3: run oracle and check if predicted future price is below threshold
            # sends email if yes — "price will be low on DATE"
            check_and_alert(product_id=product_id, threshold=threshold)

        except Exception as e:
            print(f"Error processing product #{product_id}: {e}")

    print(f"\n[{datetime.now()}] All products processed.\n")


# Run once immediately on startup so you dont wait 24 hours for the first scrape
scrape_all_products()

# Then schedule to repeat every 24 hours automatically
scheduler.add_job(scrape_all_products, "interval", hours=24)

print("Scheduler is running. Scraping every 24 hours. Press Ctrl+C to stop.")
scheduler.start()