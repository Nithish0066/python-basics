import pymysql

print("\n===== ONLINE FOOD DELIVERY SYSTEM =====\n")

try:
    connection = pymysql.connect(
        host="localhost",
        user="root",
        password="nithishhn",  # change if needed
        port=3306
    )
    cursor = connection.cursor()
    print(" Connected to MySQL Server\n")

except Exception as e:
    print(" Connection Failed:", e)
    exit()

cursor.execute("CREATE DATABASE IF NOT EXISTS food_delivery")
cursor.execute("USE food_delivery")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Customer (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(15),
    address TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Restaurant (
    restaurant_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    location VARCHAR(150),
    phone VARCHAR(15)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Food_Item (
    food_id INT PRIMARY KEY AUTO_INCREMENT,
    restaurant_id INT,
    name VARCHAR(100),
    price DECIMAL(10,2),
    FOREIGN KEY (restaurant_id) REFERENCES Restaurant(restaurant_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Delivery_Person (
    delivery_person_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    phone VARCHAR(15)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    delivery_person_id INT,
    total_amount DECIMAL(10,2),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
    FOREIGN KEY (delivery_person_id) REFERENCES Delivery_Person(delivery_person_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Order_Item (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    food_id INT,
    quantity INT,
    subtotal DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    FOREIGN KEY (food_id) REFERENCES Food_Item(food_id)
)
""")

connection.commit()
print(" Database & Tables Ready!\n")


def add_customer():
    name = input("Name: ")
    email = input("Email: ")
    phone = input("Phone: ")
    address = input("Address: ")

    cursor.execute(
        "INSERT INTO Customer (name,email,phone,address) VALUES (%s,%s,%s,%s)",
        (name, email, phone, address)
    )
    connection.commit()
    print(" Customer Added\n")


def update_customer():
    cid = int(input("Customer ID to Update: "))
    new_name = input("New Name: ")

    cursor.execute(
        "UPDATE Customer SET name=%s WHERE customer_id=%s",
        (new_name, cid)
    )
    connection.commit()
    print(" Customer Updated\n")


def delete_customer():
    cid = int(input("Customer ID to Delete: "))

    cursor.execute("DELETE FROM Customer WHERE customer_id=%s", (cid,))
    connection.commit()
    print(" Customer Deleted\n")


def view_customers():
    cursor.execute("SELECT * FROM Customer")
    rows = cursor.fetchall()

    print("\n---- Customers ----")
    for row in rows:
        print(row)
    print("-------------------\n")


def add_restaurant():
    name = input("Restaurant Name: ")
    location = input("Location: ")
    phone = input("Phone: ")

    cursor.execute(
        "INSERT INTO Restaurant (name,location,phone) VALUES (%s,%s,%s)",
        (name, location, phone)
    )
    connection.commit()
    print("Restaurant Added\n")


def add_food_item():
    rid = int(input("Restaurant ID: "))
    name = input("Food Name: ")
    price = float(input("Price: "))

    cursor.execute(
        "INSERT INTO Food_Item (restaurant_id,name,price) VALUES (%s,%s,%s)",
        (rid, name, price)
    )
    connection.commit()
    print("Food Item Added\n")


def add_delivery_person():
    name = input("Delivery Person Name: ")
    phone = input("Phone: ")

    cursor.execute(
        "INSERT INTO Delivery_Person (name,phone) VALUES (%s,%s)",
        (name, phone)
    )
    connection.commit()
    print(" Delivery Person Added\n")


def place_order():
    customer_id = int(input("Customer ID: "))
    delivery_id = int(input("Delivery Person ID: "))

    cursor.execute(
        "INSERT INTO Orders (customer_id,delivery_person_id,total_amount) VALUES (%s,%s,0)",
        (customer_id, delivery_id)
    )
    connection.commit()

    order_id = cursor.lastrowid
    total_amount = 0

    while True:
        food_id = int(input("Food ID: "))
        quantity = int(input("Quantity: "))

        cursor.execute("SELECT price FROM Food_Item WHERE food_id=%s", (food_id,))
        result = cursor.fetchone()

        if not result:
            print(" Invalid Food ID\n")
            continue

        price = float(result[0])
        subtotal = price * quantity
        total_amount += subtotal

        cursor.execute(
            "INSERT INTO Order_Item (order_id,food_id,quantity,subtotal) VALUES (%s,%s,%s,%s)",
            (order_id, food_id, quantity, subtotal)
        )
        connection.commit()

        more = input("Add more items? (y/n): ")
        if more.lower() != 'y':
            break

    cursor.execute(
        "UPDATE Orders SET total_amount=%s WHERE order_id=%s",
        (total_amount, order_id)
    )
    connection.commit()

    print(f" Order Placed! Total = {total_amount}\n")


def view_orders():
    query = """
    SELECT o.order_id, c.name, d.name, o.total_amount
    FROM Orders o
    JOIN Customer c ON o.customer_id = c.customer_id
    JOIN Delivery_Person d ON o.delivery_person_id = d.delivery_person_id
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    print("\n---- Orders ----")
    for row in rows:
        print(f"Order ID: {row[0]} | Customer: {row[1]} | Delivery: {row[2]} | Total: {row[3]}")
    print("----------------\n")

while True:
    print("1. Add Customer")
    print("2. View Customers")
    print("3. Update Customer")
    print("4. Delete Customer")
    print("5. Add Restaurant")
    print("6. Add Food Item")
    print("7. Add Delivery Person")
    print("8. Place Order")
    print("9. View Orders")
    print("10. Exit")

    choice = input("Enter Choice: ")

    if choice == "1":
        add_customer()
    elif choice == "2":
        view_customers()
    elif choice == "3":
        update_customer()
    elif choice == "4":
        delete_customer()
    elif choice == "5":
        add_restaurant()
    elif choice == "6":
        add_food_item()
    elif choice == "7":
        add_delivery_person()
    elif choice == "8":
        place_order()
    elif choice == "9":
        view_orders()
    elif choice == "10":
        print("Exiting Program...")
        break
    else:
        print(" Invalid Choice\n")