import re
from datetime import datetime


users = {}


email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
password_pattern = r'^(?=.*[A-Z])(?=.*\d).{8,}$'


def calculate_age(dob):
    today = datetime.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age


def register_user():
    print("\n--- User Registration ---")

    name = input("Enter Name: ")

    while True:
        email = input("Enter Email: ")
        if re.match(email_pattern, email):
            if email not in users:
                break
            else:
                print("Email already registered!")
        else:
            print("Invalid email format!")

  
    while True:
        password = input("Enter Password: ")
        if re.match(password_pattern, password):
            break
        else:
            print(" Password must have 8 characters, 1 uppercase, and 1 digit!")

   
    while True:
        dob_input = input("Enter Date of Birth (YYYY-MM-DD): ")
        try:
            dob = datetime.strptime(dob_input, "%Y-%m-%d")
            break
        except ValueError:
            print(" Invalid date format!")

    
    users[email] = {
        "name": name,
        "password": password,
        "dob": dob
    }

    print(" Registration Successful!")


def display_users():
    print("\n--- Registered Users ---")

    if not users:
        print("No users registered yet.")
        return

    for email, details in users.items():
        age = calculate_age(details["dob"])
        print("\n-------------------------")
        print(f"Name   : {details['name']}")
        print(f"Email  : {email}")
        print(f"DOB    : {details['dob'].strftime('%Y-%m-%d')}")
        print(f"Age    : {age}")


while True:
    print("\n===== MENU =====")
    print("1. Register User")
    print("2. Display Users")
    print("3. Exit")

    choice = input("Enter your choice: ")

    if choice == "1":
        register_user()
    elif choice == "2":
        display_users()
    elif choice == "3":
        print("Exiting program...")
        break
    else:
        print(" Invalid choice!")