from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def dashboard():
    # Load data
    df = pd.read_csv('data/sales.csv')

    # ---------------------------
    # ✅ FILTERS
    # ---------------------------
    month = request.args.get('month')
    product = request.args.get('product')

    if month:
        df = df[df['date'].str.contains(month)]

    if product:
        df = df[df['product'] == product]

    # ---------------------------
    # Convert date
    # ---------------------------
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month

    # ---------------------------
    # 📈 Revenue Trend
    # ---------------------------
    revenue = df.groupby('month')['price'].sum()

    plt.figure()
    revenue.plot(kind='line', marker='o')
    plt.title("Monthly Revenue")
    plt.xlabel("Month")
    plt.ylabel("Revenue")
    plt.grid()

    os.makedirs('static/images', exist_ok=True)
    plt.savefig('static/images/revenue.png')
    plt.close()

    # ---------------------------
    # 🥧 Gender Distribution
    # ---------------------------
    gender = df['gender'].value_counts()

    plt.figure()
    gender.plot(kind='pie', autopct='%1.1f%%')
    plt.title("Gender Distribution")

    plt.savefig('static/images/gender.png')
    plt.close()

    # ---------------------------
    # 📊 Age Distribution
    # ---------------------------
    plt.figure()
    df['age'].plot(kind='hist', bins=5)
    plt.title("Age Distribution")

    plt.savefig('static/images/age.png')
    plt.close()

    # ---------------------------
    # 📊 Top Products
    # ---------------------------
    top_products = df.groupby('product')['price'].sum()

    plt.figure()
    top_products.plot(kind='bar')
    plt.title("Top Products")

    plt.savefig('static/images/products.png')
    plt.close()

    # ---------------------------
    # 📊 KPI VALUES
    # ---------------------------
    total_revenue = df['price'].sum()
    total_customers = df['customer_id'].nunique()
    avg_order = round(df['price'].mean(), 2)

    return render_template(
        "dashboard.html",
        total_revenue=total_revenue,
        total_customers=total_customers,
        avg_order=avg_order
    )


if __name__ == '__main__':
    app.run(debug=True)