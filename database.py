import mysql.connector

#DB credentials
DB_USER     = "YOUR USERNAME"
DB_PASSWORD = "YOUR PASSWORD"                   
DB_HOST     = "localhost"
DB_PORT     = "3306"
DB_NAME     = "price_oracle"   # ← must already exist in MySQL Workbench


def get_connection():
    # Establish a connection to the MySQL database
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def save_scrape_result(data):
    conn = get_connection()
    cursor= conn.cursor()
#check if the product already exists in database
    cursor.execute(
        "SELECT id FROM products WHERE url = %s", (data["url"],)   
    )
    result = cursor.fetchone()  # returns one row or None
    #Now create or get product
    if result:
        product_id = result[0]
    else:
        cursor.execute(
            "INSERT INTO products (title , url , platform) VALUES (%s, %s, %s)",
            (data["product_title"], data["url"], data["platform"])

        )
        product_id = cursor.lastrowid
        #insert a new price log
    cursor.execute(
        "INSERT INTO price_logs (product_id, price, stock_status) VALUES (%s, %s, %s)",
        (product_id, data["current_price"], data["stock_status"])
    )
    #commit saves the changes to the database
    conn.commit()
    #close the connection and cursor
    cursor.close()
    conn.close()
    print(f"Saved: {data['product_title']} at {data['current_price']} ({data['current_price']})")

