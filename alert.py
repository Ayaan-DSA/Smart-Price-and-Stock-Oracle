import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from oracle import predict_price
from database import get_connection

# YOUR GMAIL CREDENTIALS

SENDER_EMAIL    = "ayaankhanak3589@gmail.com"
SENDER_PASSWORD = "ybip cfvm gfrr isov"
RECEIVER_EMAIL  = "ayaankhanak3589@gmail.com"


def send_email(subject: str, body: str):
    """
    Core email sender used by both alert functions below.
    Builds the email and sends it via Gmail SMTP.
    Separated into its own function so we dont repeat
    the SMTP logic in every alert function.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECEIVER_EMAIL
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print(f"Email sent to {RECEIVER_EMAIL}")
    except smtplib.SMTPAuthenticationError:
        print("Authentication failed. Check your App Password.")
    except smtplib.SMTPException as e:
        print(f"Email error: {e}")


def get_latest_price(product_id: int) -> float:
    """
    Fetches the most recently scraped price for a product from the database.
    Used to check if the current live price is already below threshold.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT price FROM price_logs WHERE product_id = %s ORDER BY scraped_at DESC LIMIT 1",
        (product_id,)
    )
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return float(row["price"]) if row else None


def check_current_price_alert(product_id: int, threshold: float):
    """
    Checks if the CURRENT live price (latest scrape) is below the threshold.
    If yes, sends a Gmail alert saying the price is low RIGHT NOW.
    This is separate from oracle which predicts future prices.
    """
    current_price = get_latest_price(product_id)

    if current_price is None:
        print(f"No price found for product #{product_id}. Skipping current price check.")
        return

    print(f"Current price for product #{product_id}: Rs {current_price:,}")

    if current_price < threshold:
        print(f"Current price Rs {current_price:,} is below threshold Rs {threshold:,}! Sending alert...")

        subject = f"Price Alert: Product #{product_id} is cheap RIGHT NOW!"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #cc0000;">Live Price Drop Alert!</h2>
            <p>The current price just dropped below your threshold. Good time to buy now!</p>

            <table style="border-collapse: collapse; width: 100%; max-width: 400px;">
                <tr style="background: #f4f4f4;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><b>Product ID</b></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">#{product_id}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><b>Current Price</b></td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: green;"><b>Rs {current_price:,.2f}</b></td>
                </tr>
                <tr style="background: #f4f4f4;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><b>Your Threshold</b></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">Rs {threshold:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><b>When</b></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">RIGHT NOW</td>
                </tr>
            </table>

            <br>
            <p style="color: #888; font-size: 12px;">
                This is an automated alert from your Price Oracle scraper.
            </p>
        </body>
        </html>
        """

        send_email(subject, body)

    else:
        print(f"Current price Rs {current_price:,} is above threshold Rs {threshold:,}. No alert.")


def check_and_alert(product_id: int, threshold: float):
    """
    Runs the oracle prediction and checks if the PREDICTED future price
    is below the threshold. If yes, sends a Gmail alert with the best buy date.
    This is for future price prediction, not the current live price.
    """
    print(f"Running oracle prediction for product #{product_id}...")
    result = predict_price(product_id)

    if "error" in result:
        print(f"Oracle error: {result['error']}")
        return

    best_buy_price = result["best_buy_price"]
    best_buy_date  = result["best_buy_date"]
    daily_change   = result["daily_change"]
    trend          = result["trend"]

    print(f"Predicted best price: Rs {best_buy_price:,} on {best_buy_date} (trend: {trend})")

    if best_buy_price < threshold:
        print(f"Predicted price Rs {best_buy_price:,} is below threshold Rs {threshold:,}! Sending alert...")

        subject = f"Price Prediction Alert: Product #{product_id} will be cheap on {best_buy_date}!"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #e47911;">Future Price Drop Prediction!</h2>
            <p>Our oracle predicts a great time to buy this product soon.</p>

            <table style="border-collapse: collapse; width: 100%; max-width: 400px;">
                <tr style="background: #f4f4f4;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><b>Product ID</b></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">#{product_id}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><b>Best Buy Date</b></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">📅 {best_buy_date}</td>
                </tr>
                <tr style="background: #f4f4f4;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><b>Predicted Price</b></td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: green;"><b>Rs {best_buy_price:,.2f}</b></td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><b>Your Threshold</b></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">Rs {threshold:,.2f}</td>
                </tr>
                <tr style="background: #f4f4f4;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><b>Daily Change</b></td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: {'red' if daily_change > 0 else 'green'};">
                        {"up" if daily_change > 0 else "down"} Rs {abs(daily_change)}/day
                    </td>
                </tr>
            </table>

            <br>
            <p style="color: #888; font-size: 12px;">
                This is an automated alert from your Price Oracle scraper.
            </p>
        </body>
        </html>
        """

        send_email(subject, body)

    else:
        print(f"Predicted price Rs {best_buy_price:,} is above threshold Rs {threshold:,}. No alert.")


if __name__ == "__main__":
    check_current_price_alert(product_id=2, threshold=45000)
    check_and_alert(product_id=2, threshold=45000)