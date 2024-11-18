import os
from bs4 import BeautifulSoup
import requests
import time
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

url = "https://www.macrotrends.net/stocks/charts/TSLA/tesla/revenue"

# Initial request with a delay
time.sleep(10)
response = requests.get(url)

# If access is forbidden, retry with headers
if response.status_code == 403 or "403 Forbidden" in response.text:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
    }
    time.sleep(10)
    response = requests.get(url, headers=headers)

# Extract HTML data
html_data = response.text
soup = BeautifulSoup(html_data, "html.parser")

# Find all tables
tables = soup.find_all("table")
for index, table in enumerate(tables):
    if "Tesla Quarterly Revenue" in str(table):
        table_index = index
        break

# Create a DataFrame
tesla_revenue = pd.DataFrame(columns=["Date", "Revenue"])
for row in tables[table_index].tbody.find_all("tr"):
    col = row.find_all("td")
    if col:
        Date = col[0].text.strip()
        Revenue = col[1].text.strip().replace("$", "").replace(",", "")
        tesla_revenue = pd.concat([tesla_revenue, pd.DataFrame({
            "Date": Date,
            "Revenue": Revenue
        }, index=[0])], ignore_index=True)

# Remove empty rows and ensure proper data types
tesla_revenue = tesla_revenue[tesla_revenue["Revenue"] != ""]
tesla_revenue["Date"] = pd.to_datetime(tesla_revenue["Date"])  # Convert to datetime for processing
tesla_revenue["Date"] = tesla_revenue["Date"].astype(str)  # Convert to string for SQLite
tesla_revenue["Revenue"] = tesla_revenue["Revenue"].astype(float)  # Convert to float for SQLite

# Save to SQLite database
connection = sqlite3.connect("Tesla.db")
cursor = connection.cursor()

# Drop and recreate the table
cursor.execute("DROP TABLE IF EXISTS revenue")
cursor.execute("CREATE TABLE revenue (Date TEXT, Revenue REAL)")

# Insert data into the table
tesla_tuples = list(tesla_revenue.to_records(index=False))
cursor.executemany("INSERT INTO revenue VALUES (?, ?)", tesla_tuples)
connection.commit()

# Verify data from the database
for row in cursor.execute("SELECT * FROM revenue"):
    print(row)

# Plotting the data
fig, axis = plt.subplots(figsize=(10, 5))

# Monthly Revenue
tesla_revenue["Month"] = pd.to_datetime(tesla_revenue["Date"]).dt.month
tesla_revenue_monthly = tesla_revenue.groupby("Month")["Revenue"].sum().reset_index()

# Optional: Replace month numbers with names
tesla_revenue_monthly["Month"] = tesla_revenue_monthly["Month"].apply(
    lambda x: pd.Timestamp(month=x, day=1, year=2023).strftime('%B')
)

sns.barplot(data=tesla_revenue_monthly, x="Month", y="Revenue", ax=axis)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Yearly Revenue
fig, axis = plt.subplots(figsize=(10, 5))

tesla_revenue["Year"] = pd.to_datetime(tesla_revenue["Date"]).dt.year
tesla_revenue_yearly = tesla_revenue.groupby("Year")["Revenue"].sum().reset_index()

sns.barplot(data=tesla_revenue_yearly[tesla_revenue_yearly["Year"] < 2023], x="Year", y="Revenue", ax=axis)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()